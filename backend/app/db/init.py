"""Beanie initialization helper.

Initializes Beanie with the MongoDB connection and document models.
"""

import logging

from pymongo import AsyncMongoClient
from pymongo.errors import DuplicateKeyError
from beanie import init_beanie

from app.db.reference import Color, Reference

logger = logging.getLogger(__name__)


async def _dedupe_colors(db) -> None:
    """Remove duplicate colors documents sharing a hex_code, keeping the oldest.

    Required so the unique index on colors.hex_code can build against
    pre-existing data. Palette entries embed color values directly (no links
    to Color documents), so deleting redundant documents is safe. Idempotent:
    a no-op when the collection has no duplicates.
    """
    colors = db["colors"]
    pipeline = [
        {"$sort": {"created_at": 1, "_id": 1}},
        {
            "$group": {
                "_id": "$hex_code",
                "ids": {"$push": "$_id"},
                "count": {"$sum": 1},
            }
        },
        {"$match": {"count": {"$gt": 1}}},
    ]

    duplicate_ids = []
    cursor = await colors.aggregate(pipeline)
    async for group in cursor:
        # Keep the first (oldest) document per hex_code, delete the rest.
        duplicate_ids.extend(group["ids"][1:])

    if duplicate_ids:
        result = await colors.delete_many({"_id": {"$in": duplicate_ids}})
        logger.info(
            "Removed %d duplicate color documents before index build",
            result.deleted_count,
        )


async def init_beanie_app(mongo_uri: str, mongo_db: str) -> AsyncMongoClient:
    """Initialize Beanie with the given MongoDB connection.

    Returns the client so callers can close it on shutdown.
    """
    client = AsyncMongoClient(mongo_uri)
    db = client[mongo_db]

    await _dedupe_colors(db)

    try:
        await init_beanie(
            database=db,
            document_models=[Reference, Color],
        )
    except DuplicateKeyError as exc:
        raise RuntimeError(
            "Failed to build the unique index on colors.hex_code: duplicate "
            "hex_code documents remain after dedupe. Inspect the 'colors' "
            "collection manually and remove the remaining duplicates."
        ) from exc

    return client
