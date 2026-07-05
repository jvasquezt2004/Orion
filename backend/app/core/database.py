"""Shared Beanie initialization helper.

Uses string paths for document_models to break the import cycle:
models import beanie.Document; this module would import models;
string paths let Beanie resolve them lazily.

In Slice 2, this list will be extended with "app.models.user" and
"app.models.token" — do NOT add them now.
"""

from pymongo import AsyncMongoClient
from beanie import init_beanie


async def init_beanie_app(mongo_uri: str, mongo_db: str) -> AsyncMongoClient:
    """Initialize Beanie with the given MongoDB connection.

    Returns the client so callers can close it on shutdown.
    """
    client = AsyncMongoClient(mongo_uri)
    await init_beanie(
        database=client[mongo_db],
        document_models=["app.models.reference"],
    )
    return client
