from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID, uuid4

from beanie import Document, Indexed
from pydantic import Field


class Token(Document):
    id: UUID = Field(default_factory=uuid4)
    jti: Annotated[str, Indexed(unique=True)]
    user_id: UUID
    expires_at: datetime
    revoked: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "tokens"
