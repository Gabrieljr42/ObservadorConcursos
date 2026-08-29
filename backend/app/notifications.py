from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Alert, Concurso, ConcursoVersion, Notification

SIGNIFICANT_CHANGE_TYPES = {
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
    if concurso.inscricao_fim is None:
        return True
    now = datetime.now(timezone.utc)
    end = concurso.inscricao_fim
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    return end >= now


def _text_haystack(concurso: Concurso) -> str:
    raw_data = concurso.raw_data or {}
    cargo_candidates = raw_data.get('cargo_candidates') or []
    if not isinstance(cargo_candidates, list):
        cargo_candidates = []

    return ' '.join([
        concurso.titulo or '',
        concurso.orgao or '',
        concurso.cargo or '',
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
    return version.change_type in SIGNIFICANT_CHANGE_TYPES


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
            created += 1
    return created
