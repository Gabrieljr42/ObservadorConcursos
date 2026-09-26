from sqlalchemy import func, select
from fastapi import HTTPException

from app.models import ConcursoVersion, Notification
from app.tenderproof import publication as pub
from app.tenderproof.publication_models import PublicationOutbox, PublicationProposal, ensure_publication_schema
from test_tenderproof_publication import env  # noqa: F401


def test_pending_proposal_rejection_is_owner_bound_idempotent_and_side_effect_free(env):
    db, _, user, contest, run, store = env
    ensure_publication_schema(db.get_bind())
    proposal = pub.create_proposal(db, run=run, concurso_id=contest.id, user=user, store=store)
    pid = proposal["id"]
    before = {
        "versions": db.scalar(select(func.count()).select_from(ConcursoVersion)),
        "outbox": db.scalar(select(func.count()).select_from(PublicationOutbox)),
        "notifications": db.scalar(select(func.count()).select_from(Notification)),
    }

    rejected = pub.reject_proposal(db, proposal_id=pid, reason="CPCON R6 superseded", user=user)
    assert rejected["state"] == "rejected"
    assert rejected["rejection_reason"] == "CPCON R6 superseded"
    assert rejected["rejected_by"] == user.id
    assert db.scalar(select(PublicationProposal).where(PublicationProposal.id == pid)).state == "rejected"
    assert {"versions": db.scalar(select(func.count()).select_from(ConcursoVersion)),
            "outbox": db.scalar(select(func.count()).select_from(PublicationOutbox)),
            "notifications": db.scalar(select(func.count()).select_from(Notification))} == before

    replay = pub.reject_proposal(db, proposal_id=pid, reason="different reason ignored", user=user)
    assert replay["state"] == "rejected" and replay["rejection_reason"] == "CPCON R6 superseded"


def test_rejection_rejects_foreign_and_approved_states(env):
    db, _, user, contest, run, store = env
    ensure_publication_schema(db.get_bind())
    proposal = pub.create_proposal(db, run=run, concurso_id=contest.id, user=user, store=store)
    other = db.query(type(user)).filter(type(user).id == 2).one()
    try:
        pub.reject_proposal(db, proposal_id=proposal["id"], reason="foreign", user=other)
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        raise AssertionError("cross-owner rejection must not disclose proposal")
    row = db.scalar(select(PublicationProposal).where(PublicationProposal.id == proposal["id"]))
    row.state = "approved"
    db.commit()
    try:
        pub.reject_proposal(db, proposal_id=row.id, reason="too late", user=user)
    except HTTPException as exc:
        assert exc.status_code == 409
    else:
        raise AssertionError("approved proposal must not be rejected")
