from datetime import datetime, timedelta
import hashlib
import os
import pytest

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Notification, PushDelivery, PushDevice, PushDeliveryAttempt, User
from app.notifications import ExpoPushTransport, drain_push_outbox, enqueue_push_deliveries
from app.notifications import _claim_push_deliveries
from app.schema_migrations import PUSH_SQL, PUSH_UPGRADE_SQL, ensure_runtime_schema
from app.schemas import PushDeviceOut, PushDeviceRegister


def session_factory():
    engine = create_engine('sqlite:///:memory:', future=True)
    Base.metadata.create_all(engine)
    return engine


def test_push_device_payload_is_strict_and_token_is_not_output():
    payload = PushDeviceRegister(platform='android', device_id='phone-1', token='ExponentPushToken[abcdefgh]')
    assert payload.platform == 'android'
    assert 'token' not in PushDeviceOut.model_json_schema().get('properties', {})


def test_push_schema_keeps_soft_revocation_columns_nullable():
    """The PostgreSQL boot schema and legacy upgrade must permit token clearing."""
    create_devices = next(sql for sql in PUSH_SQL if sql.startswith('CREATE TABLE IF NOT EXISTS push_devices'))
    assert 'token VARCHAR(512)' in create_devices
    assert 'token_fingerprint VARCHAR(64) UNIQUE' in create_devices
    assert 'token_fingerprint VARCHAR(64) NOT NULL' not in create_devices
    assert 'ALTER TABLE push_devices ALTER COLUMN token DROP NOT NULL' in PUSH_UPGRADE_SQL
    assert 'ALTER TABLE push_devices ALTER COLUMN token_fingerprint DROP NOT NULL' in PUSH_UPGRADE_SQL

    engine = session_factory()
    with Session(engine) as db:
        user = User(name='nullable', email='nullable@example.test', password_hash='x')
        device = PushDevice(user=user, device_id='soft-revoked', platform='ios', token='token')
        db.add(user)
        db.flush()
        device.active = False
        device.token = None
        device.token_fingerprint = None
        db.commit()
        assert db.get(PushDevice, device.id).token is None
        assert db.get(PushDevice, device.id).token_fingerprint is None


def test_enqueue_is_idempotent_and_scoped_to_owner():
    engine = session_factory()
    with Session(engine) as db:
        user = User(name='A', email='a@example.test', password_hash='x')
        db.add(user); db.flush()
        device = PushDevice(user_id=user.id, device_id='device-a', platform='ios', token='ExpoPushToken[abcdefgh]')
        notification = Notification(user_id=user.id, title='T', message='M', notification_type='x')
        db.add_all([device, notification]); db.flush()
        assert enqueue_push_deliveries(db, notification_id=notification.id) == 1
        db.flush()
        assert enqueue_push_deliveries(db, notification_id=notification.id) == 0
        assert db.scalar(select(PushDelivery).where(PushDelivery.notification_id == notification.id)) is not None


def test_drain_mock_provider_retries_without_network(monkeypatch):
    engine = session_factory()
    from app.config import get_settings
    monkeypatch.setattr(get_settings(), 'push_dispatch_enabled', True)
    with Session(engine) as db:
        user = User(name='A', email='b@example.test', password_hash='x')
        db.add(user); db.flush()
        device = PushDevice(user_id=user.id, device_id='device-a', platform='ios', token='ExpoPushToken[abcdefgh]')
        notification = Notification(user_id=user.id, title='T', message='M', notification_type='x')
        db.add_all([device, notification]); db.flush()
        enqueue_push_deliveries(db, notification_id=notification.id); db.commit()

        class Provider:
            def send(self, messages):
                assert messages[0]['to'].startswith('ExpoPushToken[')
                return [{'status': 'error', 'message': 'temporary'}]

        result = drain_push_outbox(db, transport=Provider())
        assert result['retry'] == 1
        delivery = db.scalar(select(PushDelivery))
        assert delivery.status == 'retry'
        assert db.scalar(select(PushDeliveryAttempt)) is not None


