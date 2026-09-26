"""Real offline `_revalidate` gate for the pinned Avança SP PDF."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[5]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "tests"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_tenderproof_publication import env  # noqa: E402,F401
from app.models import Source  # noqa: E402
from app.tenderproof import publication as pub  # noqa: E402
from app.tenderproof.contracts import Artifact, DiscoveredCandidate, DocumentCandidate, TenderProofRun  # noqa: E402
from app.tenderproof.pdf_text import extract_pages  # noqa: E402
from app.tenderproof import reviewed_run_import  # noqa: E402

import avancasp_parser as parser  # noqa: E402

PDF = ROOT / "docs/execucao/evidencias/T012/avancasp_open/avancasp-open-edital-272.pdf"
PDF_URL = "https://anexos-r2.selecao.net.br/uploads/301/concursos/272/anexos/aa3e927b-faeb-414e-ae6c-28800427a051.pdf"
DETAIL_URL = "https://avancasp.selecao.net.br/informacoes/272/"


def _run_for(env_tuple):
    db, _, user, contest, _, store = env_tuple
    content = PDF.read_bytes()
    parser.preflight(content)
    source = db.get(Source, contest.source_id)
    source.source_type = parser.SOURCE
    source.name = "Avança SP"
    contest.external_id = parser.EXTERNAL_ID
    contest.titulo = "Concurso Público - 01/2026 - PREFEITURA MUNICIPAL DE CABREÚVA"
    contest.orgao = "Prefeitura Municipal De Cabreúva"
    contest.edital_numero = parser.EXPECTED_EDITAL
    contest.link_pagina = DETAIL_URL
    contest.link_edital = PDF_URL
    artifact = Artifact(
        artifact_id="avancasp-open-edital-272-pdf-b0ba7e15",
        sha256=hashlib.sha256(content).hexdigest(), byte_len=len(content),
        url_requested=PDF_URL, url_final=PDF_URL, content_type="application/pdf",
        downloaded_at=datetime.now(timezone.utc),
    )
    store.save_artifact_file(artifact, content)
    candidate = DiscoveredCandidate(
        candidate_id="avancasp_open-272",
        title_observed="CONCURSO PÚBLICO 01/2026 - PREFEITURA MUNICIPAL DE CABREÚVA",
        detail_url_observed=DETAIL_URL, external_id=parser.EXTERNAL_ID,
        observed_at=datetime.now(timezone.utc), source=parser.SOURCE,
    )
    pages, *_ = extract_pages(content, artifact_id=artifact.artifact_id)
    fields = parser.extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    run = TenderProofRun(
        run_id="t012-avancasp-272-strong-preflight", owner_user_id=user.id, source=parser.SOURCE,
        mode="real", is_synthetic_sample=False, execution_status="completed",
        validation_status="valid", candidates=[candidate], selected_candidate_id=candidate.candidate_id,
        document=DocumentCandidate(doc_id="avancasp-open-doc-8a30699a26344fa0",
                                   title="EDITAL COMPLETO 04/09/2026", kind="edital",
                                   url_requested=PDF_URL, url_final=PDF_URL),
        artifact=artifact, fields=fields,
    )
    return db, source, contest, store, run, candidate, pages


def test_pinned_parser_and_real_revalidate_pass(env, monkeypatch):
    db, source, contest, store, run, candidate, pages = _run_for(env)
    monkeypatch.setattr(pub, "extract_fields", parser.extract_fields)
    monkeypatch.setattr(pub, "document_identity_ids",
                        lambda adapter, checked_candidate, checked_pages:
                        parser.document_identity_ids(checked_candidate, checked_pages))
    eligible, blocked = pub._revalidate(run, contest, source, store)
    assert {"titulo", "orgao", "edital_numero", "inscricao_inicio", "inscricao_fim", "prova_data", "cargos"}.issubset(eligible)
    assert not (set(eligible) & set(blocked))
    assert parser.document_identity_ids(candidate, pages) == {"272"}
    assert eligible["orgao"] == contest.orgao
    assert eligible["edital_numero"] == "01/2026"


def test_parser_fails_closed_on_drift_and_wrong_identity():
    content = PDF.read_bytes()
    with pytest.raises(ValueError, match="artifact drift"):
        parser.preflight(content[:-1])
    with pytest.raises(ValueError, match="artifact drift"):
        parser.preflight(content + b"x")


def test_live_envelope_round_trip_and_html_stale_drift_negatives(env, monkeypatch):
    db, source, contest, store, _, _, _ = _run_for(env)
    payload = json.loads((Path(__file__).with_name("live-envelope-ready-r1.json")).read_text(encoding="utf-8"))
    payload["artifact"]["content_path"] = str(PDF.resolve())
    model = reviewed_run_import.ReviewedRun.model_validate(payload)
    content = PDF.read_bytes()
    run = reviewed_run_import.build_run(model, content)
    store.save_artifact_file(run.artifact, content)
    monkeypatch.setattr(pub, "extract_fields", parser.extract_fields)
    monkeypatch.setattr(pub, "document_identity_ids",
                        lambda adapter, checked_candidate, checked_pages:
                        parser.document_identity_ids(checked_candidate, checked_pages))
    eligible, blocked = pub._revalidate(run, contest, source, store)
    assert {"titulo", "orgao", "edital_numero", "inscricao_inicio", "inscricao_fim", "prova_data", "cargos"}.issubset(eligible)
    assert "cargos" not in blocked

    html_run = run.model_copy(deep=True)
    html_run.artifact.url_requested = DETAIL_URL
    html_run.artifact.url_final = DETAIL_URL
    html_run.document.url_requested = DETAIL_URL
    html_run.document.url_final = DETAIL_URL
    with pytest.raises(HTTPException):
        pub._revalidate(html_run, contest, source, store)

    contest.external_id = "273"
    with pytest.raises(HTTPException):
        pub._revalidate(run, contest, source, store)
    contest.external_id = "272"

    drift_run = run.model_copy(deep=True)
    drift_run.artifact.sha256 = "0" * 64
    with pytest.raises(HTTPException):
        pub._revalidate(drift_run, contest, source, store)
