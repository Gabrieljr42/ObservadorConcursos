from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.tenderproof.ufu_selection_parser import (ARTIFACT_ID, DETAIL_URL, DOCUMENT_URL, EXPECTED_BYTES,
    EXPECTED_SHA256, TITLE, derive, parse, preflight)
from test_tenderproof_publication import env  # noqa: F401

HTML = Path("backend/tests/fixtures/tenderproof_batch30_institutional/ufu_selection-cycle1-detail-9088337b8d.html")
R3 = (Path(__file__).resolve().parents[2] / "docs/execucao/evidencias/T012/ufu_selection/live-envelope-ready-r3.json")
R10 = (Path(__file__).resolve().parents[2] / "docs/execucao/evidencias/T012/ufu_selection/reviewed-run-r10.json")


def test_ufu_current_detail_is_strongly_pinned_and_fail_closed():
    content = HTML.read_bytes()
    value = derive(content)
    assert hashlib.sha256(content).hexdigest() == EXPECTED_SHA256
    assert len(content) == EXPECTED_BYTES
    assert value["identity"]["source_id"] == 40
    assert value["identity"]["external_id"] == "1843"
    assert value["identity"]["edital_numero"] == "144/2026"
    assert value["document_urls"]
    assert value["pending_fields"] == ["taxa", "cargos", "remuneracao"]


@pytest.mark.parametrize("kwargs", [{"source": "other_open"}, {"external_id": "1842"}])
def test_identity_drift_rejected(kwargs):
    with pytest.raises(ValueError, match="identity drift"):
        parse(HTML.read_bytes(), **kwargs)


def test_truncation_hash_and_markers_rejected(monkeypatch):
    content = HTML.read_bytes()
    with pytest.raises(ValueError, match="artifact drift"):
        preflight(content[:-1])
    with pytest.raises(ValueError, match="required markers"):
        changed = content.replace("Universidade Federal de Uberlândia".encode(), b"Universidade Federal de X")
        monkeypatch.setattr("app.tenderproof.ufu_selection_parser.EXPECTED_SHA256", hashlib.sha256(changed).hexdigest())
        monkeypatch.setattr("app.tenderproof.ufu_selection_parser.EXPECTED_BYTES", len(changed))
        parse(changed)


def test_dispatch_rejects_artifact_pin_or_url_drift():
    from datetime import datetime, timezone
    from app.tenderproof.contracts import Artifact, DiscoveredCandidate, PageText
    from app.tenderproof.fields import extract_fields
    content = HTML.read_bytes()
    candidate = DiscoveredCandidate(candidate_id="ufu_selection-1843", external_id="1843",
                                    source="ufu_selection", title_observed=TITLE,
                                    detail_url_observed=DETAIL_URL,
                                    observed_at=datetime.now(timezone.utc))
    pages = [PageText(artifact_id=ARTIFACT_ID, page_number=1, text=content.decode("utf-8"))]
    bad = Artifact(artifact_id=ARTIFACT_ID, sha256="0" * 64, byte_len=EXPECTED_BYTES,
                   url_requested=DETAIL_URL, url_final=DETAIL_URL,
                   downloaded_at=datetime.now(timezone.utc), storage_path=str(HTML))
    extracted = extract_fields(candidate=candidate, artifact=bad, pages=pages)
    assert all(field.state.value == "failed" for field in extracted
               if field.field_name in {"titulo", "orgao", "edital_numero", "inscricao_inicio", "inscricao_fim"})


def test_sqlite_revalidate_remains_fail_closed_without_publication(env):
    """The source-specific reserve parser must not silently wire shared dispatch."""
    from sqlalchemy import func, select
    from app.models import ConcursoVersion, Source
    from app.tenderproof import publication as pub
    from app.tenderproof.fields import extract_fields
    from app.tenderproof.contracts import Artifact, DiscoveredCandidate, DocumentCandidate
    from app.tenderproof.publication_models import PublicationOutbox, PublicationProposal

    db, _, _, contest, run, store = env
    source = db.get(Source, contest.source_id)
    source.source_type = "ufu_selection"
    contest.external_id = "1843"
    contest.orgao = "Universidade Federal de Uberlândia"
    contest.edital_numero = "144/2026"
    contest.link_pagina = DETAIL_URL
    content = HTML.read_bytes()
    artifact = Artifact(artifact_id=ARTIFACT_ID, sha256=EXPECTED_SHA256,
                        byte_len=EXPECTED_BYTES, url_requested=DETAIL_URL,
                        url_final=DETAIL_URL, downloaded_at="2026-09-13T10:00:00Z")
    store.save_artifact_file(artifact, content)
    candidate = DiscoveredCandidate(candidate_id="ufu_selection-1843", external_id="1843",
                                    source="ufu_selection", title_observed=TITLE,
                                    detail_url_observed=DETAIL_URL, observed_at="2026-09-13T10:00:00Z")
    run.mode = "real"; run.is_synthetic_sample = False; run.source = "ufu_selection"
    run.candidates = [candidate]; run.selected_candidate_id = candidate.candidate_id
    run.document = DocumentCandidate(doc_id=ARTIFACT_ID, title="Edital de Processo",
                                     url_requested=DETAIL_URL, url_final=DETAIL_URL, kind="edital")
    run.artifact = artifact
    pages = []
    from app.tenderproof.contracts import PageText
    text = content.decode("utf-8")
    pages = [PageText(artifact_id=ARTIFACT_ID, page_number=1, text=text)]
    run.fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    eligible, blocked = pub._revalidate(run, contest, source, store)
    assert not eligible
    assert {"titulo", "orgao", "edital_numero", "inscricao_inicio", "inscricao_fim"}.issubset(set(blocked))
    assert db.scalar(select(func.count()).select_from(PublicationProposal)) == 0
    assert db.scalar(select(func.count()).select_from(ConcursoVersion)) == 0
    assert db.scalar(select(func.count()).select_from(PublicationOutbox)) == 0


