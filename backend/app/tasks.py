from datetime import datetime

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Source
from app.services import CrawlService
from app.worker import celery_app


@celery_app.task(name='app.tasks.heartbeat')
def heartbeat() -> dict:
    return {
        'status': 'ok',
        'message': 'scheduler ativo',
        'timestamp': datetime.now().isoformat(),
    }


@celery_app.task(name='app.tasks.crawl_source')
def crawl_source(source_id: int) -> dict:
    db = SessionLocal()
    try:
        service = CrawlService(db)
        result = service.crawl_source(source_id)
        return {
            'status': 'success',
            **result,
            'timestamp': datetime.now().isoformat(),
        }
    finally:
        db.close()


@celery_app.task(name='app.tasks.crawl_active_sources')
def crawl_active_sources() -> dict:
    """Scheduled job: crawl all active sources and let CrawlService create versions/notifications."""
    db = SessionLocal()
    try:
        sources = db.execute(
            select(Source).where(Source.active.is_(True)).order_by(Source.id.asc())
        ).scalars().all()
        results = []
        for source in sources:
            service = CrawlService(db)
            try:
                results.append(service.crawl_source(source.id))
            except Exception as exc:  # keep one broken source from killing the whole schedule
                results.append({
                    'source_id': source.id,
                    'source_name': source.name,
                    'status': 'error',
                    'error': str(exc),
                })
        return {
            'status': 'success',
            'processed_sources': len(sources),
            'results': results,
            'timestamp': datetime.now().isoformat(),
        }
    finally:
        db.close()
