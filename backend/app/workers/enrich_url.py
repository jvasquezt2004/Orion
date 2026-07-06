import asyncio
import ipaddress
import logging
import re
import socket
import tempfile
from uuid import uuid4

import cv2
import httpx

from app.core.config import config
from app.core.minio_client import minio_client
from app.db.reference import MediaKind, Reference, ReferenceType
from app.services.image_services import ImageServices
from app.workers.config import broker

logger = logging.getLogger(__name__)

PROVIDERS = {
    "youtube.com": "youtube",
    "youtu.be": "youtube",
    "vimeo.com": "vimeo",
    "tiktok.com": "tiktok",
    "instagram.com": "instagram",
    "behance.net": "behance",
    "dribbble.com": "dribbble",
}

HEADERS = {"User-Agent": "OrionBot/1.0"}


def _detect_provider(url: str) -> str | None:
    from urllib.parse import urlparse

    host = urlparse(url).hostname or ""
    host = host.removeprefix("www.")
    for domain, provider in PROVIDERS.items():
        if domain in host:
            return provider
    return None


def _youtube_id(url: str) -> str | None:
    from urllib.parse import parse_qs, urlparse

    parsed = urlparse(url)

    if "youtu.be" in parsed.hostname:
        return parsed.path.removeprefix("/").split("?")[0] or None

    if "youtube.com" in parsed.hostname:
        parts = [p for p in parsed.path.split("/") if p]
        if parts[0] in ("embed", "shorts"):
            return parts[1] if len(parts) > 1 else None
        return parse_qs(parsed.query).get("v", [None])[0]

    return None


