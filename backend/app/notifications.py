from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import uuid
from typing import Iterable, Protocol

import httpx
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Alert, Concurso, ConcursoVersion, Notification, PushDelivery, PushDeliveryAttempt, PushDevice

SIGNIFICANT_CHANGE_TYPES = {
    'amendment',
    'created',
    'status_changed',
    'dates_changed',
    'edital_changed',
    'values_changed',
    'vacancies_changed',
    'document_added',
}

AREA_KEYWORDS: dict[str, tuple[str, ...]] = {
    'assistencia_social': ('assistente social', 'serviço social', 'servico social', 'cras', 'creas'),
    'administrativa': ('assistente administrativo', 'agente administrativo', 'analista administrativo', 'administração', 'administracao'),
    'saude': ('saúde', 'saude', 'enfermeiro', 'técnico de enfermagem', 'tecnico de enfermagem', 'médico', 'medico', 'acs', 'agente comunitário de saúde', 'agente comunitario de saude', 'agente de combate'),
    'educacao': ('professor', 'pedagogo', 'supervisor escolar', 'educação', 'educacao'),
    'tecnologia_informacao': ('tecnologia da informação', 'tecnologia da informacao', 'técnico de informática', 'tecnico de informatica', 'analista de sistemas', 'desenvolvedor'),
}


def is_concurso_open(concurso: Concurso) -> bool:
    from app.registration_status import registration_situation
    return registration_situation(concurso) == 'open'


def _text_haystack(concurso: Concurso) -> str:
    raw_data = concurso.raw_data or {}
    cargo_candidates = raw_data.get('cargo_candidates') or []
    if not isinstance(cargo_candidates, list):
        cargo_candidates = []

    return ' '.join([
        concurso.titulo or '',
        concurso.orgao or '',
        concurso.cargo or '',
        ' '.join(str(job.get('nome') or '') for job in (concurso.cargos or []) if isinstance(job, dict)),
        concurso.area or '',
        concurso.cidade or '',
        concurso.uf or '',
        concurso.resumo or '',
        ' '.join(str(item) for item in cargo_candidates[:80]),
    ]).lower()


def _area_matches(alert_area: str, concurso: Concurso) -> bool:
    wanted = alert_area.strip().lower()
    current = (concurso.area or '').strip().lower()
    if not wanted:
        return True
    if current == wanted:
        return True

    # For multi-area concursos, use cargo candidates and summary as a secondary
    # signal so alerts for Administração/Assistência Social/Saúde still match.
    haystack = _text_haystack(concurso)
    keywords = AREA_KEYWORDS.get(wanted, (wanted,))
    return any(keyword.lower() in haystack for keyword in keywords)


def alert_matches_concurso(alert: Alert, concurso: Concurso) -> bool:
    if alert.uf and (concurso.uf or '').upper() != alert.uf.upper():
        return False
    if alert.cidade and alert.cidade.lower() not in (concurso.cidade or '').lower():
        return False
    if alert.banca and alert.banca.lower() not in (concurso.banca or '').lower():
        return False
    if alert.area and not _area_matches(alert.area, concurso):
        return False
    if alert.status and alert.status.lower() not in (concurso.status or '').lower():
        return False
    if alert.cargo_keyword:
        if alert.cargo_keyword.lower() not in _text_haystack(concurso):
            return False
    if alert.only_open and not is_concurso_open(concurso):
        return False
    return True


def should_notify_version(version: ConcursoVersion) -> bool:
    return version.change_type in SIGNIFICANT_CHANGE_TYPES or 'cargos' in (version.changed_fields or {})


def _notification_payload(alert: Alert, concurso: Concurso, version: ConcursoVersion) -> tuple[str, str, str]:
    if version.change_type == 'created':
        return (
            'alert_match',
            f'Novo concurso compatível: {concurso.titulo[:180]}',
            f'O alerta "{alert.name}" encontrou um concurso da banca {concurso.banca}.',
        )

    if version.change_type == 'document_added':
        return (
            f'document_added_{version.id}',
            f'Nova publicação: {concurso.titulo[:180]}',
            f'Alerta "{alert.name}": {version.change_summary or "Uma nova publicação foi adicionada ao concurso."}',
        )

    # Unique per version while keeping the type readable enough for debugging.
    notification_type = f'version_update_{version.id}'
    title = f'Atualização em concurso: {concurso.titulo[:170]}'
    message = version.change_summary or 'Um concurso compatível com seu alerta foi atualizado.'
    return notification_type, title, f'Alerta "{alert.name}": {message}'


