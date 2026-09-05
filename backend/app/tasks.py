from datetime import datetime

from sqlalchemy import select

from app.crawl_lock import (
    CrawlLockUnavailable,
    acquire_crawl_all_lock,
    release_crawl_all_lock,
)
from app.connectors import seed_master_sources
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
def crawl_active_sources(lock_token: str | None = None) -> dict:
    """Scheduled job: crawl all active sources and let CrawlService create versions/notifications."""
    try:
        owned_lock_token = acquire_crawl_all_lock(lock_token)
    except CrawlLockUnavailable as exc:
        return {
            'status': 'failed',
            'error': f'{exc.__class__.__name__}: {str(exc)}',
            'processed_sources': 0,
            'results': [],
            'success': [],
            'failed': [],
            'timestamp': datetime.now().isoformat(),
        }

    if owned_lock_token is None:
        return {
            'status': 'already_running',
            'processed_sources': 0,
            'results': [],
            'success': [],
            'failed': [],
            'timestamp': datetime.now().isoformat(),
        }

    db = SessionLocal()
    try:
        try:
            # Scheduled runs can be the first crawl after deployment; do not
            # depend on a separate manual seed request to discover all 99
            # catalog sources.
            seed_master_sources(db)
        except Exception as exc:
            db.rollback()
            return {
                'status': 'failed',
                'error': f'{exc.__class__.__name__}: {str(exc)}',
                'processed_sources': 0,
                'results': [],
                'success': [],
                'failed': [],
                'timestamp': datetime.now().isoformat(),
            }

        source_snapshots = [
            (source.id, source.name, source.source_type)
            for source in db.execute(
                select(Source).where(Source.active.is_(True)).order_by(Source.id.asc())
            ).scalars().all()
        ]
        results = []
        for source_id, source_name, source_type in source_snapshots:
            service = CrawlService(db)
            try:
                results.append(service.crawl_source(source_id))
            except Exception as exc:  # keep one broken source from killing the whole schedule
                db.rollback()
                results.append({
                    'source_id': source_id,
                    'source_name': source_name,
                    'source_type': source_type,
                    'status': 'failed',
                    'error': f'{exc.__class__.__name__}: {str(exc)}',
                })
        failed = [result for result in results if result.get('status') in {'failed', 'error'}]
        successful = [
            result for result in results
            if result.get('status') not in {'failed', 'error'}
        ]
        return {
            'status': 'partial_failure' if failed else 'success',
            'processed_sources': len(source_snapshots),
            'results': results,
            'success': successful,
            'failed': failed,
            'timestamp': datetime.now().isoformat(),
        }
    finally:
        db.close()
        try:
            release_crawl_all_lock(owned_lock_token)
        except CrawlLockUnavailable:
            # The key has a TTL and will self-expire if Redis is temporarily
            # unavailable during cleanup.  Do not turn a completed crawl into
            # a failed Celery task solely because unlock could not be sent.
            pass
