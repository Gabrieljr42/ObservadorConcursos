from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Observador de Concursos"
    app_env: str = "development"
    app_debug: bool = True
    api_port: int = 8000
    database_url: str = "postgresql+psycopg://postgres:postgres@postgres:5432/observador"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
