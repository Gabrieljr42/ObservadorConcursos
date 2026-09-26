"""Reproducible, explicitly synthetic publication demonstration in disposable DB."""
from contextlib import contextmanager
from datetime import datetime
import json
import os
from pathlib import Path
import tempfile
from time import perf_counter

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.connectors.common import build_hash
from app.database import Base
from app.models import Concurso, ConcursoVersion, Source, User
from app.tenderproof import publication as pub
from app.tenderproof.mock_demo import MOCK_BASELINE, build_mock_driver
from app.tenderproof.service import TenderProofService
from app.tenderproof.store import TenderProofStore
from app.versioning import jsonable


def seed_isolated_baseline(db, *, canonical_snapshot, source_snapshot, provenance):
    """Seed an explicitly supplied snapshot, never derive truth from extraction.

    Caller retains the original snapshot and its origin/collected_at. A real
    source snapshot is not magically a prior catalog observation. Its kind must
    distinguish traditional_connector_observation / preserved_canonical_snapshot
    / synthetic_fixture. This utility only accepts a SQLite DB distinct from the
    configured application database; it never reads or writes the user's DB.
    """
    from app.database import engine as application_engine
    bind = db.get_bind()
    if bind.dialect.name != "sqlite" or str(bind.url) == str(application_engine.url):
        raise ValueError("TenderProof seed requires a separate disposable SQLite DB")
    if provenance.get("kind") not in {"traditional_connector_observation", "preserved_canonical_snapshot", "synthetic_fixture"}:
        raise ValueError("Explicit snapshot origin kind is required")
    if not provenance.get("origin") or not provenance.get("collected_at"):
        raise ValueError("Origin and observed time must be preserved")
    required = {"titulo", "banca", "external_id", "link_pagina", "content_hash"}
    if not required.issubset(canonical_snapshot):
        raise ValueError("Incomplete canonical snapshot")
    source = Source(**{k: source_snapshot[k] for k in ("name", "base_url", "source_type")})
    db.add(source)
    db.flush()
    allowed = {column.name for column in Concurso.__table__.columns} - {"id", "source_id"}
    values = {k: v for k, v in canonical_snapshot.items() if k in allowed}
    for name in ("prova_data", "edital_data", "inscricao_inicio", "inscricao_fim", "pdf_extracted_at", "fetched_at", "created_at", "updated_at"):
        if isinstance(values.get(name), str):
            values[name] = datetime.fromisoformat(values[name])
    contest = Concurso(source_id=source.id, **values)
    db.add(contest)
    db.commit()
    return contest, {"kind": provenance["kind"], "origin": provenance["origin"],
                     "collected_at": provenance["collected_at"], "snapshot_sha256": build_hash(jsonable(canonical_snapshot)),
                     "concurso_id": contest.id, "source_id": source.id}


