from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID, uuid4

from beanie import Document, Indexed
from pydantic import Field


class User(Document):
    id: UUID = Field(default_factory=uuid4)
    email: Annotated[str, Indexed(unique=True)]
    hashed_password: str
    role: str = "user"
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
