from copy import deepcopy
from datetime import datetime

import pytest
from sqlalchemy import select

from app.models import ConcursoVersion
from app.services import CrawlService
from test_tenderproof_amendment import _proposal
from test_tenderproof_publication import env


pytestmark = pytest.mark.usefixtures("legacy_crawler_enabled")


def test_legacy_crawl_keeps_applied_dates_ledger_and_history(env, monkeypatch):
    db, user, contest, run, store, queue, case, proposal = _proposal(env)
    from app.tenderproof import amendment

    amendment.approve_proposal(
        db, proposal_id=proposal["id"], proposal_hash=proposal["proposal_hash"],
        user=user, fields=["inscricao_inicio", "inscricao_fim", "prova_data"],
        queue=queue, store=store,
    )
    amendment.apply_proposal(
        db, proposal_id=proposal["id"], proposal_hash=proposal["proposal_hash"],
        user=user, queue=queue, store=store,
    )
    db.refresh(contest)
    original_ledger = deepcopy(contest.raw_data["tenderproof"])
    contest.raw_data = {**contest.raw_data, "history": [{"event": "before-legacy"}]}
    db.commit()

    # CrawlService receives a connector item, not a version row.  Build the
    # same payload shape as a legacy connector while carrying a stale date.
    from app.models import Concurso
    item = {
        column.name: getattr(contest, column.name)
        for column in Concurso.__table__.columns
        if column.name not in {"id", "source_id", "created_at", "updated_at"}
    }
    item["inscricao_fim"] = datetime.fromisoformat("2026-09-04T23:59:00-03:00")
    item["raw_data"] = {
        "source_payload": "fresh legacy observation",
        "history": [{"event": "after-legacy"}],
        "tenderproof": {"amendments": [{"stale": True}]},
    }

    class Connector:
        def crawl(self):
            return [item]

    monkeypatch.setattr("app.services.get_connector", lambda *args, **kwargs: Connector())
    before_versions = db.scalar(select(ConcursoVersion).where(ConcursoVersion.concurso_id == contest.id)).id
    first = CrawlService(db).crawl_source(contest.source_id)
    assert first["unchanged"] == 1
    assert db.scalar(select(ConcursoVersion).where(ConcursoVersion.concurso_id == contest.id)).id == before_versions
    db.refresh(contest)
    assert contest.inscricao_fim.isoformat().startswith("2026-09-11T10:00:00")
    assert contest.raw_data["source_payload"] == "fresh legacy observation"
    assert contest.raw_data["tenderproof"]["amendments"] == original_ledger["amendments"]
    assert contest.raw_data["history"] == [{"event": "before-legacy"}, {"event": "after-legacy"}]
    observations = contest.raw_data["tenderproof"]["legacy_observations"]
    assert observations[0]["protected_fields"]["inscricao_fim"]["observed"].startswith("2026-09-04")
    assert observations[0]["review_required"] is True

    second = CrawlService(db).crawl_source(contest.source_id)
    db.refresh(contest)
    assert second["unchanged"] == 1
    assert len(contest.raw_data["tenderproof"]["legacy_observations"]) == 1


def test_legacy_crawl_still_records_unprotected_field_changes(env, monkeypatch):
    db, user, contest, run, store, queue, case, proposal = _proposal(env)
    from app.tenderproof import amendment

    amendment.approve_proposal(
        db, proposal_id=proposal["id"], proposal_hash=proposal["proposal_hash"],
        user=user, fields=["inscricao_inicio", "inscricao_fim", "prova_data"],
        queue=queue, store=store,
    )
    amendment.apply_proposal(
        db, proposal_id=proposal["id"], proposal_hash=proposal["proposal_hash"],
        user=user, queue=queue, store=store,
    )
    from app.models import Concurso
    item = {
        column.name: getattr(contest, column.name)
        for column in Concurso.__table__.columns
        if column.name not in {"id", "source_id", "created_at", "updated_at"}
    }
    item["status"] = "Encerrado"

    class Connector:
        def crawl(self):
            return [item]

    monkeypatch.setattr("app.services.get_connector", lambda *args, **kwargs: Connector())
    result = CrawlService(db).crawl_source(contest.source_id)
    assert result["updated"] == 1
    db.refresh(contest)
    assert contest.status == "Encerrado"
    version = db.scalar(
        select(ConcursoVersion).where(ConcursoVersion.concurso_id == contest.id)
        .order_by(ConcursoVersion.id.desc())
    )
    assert version.change_type == "status_changed"
    assert "status" in version.changed_fields