def create_notifications_for_version(db: Session, *, concurso: Concurso, version: ConcursoVersion) -> int:
    """Create internal notifications for alert users affected by a concurso version.

    This is called by the crawl/upsert flow. It covers both new concursos
    (alert_match) and meaningful updates (version_update_<id>). The mobile app
    already reads /me/notifications, so this makes version changes visible without
    requiring push notification infrastructure yet.
    """
    if not should_notify_version(version):
        return 0

    alerts = db.execute(select(Alert).where(Alert.active.is_(True))).scalars().all()
    created = 0

    for alert in alerts:
        if not alert_matches_concurso(alert, concurso):
            continue

        notification_type, title, message = _notification_payload(alert, concurso, version)

        exists = db.execute(
            select(Notification).where(
                Notification.user_id == alert.user_id,
                Notification.alert_id == alert.id,
                Notification.concurso_id == concurso.id,
                Notification.notification_type == notification_type,
            )
        ).scalar_one_or_none()
        if exists:
            continue

        db.add(Notification(
            user_id=alert.user_id,
            alert_id=alert.id,
            concurso_id=concurso.id,
            notification_type=notification_type,
            title=title,
            message=message,
        ))
        db.flush()
        enqueue_push_deliveries(db, notification_id=db.execute(
            select(Notification.id).where(
                Notification.user_id == alert.user_id,
                Notification.alert_id == alert.id,
                Notification.concurso_id == concurso.id,
                Notification.notification_type == notification_type,
            )
        ).scalar_one())
        created += 1

    # Do not commit here; caller owns the transaction.
    return created


def run_alerts_for_user(db: Session, *, user_id: int, concursos: Iterable[Concurso]) -> int:
    """Existing manual alert-run behavior, extracted for reuse."""
    alerts = db.execute(select(Alert).where(Alert.user_id == user_id, Alert.active.is_(True))).scalars().all()
    created = 0
    for alert in alerts:
        for concurso in concursos:
            if not alert_matches_concurso(alert, concurso):
                continue
            exists = db.execute(
                select(Notification).where(
                    Notification.user_id == user_id,
                    Notification.alert_id == alert.id,
                    Notification.concurso_id == concurso.id,
                    Notification.notification_type == 'alert_match',
                )
            ).scalar_one_or_none()
            if exists:
                continue
            db.add(Notification(
                user_id=user_id,
                alert_id=alert.id,
                concurso_id=concurso.id,
                notification_type='alert_match',
                title=f'Novo concurso compatível: {concurso.titulo[:180]}',
                message=f'O alerta "{alert.name}" encontrou um concurso da banca {concurso.banca}.',
            ))
            db.flush()
            notification = db.execute(
                select(Notification).where(
                    Notification.user_id == user_id,
                    Notification.alert_id == alert.id,
                    Notification.concurso_id == concurso.id,
                    Notification.notification_type == 'alert_match',
                )
            ).scalar_one()
            enqueue_push_deliveries(db, notification_id=notification.id)
            created += 1
    return created


def enqueue_push_deliveries(db: Session, *, notification_id: int) -> int:
    """Create durable work rows; this function never performs network I/O."""
    notification = db.get(Notification, notification_id)
    if notification is None:
        return 0
    devices = db.execute(select(PushDevice).where(
        PushDevice.user_id == notification.user_id,
        PushDevice.active.is_(True),
    )).scalars().all()
    created = 0
    for device in devices:
        existing = db.execute(select(PushDelivery).where(
            PushDelivery.notification_id == notification_id,
            PushDelivery.device_id == device.id,
        )).scalar_one_or_none()
        if existing is None:
            # Savepoint contains the uniqueness race, preserving the caller's
            # Notification transaction if another worker won the insert.
            try:
                with db.begin_nested():
                    db.add(PushDelivery(notification_id=notification_id, device_id=device.id))
                    db.flush()
                created += 1
            except IntegrityError:
                pass
    return created


