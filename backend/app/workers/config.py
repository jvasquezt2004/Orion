from taskiq_redis import RedisStreamBroker
from taskiq import TaskiqEvents, Context
from tortoise import Tortoise
from app.core.config import config
from app.core.minio_client import ensure_bucket
from app.db.config import TORTOISE_ORM

broker = RedisStreamBroker(url=config.redis_url)

@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: Context) -> None:
    ensure_bucket()
    await Tortoise.init(config=TORTOISE_ORM)

from app.workers import process_file