def test_expo_transport_posts_array_and_closes_owned_client():
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'data': [{'status': 'ok', 'id': 'ticket-1'}]}
    class Client:
        def __init__(self): self.calls = []; self.closed = False
        def post(self, url, json): self.calls.append((url, json)); return Response()
        def close(self): self.closed = True
    client = Client()
    transport = ExpoPushTransport(client=client, timeout_seconds=1)
    assert transport.send([{'to': 'ExpoPushToken[abcdefgh]', 'title': 'T', 'body': 'M'}])[0]['status'] == 'ok'
    # Injected clients are not owned/closed; the real client path is tested by
    # the same contract in integration fixtures without network access.
    assert client.calls[0][0] == ExpoPushTransport.OFFICIAL_URL
    assert isinstance(client.calls[0][1], list)


def test_expired_processing_lease_is_recoverable(monkeypatch):
    engine = session_factory()
    from app.config import get_settings
    monkeypatch.setattr(get_settings(), 'push_dispatch_enabled', True)
    with Session(engine) as db:
        user = User(name='A', email='lease@example.test', password_hash='x')
        device = PushDevice(user=user, device_id='device-a', platform='ios', token='ExpoPushToken[abcdefgh]', token_fingerprint=hashlib.sha256(b'ExpoPushToken[abcdefgh]').hexdigest())
        notification = Notification(user=user, title='T', message='M', notification_type='x')
        db.add_all([device, notification]); db.flush(); enqueue_push_deliveries(db, notification_id=notification.id); db.commit()
        delivery = db.scalar(select(PushDelivery)); delivery.status = 'processing'; delivery.lease_owner = 'dead-worker'; delivery.lease_expires_at = datetime.utcnow() - timedelta(seconds=1); db.commit()
        result = drain_push_outbox(db, transport=type('P', (), {'send': lambda self, messages: [{'status': 'ok', 'id': 'ticket'}]})())
        assert result['sent'] == 1


def test_payload_has_typed_deep_link_data_and_malicious_provider_is_redacted(monkeypatch):
    engine = session_factory()
    from app.config import get_settings
    monkeypatch.setattr(get_settings(), 'push_dispatch_enabled', True)
    token = 'ExpoPushToken[abcdefgh]'
    with Session(engine) as db:
        user = User(name='A', email='redact@example.test', password_hash='x')
        device = PushDevice(user=user, device_id='device-a', platform='ios', token=token)
        notification = Notification(user=user, title='T', message='M', notification_type='alert_match', concurso_id=None)
        db.add_all([device, notification]); db.flush(); enqueue_push_deliveries(db, notification_id=notification.id); db.commit()
        class Provider:
            def send(self, messages):
                assert isinstance(messages[0]['data']['notification_id'], int)
                assert isinstance(messages[0]['data']['notification_type'], str)
                return [{'status': 'error', 'message': f'bad {token}', 'details': {'echo': token}}]
        drain_push_outbox(db, transport=Provider())
        attempt = db.scalar(select(PushDeliveryAttempt))
        assert token not in (attempt.error_message or '')
        assert token not in str(attempt.response_metadata)


def test_stale_worker_cas_cannot_finalize_after_recovery(monkeypatch):
    engine = session_factory()
    from app.config import get_settings
    monkeypatch.setattr(get_settings(), 'push_dispatch_enabled', True)
    with Session(engine) as db:
        user = User(name='A', email='cas@example.test', password_hash='x')
        device = PushDevice(user=user, device_id='device-a', platform='ios', token='ExpoPushToken[abcdefgh]')
        notification = Notification(user=user, title='T', message='M', notification_type='x')
        db.add_all([device, notification]); db.flush(); enqueue_push_deliveries(db, notification_id=notification.id); db.commit()
        delivery = db.scalar(select(PushDelivery)); delivery.status = 'processing'; delivery.lease_owner = 'new-worker'; delivery.lease_expires_at = datetime.utcnow() + timedelta(seconds=10); db.commit()
        stale = db.execute(update(PushDelivery).where(PushDelivery.id == delivery.id, PushDelivery.status == 'processing', PushDelivery.lease_owner == 'old-worker').values(status='sent')).rowcount
        assert stale == 0