class PushTransport(Protocol):
    def send(self, messages: list[dict]) -> list[dict]: ...


class ExpoPushTransport:
    """Minimal Expo transport, injectable in drain tests."""
    OFFICIAL_URL = 'https://exp.host/--/api/v2/push/send'

    def __init__(self, *, url: str | None = None, timeout_seconds: float | None = None, client=None):
        settings = get_settings()
        self.url = url or self.OFFICIAL_URL
        if self.url != self.OFFICIAL_URL:
            raise ValueError('Expo URL must be the official HTTPS endpoint')
        self.timeout_seconds = timeout_seconds or settings.push_timeout_seconds
        self.client = client

    def send(self, messages: list[dict]) -> list[dict]:
        own_client = self.client is None
        client = self.client or httpx.Client(timeout=self.timeout_seconds)
        try:
            response = client.post(self.url, json=messages)
            response.raise_for_status()
            payload = response.json()
            return payload.get('data', []) if isinstance(payload, dict) else payload
        finally:
            if own_client:
                client.close()


def _claim_push_deliveries(db: Session, *, limit: int, owner: str, lease_seconds: int) -> list[int]:
    now = datetime.utcnow()
    candidates = db.execute(select(PushDelivery.id).where(
        ((PushDelivery.status.in_(['pending', 'retry'])) & (PushDelivery.next_attempt_at <= now)) |
        ((PushDelivery.status == 'processing') & (PushDelivery.lease_expires_at < now))
    ).order_by(PushDelivery.id).limit(limit)).scalars().all()
    claimed: list[int] = []
    for delivery_id in candidates:
        result = db.execute(update(PushDelivery).where(
            PushDelivery.id == delivery_id,
            ((PushDelivery.status.in_(['pending', 'retry'])) & (PushDelivery.next_attempt_at <= now)) |
            ((PushDelivery.status == 'processing') & (PushDelivery.lease_expires_at < now)),
        ).values(status='processing', lease_owner=owner, lease_expires_at=now + timedelta(seconds=lease_seconds)))
        if result.rowcount == 1:
            claimed.append(delivery_id)
    db.commit()
    return claimed


def _redact(value, secrets: set[str]):
    """Provider responses/errors are untrusted; never persist token material."""
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, '[REDACTED_PUSH_TOKEN]')
        return value[:2000]
    if isinstance(value, dict):
        return {str(key): ('[REDACTED_SECRET]' if any(word in str(key).lower() for word in ('token', 'secret', 'authorization')) else _redact(item, secrets)) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item, secrets) for item in value[:50]]
    return value


