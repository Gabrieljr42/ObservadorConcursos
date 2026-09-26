from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "observador",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks", "app.tenderproof.continuous_tasks", "app.tenderproof.notification_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Sao_Paulo",
    enable_utc=False,
    task_routes={"app.tenderproof.continuous.*": {"queue": "tenderproof"}},
    beat_schedule={
        "tenderproof-continuous": {
            "task": "app.tenderproof.continuous.tick",
            "schedule": 30.0,
        },
        "heartbeat-crawler": {
            "task": "app.tasks.heartbeat",
            "schedule": crontab(minute="*/15"),
        },
        "crawl-active-sources-hourly": {
            "task": "app.tasks.scheduled_crawl_active_sources",
            "schedule": crontab(minute=0),
        },
        "tenderproof-internal-notifications": {
            "task": "app.tenderproof.notifications.deliver",
            "schedule": 30.0,
        },
    },
)
