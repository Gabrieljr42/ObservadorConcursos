from types import SimpleNamespace

from sqlalchemy import func, select

from test_tenderproof_publication import env
from app.models import Notification
from app.tenderproof import publication as pub
from app.tenderproof import notification_tasks as delivery
from app.tasks import scheduled_crawl_active_sources
from app.tenderproof.publication_models import PublicationOutbox


def test_legacy_timer_does_not_touch_database_when_disabled(monkeypatch):
    monkeypatch.setattr('app.tasks.get_settings', lambda: SimpleNamespace(legacy_crawler_enabled=False))
    monkeypatch.setattr('app.tasks.crawl_active_sources.run', lambda: (_ for _ in ()).throw(AssertionError('legacy executed')))
    assert scheduled_crawl_active_sources.run()['status'] == 'disabled'


def test_legacy_timer_explicit_opt_in(monkeypatch):
    monkeypatch.setattr('app.tasks.get_settings', lambda: SimpleNamespace(legacy_crawler_enabled=True))
    monkeypatch.setattr('app.tasks.crawl_active_sources.run', lambda: {'status': 'success'})
    assert scheduled_crawl_active_sources.run()['status'] == 'success'


def test_notifications_disabled_does_not_open_database(monkeypatch):
    monkeypatch.delenv('TENDERPROOF_INTERNAL_NOTIFICATIONS_ENABLED', raising=False)
    monkeypatch.setattr(delivery, 'SessionLocal', lambda: (_ for _ in ()).throw(AssertionError('database opened')))
    assert delivery.deliver_internal_notifications.run()['status'] == 'disabled'


def test_internal_delivery_is_opt_in_and_deduplicated(env, monkeypatch):
    db, factory, user, contest, run, store = env
    proposal = pub.create_proposal(db, run=run, concurso_id=contest.id, user=user, store=store)
    pub.approve_proposal(db, proposal_id=proposal['id'], proposal_hash=proposal['proposal_hash'],
                        fields=['inscricao_fim'], user=user, store=store)
    pub.apply_proposal(db, proposal_id=proposal['id'], proposal_hash=proposal['proposal_hash'], user=user, store=store)
    monkeypatch.setattr(delivery, 'SessionLocal', factory)
    monkeypatch.setenv('TENDERPROOF_INTERNAL_NOTIFICATIONS_ENABLED', 'true')
    monkeypatch.setenv('TENDERPROOF_PUBLISHER_USER_IDS', '2')
    assert delivery.deliver_internal_notifications.run()['delivered'] == 0
    monkeypatch.setenv('TENDERPROOF_PUBLISHER_USER_IDS', '1')
    original = delivery.drain_outbox
    monkeypatch.setattr(delivery, 'drain_outbox', lambda *a, **kw: (_ for _ in ()).throw(RuntimeError('controlled delivery failure')))
    assert delivery.deliver_internal_notifications.run()['failed'] == 1
    with factory() as check:
        assert check.scalar(select(PublicationOutbox.attempts)) == 1
        assert check.scalar(select(PublicationOutbox.state)) == 'pending'
    monkeypatch.setattr(delivery, 'drain_outbox', original)
    first = delivery.deliver_internal_notifications.run()
    assert first['delivered'] == 1 and first['created'] == 1
    assert delivery.deliver_internal_notifications.run()['delivered'] == 0
    assert db.scalar(select(func.count()).select_from(Notification)) == 1
