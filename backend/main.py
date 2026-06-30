import os
import shutil
import tempfile
from fastapi import FastAPI, UploadFile, HTTPException
from tortoise import Tortoise
from tortoise.contrib.fastapi import RegisterTortoise, tortoise_exception_handlers
from contextlib import asynccontextmanager

from app.core.config import config
from app.db.config import TORTOISE_ORM
from app.db.schema import Reference
from app.workers.process_file import process_file_task
from app.workers.config import broker
from app.core.minio_client import ensure_bucket
from app.core.logging import setup_logging
from app.api.upload import router as upload_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    async with RegisterTortoise(app, config=TORTOISE_ORM, generate_schemas=False):
        yield

app = FastAPI(
    title="Orion API",
    lifespan=lifespan,
    exception_handlers=tortoise_exception_handlers()
)

app.include_router(upload_router, prefix="/api")