from taskiq_redis import RedisStreamBroker
from taskiq import TaskiqEvents, Context
from app.core.config import config
from app.core.minio_client import ensure_bucket
from app.db.init import init_beanie_app

# Redis streams use blocking reads; keep the socket unbounded so long image
# processing tasks do not make redis-py turn normal waiting into fatal timeouts.
broker = RedisStreamBroker(url=config.redis_url, socket_timeout=None)


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: Context) -> None:
    ensure_bucket()
    client = await init_beanie_app(config.mongo_uri, config.mongo_db)
    state.mongo_client = client


from app.workers import process_file
