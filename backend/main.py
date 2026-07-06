from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import config
from app.db.init import init_beanie_app
from app.core.logging import setup_logging
from app.api.upload import router as upload_router
from app.api.urls import router as urls_router
from app.api.registries import router as registries_router
from app.api.config import router as config_router
from app.api.files import router as files_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    client = await init_beanie_app(config.mongo_uri, config.mongo_db)
    yield
    await client.close()


app = FastAPI(
    title="Orion API",
    lifespan=lifespan,
)

app.include_router(upload_router, prefix="/api")
app.include_router(urls_router, prefix="/api")
app.include_router(registries_router, prefix="/api")
app.include_router(config_router, prefix="/api")
app.include_router(files_router, prefix="/api")
