import asyncio
import logging
import os
from uuid import uuid4

import cv2

from app.core.config import config
from app.core.minio_client import minio_client
from app.db.reference import MediaKind, Reference, ReferenceType
from app.services.image_services import ImageServices

logger = logging.getLogger(__name__)


async def process_file(
    temp_path: str, original_name: str, content_type: str | None = None
):
    stored_name = f"{uuid4().hex}_{original_name}"
    object_path = f"uploads/{stored_name}"

    is_processed = False

    try:
        img = await asyncio.to_thread(cv2.imread, temp_path)

        if img is not None:
            try:
                await asyncio.to_thread(
                    minio_client.fput_object,
                    config.minio_bucket,
                    object_path,
                    temp_path,
                )

                image_pipeline = ImageServices(
                    temp_path, original_name, stored_name, object_path, content_type
                )

                await image_pipeline()
                is_processed = True
            except Exception:
                logger.exception(
                    "Failed to process image file %s (stored as %s)",
                    original_name,
                    stored_name,
                )
                await Reference(
                    original_name=original_name,
                    stored_name=stored_name,
                    bucket=config.minio_bucket,
                    object_path=object_path,
                    is_processed=False,
                    type=ReferenceType.REFERENCE,
                    media=MediaKind.IMAGE,
                    content_type=content_type,
                ).insert()
        else:
            await asyncio.to_thread(
                minio_client.fput_object,
                config.minio_bucket,
                object_path,
                temp_path,
                content_type="application/octet-stream",
            )

            await Reference(
                original_name=original_name,
                stored_name=stored_name,
                bucket=config.minio_bucket,
                object_path=object_path,
                is_processed=is_processed,
                type=ReferenceType.REFERENCE,
                media=MediaKind.UNKNOWN,
                content_type=content_type,
            ).insert()

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