def test_sqlite_revalidate_accepts_document_url_separately_from_detail_url(env):
    """The HTML artifact URL is distinct from the candidate detail URL."""
    from sqlalchemy import func, select
    from app.models import ConcursoVersion, Source
    from app.tenderproof import publication as pub
    from app.tenderproof.fields import extract_fields
    from app.tenderproof.contracts import Artifact, DiscoveredCandidate, DocumentCandidate, PageText
    from app.tenderproof.publication_models import PublicationOutbox, PublicationProposal

    db, _, _, contest, run, store = env
    source = db.get(Source, contest.source_id)
    source.source_type = "ufu_selection"
    contest.external_id = "1843"; contest.orgao = "Universidade Federal de Uberlândia"
    contest.edital_numero = "144/2026"; contest.link_pagina = DETAIL_URL
    content = HTML.read_bytes()
    artifact = Artifact(artifact_id=ARTIFACT_ID, sha256=EXPECTED_SHA256,
                        byte_len=EXPECTED_BYTES, url_requested=DOCUMENT_URL,
                        url_final=DOCUMENT_URL, downloaded_at="2026-09-13T10:00:00Z")
    store.save_artifact_file(artifact, content)
    candidate = DiscoveredCandidate(candidate_id="ufu_selection-1843", external_id="1843",
                                    source="ufu_selection", title_observed=TITLE,
                                    detail_url_observed=DETAIL_URL, observed_at="2026-09-13T10:00:00Z")
    run.mode = "real"; run.is_synthetic_sample = False; run.source = "ufu_selection"
    run.candidates = [candidate]; run.selected_candidate_id = candidate.candidate_id
    run.document = DocumentCandidate(doc_id=ARTIFACT_ID, title="Edital de Processo",
                                     url_requested=DOCUMENT_URL, url_final=DOCUMENT_URL, kind="edital")
    run.artifact = artifact
    pages = [PageText(artifact_id=ARTIFACT_ID, page_number=1, text=content.decode("utf-8"))]
    run.fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    eligible, blocked = pub._revalidate(run, contest, source, store)
    assert {"titulo", "orgao", "edital_numero", "inscricao_inicio", "inscricao_fim"}.issubset(eligible)
    assert not (set(blocked) & {"titulo", "orgao", "edital_numero", "inscricao_inicio", "inscricao_fim"})
    assert db.scalar(select(func.count()).select_from(PublicationProposal)) == 0
    assert db.scalar(select(func.count()).select_from(ConcursoVersion)) == 0
    assert db.scalar(select(func.count()).select_from(PublicationOutbox)) == 0


