from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Observador de Concursos"
    app_env: str = "development"
    app_debug: bool = True
    api_port: int = 8000
    legacy_crawler_enabled: bool = False
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    database_url: str = "postgresql+psycopg://postgres:postgres@postgres:5432/observador"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7
    # Push is fail-closed: enabling it is an explicit deployment decision.
    push_dispatch_enabled: bool = False
    push_expo_url: str = "https://exp.host/--/api/v2/push/send"
    push_timeout_seconds: float = 5.0
    push_batch_size: int = 100
    push_max_attempts: int = 5
    push_retry_base_seconds: int = 30
    push_retry_max_seconds: int = 3600
    push_lease_seconds: int = 120

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
