from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

import pymongo
from pymongo import IndexModel
from pydantic import Field
from beanie import Document


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


class Reference(Document):
    id: UUID = Field(default_factory=uuid4)
    type: ReferenceType
    media: MediaKind
    original_name: str
    stored_name: str
    bucket: str
    object_path: str
    is_processed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None

    class Settings:
        name = "references"
        indexes = [
            IndexModel(
                [("created_at", pymongo.DESCENDING)],
                name="created_at_idx",
            )
        ]