def drain_push_outbox(db: Session, *, transport: PushTransport | None = None, limit: int = 100) -> dict:
    """Attempt pending push rows. Disabled by default and safe to call explicitly."""
    settings = get_settings()
    if not settings.push_dispatch_enabled:
        return {'status': 'disabled', 'processed': 0, 'sent': 0, 'retry': 0, 'failed': 0}
    if limit < 1 or limit > settings.push_batch_size * 20:
        raise ValueError('limit fora do limite operacional')
    now = datetime.utcnow()
    owner = uuid.uuid4().hex
    claimed_ids = _claim_push_deliveries(db, limit=limit, owner=owner, lease_seconds=settings.push_lease_seconds)
    if not claimed_ids:
        return {'status': 'idle', 'processed': 0, 'sent': 0, 'retry': 0, 'failed': 0}
    deliveries = db.execute(select(PushDelivery).where(
        PushDelivery.id.in_(claimed_ids), PushDelivery.lease_owner == owner
    )).scalars().all()
    sender = transport or ExpoPushTransport()
    sent = retried = failed = canceled = 0
    for offset in range(0, len(deliveries), settings.push_batch_size):
        candidates = deliveries[offset:offset + settings.push_batch_size]
        batch = []
        for delivery in candidates:
            # This is only a local candidate number.  Do not persist it before
            # the provider result: the lease may be recovered by another
            # worker while the provider is in flight.
            attempt_number = delivery.attempts + 1
            if not delivery.device.active or not delivery.device.token:
                cas = db.execute(update(PushDelivery).where(
                    PushDelivery.id == delivery.id, PushDelivery.status == 'processing',
                    PushDelivery.lease_owner == owner, PushDelivery.lease_expires_at > datetime.utcnow(),
                ).values(status='canceled', last_error='device revoked or token unavailable', lease_owner=None, lease_expires_at=None))
                if cas.rowcount == 1:
                    canceled += 1
                    db.commit()
                continue
            batch.append((delivery, attempt_number, delivery.device.token))
        if not batch:
            continue
        messages = [{'to': token, 'title': delivery.notification.title, 'body': delivery.notification.message,
                     'data': {'notification_id': int(delivery.notification_id),
                              'concurso_id': int(delivery.notification.concurso_id) if delivery.notification.concurso_id is not None else None,
                              'notification_type': str(delivery.notification.notification_type)}}
                    for delivery, _, token in batch]
        token_secrets = {token for _, _, token in batch}
        try:
            results = sender.send(messages)
            if len(results) != len(batch):
                raise RuntimeError('provider retornou quantidade de resultados inconsistente')
        except Exception as exc:
            results = [{'status': 'error', 'message': _redact(str(exc), token_secrets)} for _ in batch]
        for (delivery, attempt_number, _), result in zip(batch, results):
            result = result if isinstance(result, dict) else {'status': 'error', 'message': 'provider result inválido'}
            status = str(result.get('status', '')).lower()
            error_code = str(result.get('details', {}).get('error', '')).lower() if isinstance(result.get('details'), dict) else ''
            permanent = status == 'error' and error_code == 'devicenotregistered'
            safe_result = _redact(result, token_secrets)
            if status == 'ok':
                desired_status, attempt_status, last_error = 'sent', 'sent', None
            elif permanent or attempt_number >= settings.push_max_attempts:
                desired_status, attempt_status = 'permanent_failed', 'permanent_failed'
                last_error = _redact(result.get('message') or result.get('details') or 'provider rejected push', token_secrets)
            else:
                desired_status, attempt_status = 'retry', 'retry'
                last_error = _redact(result.get('message') or result.get('details') or 'provider unavailable', token_secrets)
            values = {'status': desired_status, 'attempts': attempt_number, 'provider_message_id': result.get('id'),
                      'last_error': last_error, 'lease_owner': None, 'lease_expires_at': None}
            if desired_status == 'retry':
                values['next_attempt_at'] = now + timedelta(seconds=min(settings.push_retry_max_seconds, settings.push_retry_base_seconds * (2 ** (attempt_number - 1))))
            cas = db.execute(update(PushDelivery).where(
                PushDelivery.id == delivery.id, PushDelivery.status == 'processing',
                PushDelivery.lease_owner == owner, PushDelivery.lease_expires_at > datetime.utcnow(),
                PushDelivery.attempts == attempt_number - 1,
            ).values(**values))
            if cas.rowcount != 1:
                db.rollback()
                continue
            db.add(PushDeliveryAttempt(
                delivery_id=delivery.id, attempt_number=attempt_number, status=attempt_status,
                provider_message_id=result.get('id'),
                error_code=_redact((result.get('details') or {}).get('error'), token_secrets) if isinstance(result.get('details'), dict) else None,
                error_message=last_error, response_metadata=safe_result,
            ))
            if permanent:
                db.execute(update(PushDevice).where(PushDevice.id == delivery.device_id, PushDevice.active.is_(True)).values(
                    active=False, token=None, token_fingerprint=None, revoked_at=datetime.utcnow(), revoke_reason='DeviceNotRegistered'))
                db.execute(update(PushDelivery).where(
                    PushDelivery.device_id == delivery.device_id, PushDelivery.status.in_(['pending', 'retry', 'processing']),
                    PushDelivery.id != delivery.id,
                ).values(status='canceled', last_error='device token not registered', lease_owner=None, lease_expires_at=None))
            db.commit()
            if desired_status == 'sent': sent += 1
            elif desired_status == 'retry': retried += 1
            else: failed += 1
    return {'status': 'completed', 'processed': len(deliveries), 'sent': sent, 'retry': retried, 'failed': failed, 'canceled': canceled}
