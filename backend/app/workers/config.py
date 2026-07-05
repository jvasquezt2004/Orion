from taskiq_redis import RedisStreamBroker
from taskiq import TaskiqEvents, Context
from app.core.config import config
from app.core.minio_client import ensure_bucket
from app.db.init import init_beanie_app

broker = RedisStreamBroker(url=config.redis_url)


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: Context) -> None:
    ensure_bucket()
    client = await init_beanie_app(config.mongo_uri, config.mongo_db)
    state.mongo_client = client


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(state: Context) -> None:
    if state.mongo_client:
        state.mongo_client.close()


from app.workers import process_file
