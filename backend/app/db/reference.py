from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

import pymongo
from beanie import Document
from pydantic import Field
from pymongo import IndexModel

from app.models.image_models import RGB, ImageAnalysis, OkLab


class ReferenceType(str, Enum):
    REFERENCE = "reference"
    COMPOSITION = "composition"
    TYPEFACE = "typeface"
    PALETTE = "palette"


class MediaKind(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    PDF = "pdf"
    WEBPAGE = "webpage"
    UNKNOWN = "unknown"


class Color(Document):
    hex_code: str
    rgb: RGB
    oklab: OkLab
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "colors"
        indexes = [
            IndexModel(
                [("hex_code", pymongo.ASCENDING)],
                name="hex_code_unique_idx",
                unique=True,
            )
        ]


class Reference(Document):
    type: ReferenceType
    media: MediaKind
    original_name: str
    stored_name: str
    bucket: str
    object_path: str
    is_processed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    description: Optional[str] = None
    title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    content_type: Optional[str] = None
    original_url: Optional[str] = None
    final_url: Optional[str] = None
    provider: Optional[str] = None
    embed_url: Optional[str] = None
    image_analysis: Optional[ImageAnalysis] = None

    class Settings:
        name = "references"
        indexes = [
            IndexModel(
                [("created_at", pymongo.DESCENDING)],
                name="created_at_idx",
            )
        ]
