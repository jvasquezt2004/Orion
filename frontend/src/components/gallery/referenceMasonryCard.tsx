import { useEffect, useRef, useState } from "react"
import { cn } from "#/lib/utils"
import { PUBLIC_BACKEND_URL } from "#/lib/backend"
import type { Reference } from "#/lib/types"

type ReferenceMasonryCardProps = {
  reference: Reference
  index: number
}

const editorialHeights = ["min-h-28", "min-h-40", "min-h-32", "min-h-48"]
const imageAspectRatios = [
  "aspect-[1/1] sm:aspect-[4/5]",
  "aspect-[1/1] sm:aspect-[3/4]",
  "aspect-[1/1]",
  "aspect-[1/1] sm:aspect-[4/3]",
]

function getReferenceImage(reference: Reference) {
  if (reference.thumbnail_url) return reference.thumbnail_url
  if (reference.media === "image" && reference.object_path) {
    const encodedPath = reference.object_path
      .split("/")
      .map(encodeURIComponent)
      .join("/")
    return `${PUBLIC_BACKEND_URL}/api/files/${encodedPath}`
  }
  return undefined
}

function getImageAspectRatio(reference: Reference, index: number) {
  if (reference.provider === "youtube" || reference.media === "video") {
    return "aspect-video"
  }
  if (reference.media === "webpage") {
    return "aspect-[16/10]"
  }
  return imageAspectRatios[index % imageAspectRatios.length]
}

function titleFromUrl(url?: string) {
  if (!url) return undefined
  try {
    const parsed = new URL(url)
    const lastPathSegment = parsed.pathname.split("/").filter(Boolean).at(-1)
    if (!lastPathSegment) return parsed.hostname.replace(/^www\./, "")
    return decodeURIComponent(lastPathSegment)
      .replace(/\.[a-z0-9]+$/i, "")
      .replaceAll("-", " ")
      .replaceAll("_", " ")
      .trim()
  } catch {
    return undefined
  }
}

function isWeakDisplayTitle(title?: string) {
  if (!title) return true
  const normalized = title.trim().toLowerCase()
  return (
    normalized === "youtube" ||
    normalized === "- youtube" ||
    /^(image|video|canvas|clipboard|pasted image|download)(\s*\(\d+\))?\.[a-z0-9]+$/i.test(
      normalized
    )
  )
}

function getFallbackTitle(reference: Reference) {
  if (reference.provider === "youtube") return "YouTube video"
  return (
    titleFromUrl(reference.final_url ?? reference.original_url ?? undefined) ??
    reference.media
  )
}

function getDisplayTitle(reference: Reference) {
  const title = reference.title ?? reference.original_name
  if (isWeakDisplayTitle(title)) return getFallbackTitle(reference)
  return (
    title ??
    titleFromUrl(reference.final_url ?? reference.original_url ?? undefined) ??
    reference.provider ??
    reference.media
  )
}

function getMetaLabel(reference: Reference) {
  if (reference.provider) return reference.provider
  return reference.media
}

function getSourceLabel(reference: Reference) {
  if (!reference.original_url) return "clipboard"
  return "url"
}

function isLikelyUrl(value: string) {
  return value.startsWith("http://") || value.startsWith("https://")
}

export function ReferenceMasonryCard({
  reference,
  index,
}: ReferenceMasonryCardProps) {
  const [imageLoaded, setImageLoaded] = useState(false)
  const [imageFailed, setImageFailed] = useState(false)
  const imageRef = useRef<HTMLImageElement>(null)
  const image = getReferenceImage(reference)
  const title = getDisplayTitle(reference)
  const meta = getMetaLabel(reference)
  const source = getSourceLabel(reference)
  const fallbackHeight = editorialHeights[index % editorialHeights.length]
  const imageAspectRatio = getImageAspectRatio(reference, index)

  useEffect(() => {
    setImageLoaded(false)
    setImageFailed(false)
  }, [image])

  useEffect(() => {
    const imageElement = imageRef.current
    if (imageElement?.complete && imageElement.naturalWidth > 0) {
      setImageLoaded(true)
    }
  }, [image])

  return (
    <div data-reference-card data-reference-id={reference.id} className="group min-w-0">
      {image && !imageFailed ? (
        <div>
          <div
            className={cn(
              imageAspectRatio,
              "relative overflow-hidden rounded-2xl border border-white/10 bg-[#0a1418] transition duration-300 group-hover:border-[#4fb8b2]/80"
            )}
          >
            <img
              ref={imageRef}
              src={image}
              alt=""
              loading="lazy"
              decoding="async"
              onLoad={() => setImageLoaded(true)}
              onError={() => setImageFailed(true)}
              className={cn(
                "h-full w-full object-cover grayscale-[10%] contrast-105 transition duration-700 group-hover:grayscale-0 group-hover:contrast-110",
                imageLoaded ? "opacity-100 blur-0" : "opacity-0 blur-md"
              )}
            />
          </div>
          <div className="space-y-1.5 border-0 px-0.5 pb-0 pt-2">
            <div className="flex items-center justify-between gap-2 font-mono text-[0.52rem] uppercase tracking-normal text-[#4fb8b2]">
              <span className="truncate">/{meta}</span>
              <span className="text-[#afcdc8]">{source}</span>
              <span>{String(index + 1).padStart(2, "0")}</span>
            </div>
            <h3 className="line-clamp-2 text-pretty text-center text-[0.68rem] font-medium uppercase leading-tight text-[#d7ece8]/90 [overflow-wrap:anywhere]">
              {title}
            </h3>
            {reference.description ? (
              <p className="line-clamp-2 text-center font-mono text-[0.54rem] uppercase leading-[1.25] text-[#afcdc8]">
                {reference.description}
              </p>
            ) : null}
          </div>
        </div>
      ) : (
        <div
          className={cn(
            fallbackHeight,
            "flex flex-col justify-between overflow-hidden rounded-2xl border border-white/10 bg-[#0f1a1e]/92 p-3 transition duration-300 group-hover:border-[#4fb8b2]/80"
          )}
        >
          <div className="flex items-center justify-between font-mono text-[0.58rem] uppercase text-[#afcdc8]">
            <span>{reference.media}</span>
            <span>{reference.is_processed ? "ready" : "pending"}</span>
          </div>
          <h3
            className={cn(
              "line-clamp-5 overflow-hidden font-mono uppercase leading-[1.18] text-[#d7ece8] [overflow-wrap:anywhere]",
              isLikelyUrl(title)
                ? "text-[0.66rem]"
                : "text-balance text-[0.82rem] font-medium"
            )}
          >
            {title}
          </h3>
          <div className="mt-4 h-px w-10 bg-[#4fb8b2]/70" />
          <div className="space-y-1.5 border-0 px-0.5 pb-0 pt-2">
            <div className="flex items-center justify-between gap-2 font-mono text-[0.52rem] uppercase tracking-normal text-[#4fb8b2]">
              <span className="truncate">/{meta}</span>
              <span className="text-[#afcdc8]">{source}</span>
              <span>{String(index + 1).padStart(2, "0")}</span>
            </div>
            <h3 className="line-clamp-2 text-pretty text-center text-[0.68rem] font-medium uppercase leading-tight text-[#d7ece8]/90 [overflow-wrap:anywhere]">
              {title}
            </h3>
            {reference.description ? (
              <p className="line-clamp-2 text-center font-mono text-[0.54rem] uppercase leading-[1.25] text-[#afcdc8]">
                {reference.description}
              </p>
            ) : null}
          </div>
        </div>
      )}
    </div>
  )
}
