from fastapi import APIRouter
from app.core.config import config

router = APIRouter()


@router.get("/config/minio-url")
async def get_minio_url():
    public_url = config.minio_public_url
    if not public_url:
        scheme = "https" if config.minio_use_ssl else "http"
        public_url = f"{scheme}://{config.minio_endpoint}/{config.minio_bucket}"
    return {"public_url": public_url}
