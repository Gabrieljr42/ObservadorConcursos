from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "observador",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Sao_Paulo",
    enable_utc=False,
    beat_schedule={
        "heartbeat-crawler": {
            "task": "app.tasks.heartbeat",
            "schedule": crontab(minute="*/15"),
        },
        "crawl-active-sources-hourly": {
            "task": "app.tasks.crawl_active_sources",
            "schedule": crontab(minute=0),
        }
    },
)
