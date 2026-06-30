from app.workers.config import broker
import cv2
from uuid import uuid4
import asyncio
from app.core.minio_client import minio_client
from app.core.config import config
import os
from app.db.schema import Reference, MediaKind

@broker.task
async def process_file_task(temp_path: str, original_name: str):
    stored_name = f"{uuid4().hex}_{original_name}"
    object_path = f"uploads/{stored_name}"

    is_image = False
    is_processed = False

    try:
        img = cv2.imread(temp_path)

        if img is not None:
            is_image = True

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, threshold1=100, threshold2=200)

            processed_path = f"{temp_path}_canny.png"
            cv2.imwrite(processed_path, edges)

            await asyncio.to_thread(
                minio_client.fput_object,
                config.minio_bucket,
                object_path,
                processed_path,
                content_type="image/png"
            )

            os.remove(processed_path)
            is_processed = True
        else:
            await asyncio.to_thread(
                minio_client.fput_object,
                config.minio_bucket,
                object_path,
                temp_path,
                content_type="application/octet-stream"
            )

        await Reference.create(
            original_name=original_name,
            stored_name=stored_name,
            bucket=config.minio_bucket,
            object_path=object_path,
            is_processed=is_processed,
            type="reference",
            media=MediaKind.IMAGE if is_image else MediaKind.UNKNOWN
        )

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)