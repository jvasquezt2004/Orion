from pydantic_settings import BaseSettings
from pydantic import computed_field
from dotenv import load_dotenv
import os

load_dotenv()

class Config(BaseSettings):
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "app"

    minio_endpoint: str = "http://localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "app-bucket"
    minio_use_ssl: bool = False
    minio_public_url: str | None = None

    redis_host: str = "localhost"
    redis_port: int = 6379

    @computed_field
    @property
    def database_url(self) -> str:
        return f"postgres://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @computed_field
    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"

    class Config:
        env_file = ".env"
        extra = "allow"

config = Config()