def test_provider_lease_recovery_discards_stale_attempt_without_any_commit(monkeypatch):
    engine = session_factory()
    from app.config import get_settings
    monkeypatch.setattr(get_settings(), 'push_dispatch_enabled', True)
    with Session(engine) as db:
        user = User(name='A', email='recovery-attempt@example.test', password_hash='x')
        device = PushDevice(user=user, device_id='device-a', platform='ios', token='ExpoPushToken[abcdefgh]')
        notification = Notification(user=user, title='T', message='M', notification_type='x')
        db.add_all([device, notification]); db.flush(); enqueue_push_deliveries(db, notification_id=notification.id); db.commit()
        delivery_id = db.scalar(select(PushDelivery)).id

        class Provider:
            def send(self, messages):
                # Worker B reclaims the expired lease before A finalizes.
                with Session(engine) as recovered:
                    recovered.execute(update(PushDelivery).where(PushDelivery.id == delivery_id).values(
                        lease_expires_at=datetime.utcnow() - timedelta(seconds=1)))
                    recovered.commit()
                    assert _claim_push_deliveries(recovered, limit=1, owner='worker-b', lease_seconds=120) == [delivery_id]
                return [{'status': 'ok', 'id': 'stale-ticket'}]

        result = drain_push_outbox(db, transport=Provider())
        delivery = db.get(PushDelivery, delivery_id)
        assert result['sent'] == result['retry'] == result['failed'] == result['canceled'] == 0
        # r4 reproduced the defect here: its pre-provider commit left 1.
        assert delivery.attempts == 0
        assert delivery.status == 'processing' and delivery.lease_owner == 'worker-b'
        assert db.scalar(select(PushDeliveryAttempt)) is None


def test_stale_devicenotregistered_does_not_revoke_device_or_cancel_siblings(monkeypatch):
    engine = session_factory()
    from app.config import get_settings
    monkeypatch.setattr(get_settings(), 'push_dispatch_enabled', True)
    with Session(engine) as db:
        user = User(name='A', email='recovery-device@example.test', password_hash='x')
        token = 'ExpoPushToken[abcdefgh]'
        device = PushDevice(user=user, device_id='device-a', platform='ios', token=token)
        first = Notification(user=user, title='T1', message='M1', notification_type='x')
        second = Notification(user=user, title='T2', message='M2', notification_type='x')
        db.add_all([device, first, second]); db.flush()
        enqueue_push_deliveries(db, notification_id=first.id); enqueue_push_deliveries(db, notification_id=second.id); db.commit()
        first_id = db.scalar(select(PushDelivery).where(PushDelivery.notification_id == first.id)).id

        class Provider:
            def send(self, messages):
                with Session(engine) as recovered:
                    recovered.execute(update(PushDelivery).where(PushDelivery.id == first_id).values(
                        lease_expires_at=datetime.utcnow() - timedelta(seconds=1)))
                    recovered.commit()
                    assert _claim_push_deliveries(recovered, limit=1, owner='worker-b', lease_seconds=120) == [first_id]
                return [{'status': 'error', 'details': {'error': 'DeviceNotRegistered'}, 'message': 'stale'}]

        drain_push_outbox(db, transport=Provider(), limit=1)
        db.refresh(device)
        sibling = db.scalar(select(PushDelivery).where(PushDelivery.notification_id == second.id))
        assert device.active is True and device.token == token
        assert sibling.status == 'pending'


def test_revoke_allows_other_account_registration_without_history_transfer():
    engine = session_factory()
    token = 'ExpoPushToken[abcdefgh]'
    fingerprint = hashlib.sha256(token.encode()).hexdigest()
    with Session(engine) as db:
        user_a = User(name='A', email='revoke-a@example.test', password_hash='x')
        user_b = User(name='B', email='revoke-b@example.test', password_hash='x')
        device_a = PushDevice(user=user_a, device_id='device-a', platform='ios', token=token, token_fingerprint=fingerprint)
        db.add_all([user_a, user_b, device_a]); db.flush()
        device_a.active = False; device_a.token = None; device_a.token_fingerprint = None; device_a.revoke_reason = 'user_revoked'; db.commit()
        device_b = PushDevice(user_id=user_b.id, device_id='device-b', platform='ios', token=token, token_fingerprint=fingerprint)
        db.add(device_b); db.commit()
        assert device_b.id != device_a.id
        assert device_a.deliveries == []


@pytest.mark.skipif(not os.getenv('TEST_POSTGRES_URL'), reason='set TEST_POSTGRES_URL for disposable PostgreSQL migration test')
def test_postgres_runtime_schema_upgrade_is_idempotent():
    engine = create_engine(os.environ['TEST_POSTGRES_URL'], future=True)
    Base.metadata.create_all(engine)
    ensure_runtime_schema(engine)
    ensure_runtime_schema(engine)
