from tortoise import fields
from tortoise.models import Model
from enum import Enum

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

class Reference(Model):
    id = fields.UUIDField(pk=True)
    type = fields.CharEnumField(ReferenceType, max_length=20)
    media = fields.CharEnumField(MediaKind, max_length=20)
    original_name = fields.CharField(max_length=255)
    stored_name = fields.CharField(max_length=255)
    bucket = fields.CharField(max_length=255)
    object_path = fields.CharField(max_length=1024)
    is_processed = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "references"