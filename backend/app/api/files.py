import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from minio.error import S3Error
from app.core.minio_client import minio_client
from app.core.config import config

router = APIRouter()


@router.get("/files/{path:path}")
async def get_file(path: str):
    try:
        url = await asyncio.to_thread(
            minio_client.presigned_get_object,
            bucket_name=config.minio_bucket,
            object_name=path,
        )
    except S3Error as exc:
        if exc.code in ("NoSuchKey", "NoSuchBucket"):
            raise HTTPException(status_code=404, detail="File not found") from exc
        raise HTTPException(status_code=502, detail="Storage service error") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Storage service error") from exc

    return RedirectResponse(url=url)