def _og(html: str, prop: str) -> str | None:
    patterns = [
        rf'<meta[^>]+property=["\']({prop})["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']({prop})["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            groups = match.groups()
            return groups[1] if groups[0].startswith(prop) else groups[0]
    return None


def _title_tag(html: str) -> str | None:
    match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _kind_from_content_type(content_type: str | None) -> MediaKind:
    if not content_type:
        return MediaKind.UNKNOWN
    ct = content_type.lower()
    if ct.startswith("image/"):
        return MediaKind.IMAGE
    if ct.startswith("video/"):
        return MediaKind.VIDEO
    if "pdf" in ct:
        return MediaKind.PDF
    if ct.startswith("text/html"):
        return MediaKind.WEBPAGE
    return MediaKind.UNKNOWN


def _kind_from_url(url: str) -> MediaKind:
    if re.search(r"\.(png|jpe?g|gif|webp|avif|svg)(\?.*)?$", url, re.IGNORECASE):
        return MediaKind.IMAGE
    if re.search(r"\.(mp4|webm|mov|m4v)(\?.*)?$", url, re.IGNORECASE):
        return MediaKind.VIDEO
    if re.search(r"\.pdf(\?.*)?$", url, re.IGNORECASE):
        return MediaKind.PDF
    return MediaKind.UNKNOWN


async def _is_safe_url(url: str) -> bool:
    """SSRF guard — reject non-http(s) schemes and hosts that resolve to
    loopback, private, link-local, or otherwise reserved IP addresses.
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    try:
        addr_infos = await asyncio.to_thread(socket.getaddrinfo, hostname, None)
    except socket.gaierror:
        return False

    for addr_info in addr_infos:
        ip = ipaddress.ip_address(addr_info[4][0])
        if (
            ip.is_loopback
            or ip.is_private
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return False

    return True


class UnsafeUrlError(Exception):
    """Raised when a request (or a redirect hop) targets an unsafe URL."""


async def _ssrf_request_hook(request: httpx.Request) -> None:
    """httpx request event hook — runs on every request, including each
    redirect hop, so redirects cannot escape the SSRF guard.
    """
    if not await _is_safe_url(str(request.url)):
        raise UnsafeUrlError(f"Blocked request to unsafe URL: {request.url}")


def _http_client() -> httpx.AsyncClient:
    """HTTP client that validates every hop against the SSRF guard."""
    return httpx.AsyncClient(
        follow_redirects=True,
        event_hooks={"request": [_ssrf_request_hook]},
    )


@broker.task
async def enrich_url_task(reference_id: str, original_url: str):
    ref = await Reference.get(reference_id)
    if not ref:
        return

    if not await _is_safe_url(original_url):
        logger.warning(
            "Rejected unsafe URL for reference %s: %s", reference_id, original_url
        )
        ref.is_processed = False
        await ref.save()
        return

    provider = _detect_provider(original_url)

    # YouTube — oEmbed
    if provider == "youtube":
        video_id = _youtube_id(original_url)
        if video_id:
            try:
                async with _http_client() as client:
                    resp = await client.get(
                        f"https://www.youtube.com/oembed?format=json&url={original_url}",
                        headers=HEADERS,
                        timeout=10,
                    )
                    if resp.is_success:
                        data = resp.json()
                        ref.title = data.get("title")
                        ref.description = (
                            f"YouTube video by {data['author_name']}"
                            if data.get("author_name")
                            else None
                        )
                        ref.thumbnail_url = data.get("thumbnail_url")
                        ref.embed_url = f"https://www.youtube.com/embed/{video_id}"
            except UnsafeUrlError as exc:
                logger.warning("Rejected unsafe redirect for %s: %s", original_url, exc)
                ref.is_processed = False
                await ref.save()
                return
            except Exception:
                logger.exception(
                    "Failed to fetch YouTube oEmbed data for %s", original_url
                )

        ref.media = MediaKind.VIDEO
        ref.provider = "youtube"
        ref.final_url = original_url
        ref.is_processed = True
        await ref.save()
        return

    # HEAD + fallback GET to detect content-type
    content_type = None
    final_url = original_url

    try:
        async with _http_client() as client:
            head = await client.head(original_url, headers=HEADERS, timeout=10)
            content_type = head.headers.get("content-type")
            final_url = str(head.url)
    except UnsafeUrlError as exc:
        logger.warning("Rejected unsafe redirect for %s: %s", original_url, exc)
        ref.is_processed = False
        await ref.save()
        return
    except Exception:
        logger.exception("Failed to HEAD request %s", original_url)

    media = _kind_from_content_type(content_type)

    if media == MediaKind.UNKNOWN:
        media = _kind_from_url(original_url)

    # Image from URL — download and run full pipeline
    if media == MediaKind.IMAGE:
        suffix = _suffix_from_url(original_url) or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = tmp.name

        try:
            async with _http_client() as client:
                resp = await client.get(
                    original_url, headers=HEADERS, timeout=30
                )
                resp.raise_for_status()

            def _write_temp_file(path: str, data: bytes) -> None:
                with open(path, "wb") as f:
                    f.write(data)

            await asyncio.to_thread(_write_temp_file, temp_path, resp.content)

            img = await asyncio.to_thread(cv2.imread, temp_path)
            if img is not None:
                stored_name = f"{uuid4().hex}_url_image{suffix}"
                object_path = f"uploads/{stored_name}"

                await asyncio.to_thread(
                    minio_client.fput_object,
                    config.minio_bucket,
                    object_path,
                    temp_path,
                )

                # The pipeline enriches and saves the placeholder itself —
                # single final save, no duplicate Reference inserted.
                ref.final_url = final_url
                pipeline = ImageServices(
                    temp_path,
                    original_url,
                    stored_name,
                    object_path,
                    content_type,
                    reference=ref,
                )
                await pipeline()
                return
            ref.is_processed = False
        except UnsafeUrlError as exc:
            logger.warning("Rejected unsafe redirect for %s: %s", original_url, exc)
            ref.is_processed = False
        except Exception:
            logger.exception("Failed to download/process image URL %s", original_url)
            ref.is_processed = False
        finally:
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)

        # Failure path — the pipeline did not save the placeholder.
        ref.media = MediaKind.IMAGE
        ref.final_url = final_url
        ref.content_type = content_type
        await ref.save()
        return

    # Webpage or other — scrape OG metadata
    if media == MediaKind.WEBPAGE or not ref.thumbnail_url:
        try:
            async with _http_client() as client:
                resp = await client.get(
                    original_url, headers=HEADERS, timeout=10
                )
                html = resp.text[:16384]

                ref.title = (
                    _og(html, "og:title")
                    or _og(html, "twitter:title")
                    or _title_tag(html)
                )
                ref.description = _og(html, "og:description") or _og(
                    html, "twitter:description"
                )
                ref.thumbnail_url = (
                    _og(html, "og:image") or _og(html, "twitter:image")
                )
                ref.embed_url = _og(html, "og:video") or _og(
                    html, "og:video:url"
                )
        except UnsafeUrlError as exc:
            logger.warning("Rejected unsafe redirect for %s: %s", original_url, exc)
            ref.is_processed = False
            await ref.save()
            return
        except Exception:
            logger.exception("Failed to scrape metadata for %s", original_url)

    ref.media = media
    ref.provider = provider
    ref.final_url = final_url
    ref.content_type = content_type
    ref.is_processed = True
    await ref.save()


def _suffix_from_url(url: str) -> str | None:
    from urllib.parse import urlparse

    path = urlparse(url).path.lower()
    for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".svg"):
        if path.endswith(ext):
            return ext
    return ".jpg"
