"""Shared Beanie initialization helper.

Used by both the FastAPI lifespan and the Taskiq worker startup
to initialize Beanie with the same set of Document models.
"""

from pymongo import AsyncMongoClient
from beanie import init_beanie

from app.db.reference import Reference


async def init_beanie_app(mongo_uri: str, mongo_db: str) -> AsyncMongoClient:
    """Initialize Beanie with the given MongoDB connection.

    Returns the client so callers can close it on shutdown.
    """
    client = AsyncMongoClient(mongo_uri)
    await init_beanie(
        database=client[mongo_db],
        document_models=[Reference],
    )
    return client
