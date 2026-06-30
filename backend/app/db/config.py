from app.core.config import config

TORTOISE_ORM = {
    "connections": {"default": config.database_url},
    "apps": {
        "models": {
            "models": ["app.db.schema"],
            "default_connection": "default",
            "migrations": "app.db.migrations"
        }
    }
}