@contextmanager
def _demo_environment(artifact_directory):
    updates = {"TENDERPROOF_PUBLICATION_ENABLED": "true", "TENDERPROOF_PUBLICATION_ALLOW_SYNTHETIC": "true",
               "TENDERPROOF_PUBLISHER_USER_IDS": "1", "TENDERPROOF_ARTIFACT_DIR": str(artifact_directory)}
    before = {k: os.environ.get(k) for k in updates}
    os.environ.update(updates)
    try:
        yield
    finally:
        for key, value in before.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def run_demo():
    """Runs all changes exclusively in an automatically deleted temporary DB."""
    with tempfile.TemporaryDirectory(prefix="tenderproof-publication-") as directory:
        root = Path(directory)
        with _demo_environment(root / "artifacts"):
            engine = create_engine(f"sqlite:///{root / 'disposable.sqlite'}")
            Base.metadata.create_all(engine)
            try:
                with Session(engine, expire_on_commit=False) as db:
                    user = User(id=1, name="Synthetic reviewer", email="synthetic@example.test", password_hash="not-a-login", is_active=True)
                    db.add(user)
                    raw = {"fixture": "TenderProof MOCK_BASELINE", "synthetic": True}
                    contest, receipt = seed_isolated_baseline(db, canonical_snapshot=MOCK_BASELINE | {
                        "banca": "IBGP", "external_id": "42", "link_pagina": "https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42",
                        "raw_data": raw, "content_hash": build_hash(raw)},
                        source_snapshot={"name": "IBGP synthetic", "base_url": "https://novo.ibgpconcursos.com.br", "source_type": "ibgp_open"},
                        provenance={"kind": "synthetic_fixture", "origin": "app.tenderproof.mock_demo.MOCK_BASELINE", "collected_at": "2026-03-01T12:00:00Z"})
                    store = TenderProofStore()
                    service = TenderProofService(store)
                    latencies = {}
                    start = perf_counter()
                    run = service.start_discovery(build_mock_driver(), mode="mock", is_synthetic=True, owner_user_id=user.id)
                    run = service.select_and_process(run.run_id, "cand-42", build_mock_driver(), mode="mock")
                    latencies["synthetic_acquisition_extraction_ms"] = round((perf_counter() - start) * 1000, 2)
                    def reviewed_apply(observation):
                        p = pub.create_proposal(db, run=observation, concurso_id=contest.id, user=user, store=store)
                        p = pub.approve_proposal(db, proposal_id=p["id"], proposal_hash=p["proposal_hash"], fields=["inscricao_fim"], user=user, store=store)
                        return pub.apply_proposal(db, proposal_id=p["id"], proposal_hash=p["proposal_hash"], user=user, store=store)
                    start = perf_counter()
                    first = reviewed_apply(run)
                    repeated = pub.apply_proposal(db, proposal_id=first["id"], proposal_hash=first["proposal_hash"], user=user, store=store)
                    latencies["review_apply_and_retry_ms"] = round((perf_counter() - start) * 1000, 2)
                    reprocessed = run.model_copy(deep=True)
                    reprocessed.run_id += "-reprocess"
                    reprocessed.session_id = "mock-metadata-only"
                    unchanged = reviewed_apply(reprocessed)
                    versions_before_rollback = db.scalar(select(func.count()).select_from(ConcursoVersion))
                    rollback = pub.rollback_proposal(db, proposal_id=first["id"], reason="Synthetic demonstration rollback", user=user)
                    expected = {"titulo": "Concurso Prefeitura Municipal de Exemplo MG cod 42", "orgao": "Prefeitura Municipal De Exemplo",
                                "edital_numero": "01/2026", "inscricao_inicio": "2026-03-10", "inscricao_fim": "2026-04-20"}
                    fields = run.field_map()
                    valid_evidence = sum(len(first["evidences"][k]["items"]) for k in first["eligible_fields"])
                    presented_evidence = sum(len(first["evidences"][k]["items"]) for k in expected)
                    return {"label": "Cenário sintético controlado; nenhum recurso Solari", "baseline": receipt,
                            "first_apply": first, "duplicate_same_version": first["version_id"] == repeated["version_id"],
                            "reprocess_state": unchanged["state"], "versions_before_rollback": versions_before_rollback,
                            "rollback": rollback, "latency_ms": latencies,
                            "metrics": {"correct_fields": {"numerator": sum(fields[k].value == v for k, v in expected.items()), "denominator": len(expected)},
                                        "filled_fields": {"numerator": sum(fields[k].value is not None for k in expected), "denominator": len(expected)},
                                        "valid_evidences_in_evaluated_fields": {"numerator": valid_evidence, "denominator": presented_evidence},
                                        "false_changes_on_unchanged_comparisons": {"numerator": int(unchanged["state"] != "no_change"), "denominator": 1},
                                        "human_review_steps": 2},
                            "cost": {"resources_created": 0, "estimated_usd": 0, "provider_confirmed_usd": None},
                            "limitations": ["Demonstração pequena e sintética; sem alegação estatística", "SQLite descartável; PostgreSQL pendente", "Não utiliza baseline real nem prova Solari"]}
            finally:
                engine.dispose()
