"""Opt-in delivery of reviewed publications to internal app notifications."""
import logging
import os

from celery import shared_task
from sqlalchemy import select, update

from app.database import SessionLocal
from app.models import User
from app.tenderproof.publication import drain_outbox
from app.tenderproof.publication_models import PublicationOutbox, PublicationProposal

logger = logging.getLogger(__name__)


@shared_task(name="app.tenderproof.notifications.deliver", ignore_result=True)
def deliver_internal_notifications():
    if any(os.getenv(key, "false").lower() != "true" for key in (
        "TENDERPROOF_INTERNAL_NOTIFICATIONS_ENABLED", "TENDERPROOF_PUBLICATION_ENABLED"
    )):
        return {"status": "disabled", "delivered": 0}
    owners = [int(value.strip()) for value in os.getenv("TENDERPROOF_PUBLISHER_USER_IDS", "").split(",")
              if value.strip().isdigit()]
    with SessionLocal() as db:
        pending = db.execute(
            select(PublicationOutbox.id, PublicationProposal.owner_user_id)
            .join(PublicationProposal, PublicationProposal.id == PublicationOutbox.proposal_id)
            .join(User, User.id == PublicationProposal.owner_user_id)
            .where(PublicationOutbox.state == "pending", User.is_active.is_(True),
                   User.id.in_(owners))
            .order_by(PublicationOutbox.attempts, PublicationOutbox.id).limit(100)
        ).all()
    delivered = failed = created = 0
    for outbox_id, owner_id in pending:
        with SessionLocal() as db:
            try:
                user = db.get(User, owner_id)
                result = drain_outbox(db, outbox_id=outbox_id, user=user)
                delivered += result["state"] == "delivered"
                created += result["created"]
            except Exception:
                db.rollback()
                db.execute(update(PublicationOutbox).where(
                    PublicationOutbox.id == outbox_id, PublicationOutbox.state == "pending"
                ).values(attempts=PublicationOutbox.attempts + 1))
                db.commit()
                failed += 1
                logger.exception("Internal notification delivery failed for event %s", outbox_id)
    return {"status": "completed", "delivered": delivered, "failed": failed, "created": created}
