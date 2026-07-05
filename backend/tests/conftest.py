import sys
from pathlib import Path

# Ensure the backend/ directory is on sys.path so `app` is importable.
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from mongomock_motor import AsyncMongoMockClient
from beanie import init_beanie
import httpx

from app.db.reference import Reference
from main import app


@pytest.fixture
async def mongo():
    """In-process mock Mongo + Beanie init.

    ASGITransport does NOT run the app lifespan, so this fixture owns
    Beanie initialization for the test suite.

    mongomock-motor 0.0.36 doesn't accept the authorizedCollections/nameOnly
    kwargs that Beanie >=2.1.0 passes to list_collection_names(). We monkey-patch
    the method to accept and ignore them.
    """
    client = AsyncMongoMockClient()
    db = client["test_db"]

    # Monkey-patch list_collection_names to accept extra kwargs
    _original_list_collections = db.list_collection_names

    async def _patched_list_collection_names(*args, **kwargs):
        # Strip kwargs that mongomock doesn't support
        kwargs.pop("authorizedCollections", None)
        kwargs.pop("nameOnly", None)
        return await _original_list_collections(*args, **kwargs)

    db.list_collection_names = _patched_list_collection_names

    await init_beanie(
        database=db,
        document_models=[Reference],
    )
    yield
    await Reference.delete_all()


@pytest.fixture
async def client(mongo):
    """Async HTTP client wired to the FastAPI app via ASGI transport."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
