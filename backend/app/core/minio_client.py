from minio import Minio
from app.core.config import config

minio_client = Minio(
    config.minio_endpoint,
    access_key=config.minio_access_key,
    secret_key=config.minio_secret_key,
    secure=config.minio_use_ssl
)

def ensure_bucket():
    if not minio_client.bucket_exists(config.minio_bucket):
        minio_client.make_bucket(config.minio_bucket)