def test_reviewed_run_round_trip_and_drift_negative(env):
    """A complete reviewed envelope imports idempotently; HTML cannot publish as a PDF."""
    from sqlalchemy import func, select
    from app.models import ConcursoVersion, Source
    from app.tenderproof import publication as pub
    from app.tenderproof.publication_models import PublicationProposal
    from app.tenderproof.reviewed_run_import import import_reviewed_run

    db, _, user, contest, _, store = env
    content = HTML.read_bytes()
    parsed = derive(content)
    evidence = parsed["evidence"]
    fields = [
        {"field_name": "titulo", "value": parsed["identity"]["title"], "evidence": [evidence["titulo"]]},
        {"field_name": "orgao", "value": parsed["identity"]["orgao"], "evidence": [evidence["orgao"]]},
        {"field_name": "edital_numero", "value": "144/2026", "evidence": [evidence["edital_numero"]]},
        {"field_name": "inscricao_inicio", "value": parsed["inscricao_inicio"], "evidence": [evidence["inscricao"]]},
        {"field_name": "inscricao_fim", "value": parsed["inscricao_fim"], "evidence": [evidence["inscricao"]]},
    ]
    assert [field["field_name"] for field in fields] == [
        "titulo", "orgao", "edital_numero", "inscricao_inicio", "inscricao_fim"
    ]
    doc_url = parsed["document_urls"][0]
    payload = {
        "schema": "tenderproof.reviewed-run.v1", "source": "ufu_selection",
        "concurso_id": contest.id, "external_id": "1843", "title": TITLE,
        "detail_url": DETAIL_URL,
        "artifact": {"artifact_id": ARTIFACT_ID, "sha256": EXPECTED_SHA256,
                      "byte_len": EXPECTED_BYTES, "url_requested": doc_url,
                      "url_final": doc_url, "downloaded_at": "2026-09-13T10:00:00Z",
                      "content_base64": base64.b64encode(content).decode()},
        "fields": fields, "pending_fields": [], "reference_only": True,
        "owner_user_id": user.id, "observed_at": "2026-09-13T10:00:00Z",
    }
    imported = import_reviewed_run(payload, store, dry_run=False)
    assert imported["status"] == "imported"
    assert import_reviewed_run(payload, store, dry_run=False)["status"] == "idempotent"
    run = store.get_run(imported["run_id"])
    assert [field.field_name for field in run.fields] == [
        "titulo", "orgao", "edital_numero", "inscricao_inicio", "inscricao_fim"
    ]
    source = db.get(Source, contest.source_id)
    source.source_type = "ufu_selection"
    contest.external_id = "1843"; contest.orgao = parsed["identity"]["orgao"]
    contest.edital_numero = "144/2026"; contest.link_pagina = DETAIL_URL
    eligible, blocked = pub._revalidate(run, contest, source, store)
    assert not eligible
    assert {"titulo", "orgao", "edital_numero"}.issubset(set(blocked))
    assert db.scalar(select(func.count()).select_from(PublicationProposal)) == 0
    assert db.scalar(select(func.count()).select_from(ConcursoVersion)) == 0
    # Import rejects a stale/mutated artifact declaration before any write.
    stale = dict(payload); stale["artifact"] = dict(payload["artifact"]); stale["artifact"]["sha256"] = "0" * 64
    with pytest.raises(ValueError):
        import_reviewed_run(stale, store, dry_run=False)


def test_r3_contract_dry_run_exact_fields_and_owner_guards(env):
    from app.tenderproof.reviewed_run_import import ReviewedRun, import_reviewed_run

    payload = json.loads(R3.read_text(encoding="utf-8"))
    model = ReviewedRun.model_validate(payload)
    assert model.concurso_id is None
    assert model.owner_user_id == 1
    assert [field.field_name for field in model.fields] == [
        "titulo", "orgao", "edital_numero", "inscricao_inicio", "inscricao_fim"
    ]
    assert not any(name in payload for name in ("run_id", "source_id"))
    assert import_reviewed_run(payload, env[-1], dry_run=True)["status"] == "validated"
    with pytest.raises(ValueError):
        ReviewedRun.model_validate({**payload, "run_id": "synthetic"})
    with pytest.raises(ValueError):
        ReviewedRun.model_validate({**payload, "owner_user_id": 0})


def test_r4_run_serialization_and_proposal_binding():
    from app.tenderproof.reviewed_run_import import ReviewedRun, _run_id

    payload = json.loads(R3.read_text(encoding="utf-8"))
    model = ReviewedRun.model_validate(payload)
    first = _run_id(model)
    second = _run_id(ReviewedRun.model_validate(json.loads(json.dumps(payload, sort_keys=True))))
    assert first == second == "tp-reviewed-f3e9c58974f5f13419565aa22ded286d"
    proposal = {"target_concurso_id": None, "owner_user_id": 1, "source": "ufu_selection",
                "source_id": 40, "external_id": "1843", "run_id": first,
                "field_names": [f.field_name for f in model.fields]}
    assert proposal["field_names"] == ["titulo", "orgao", "edital_numero", "inscricao_inicio", "inscricao_fim"]
    assert proposal["run_id"] == first
    assert proposal["run_id"] != "tp-reviewed-00000000000000000000000000000000"


def test_r10_import_replay_and_real_revalidation_evidence(env):
    from sqlalchemy import select
    from app.models import Source
    from app.tenderproof import publication as pub
    from app.tenderproof.reviewed_run_import import ReviewedRun, import_reviewed_run

    payload = json.loads(R10.read_text(encoding="utf-8"))
    model = ReviewedRun.model_validate(payload)
    assert model.concurso_id is None
    assert [field.field_name for field in model.fields] == [
        "titulo", "orgao", "edital_numero", "inscricao_inicio", "inscricao_fim"
    ]
    db, _, _, contest, _, store = env
    first = import_reviewed_run(payload, store, dry_run=False)
    assert import_reviewed_run(payload, store, dry_run=False)["status"] == "idempotent"
    run = store.get_run(first["run_id"])
    source = db.get(Source, contest.source_id)
    source.source_type = "ufu_selection"
    contest.external_id = "1843"; contest.link_pagina = model.detail_url
    contest.orgao = "Universidade Federal de Uberlândia"; contest.edital_numero = "144/2026"
    eligible, blocked = pub._revalidate(run, contest, source, store)
    assert eligible, blocked
    assert set(blocked).issubset({"taxa", "cargos", "prova_data"})
    assert all(field.evidence[0].source_url == model.artifact.url_requested for field in run.fields)
    assert first["run_id"] != "tp-reviewed-f3e9c58974f5f13419565aa22ded286d"
    assert select is not None  # keep SQLAlchemy fixture import explicit for replay coverage
