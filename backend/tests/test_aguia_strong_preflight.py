from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from app.tenderproof.aguia_balsamo import EXPECTED_BYTES, EXPECTED_PAGES, EXPECTED_SHA256, derive, parse, preflight
from test_tenderproof_publication import env  # noqa: F401

PDF = Path("docs/execucao/evidencias/T012/aguia_open/artifacts/aguia-43.pdf")


def test_strong_preflight_and_semantic_revalidation_are_pinned():
    content = PDF.read_bytes()
    first = derive(content)
    second = derive(content)
    assert first == second
    assert hashlib.sha256(content).hexdigest() == EXPECTED_SHA256
    assert len(content) == EXPECTED_BYTES
    assert first["identity"]["source_id"] == 27
    assert first["identity"]["external_id"] == "43"
    assert first["identity"]["edital_numero"] == "01/2025"
    assert first["taxa_inscricao"] == "65.00"
    assert len(first["cargos"]) == 4
    assert preflight(content)["pages"] == EXPECTED_PAGES


@pytest.mark.parametrize("kwargs", [{"source": "other_open"}, {"external_id": "44"}])
def test_identity_drift_is_rejected(kwargs):
    with pytest.raises(ValueError, match="identity drift"):
        parse(PDF.read_bytes(), **kwargs)


def test_truncated_sha_and_u_fffd_are_rejected(monkeypatch):
    import app.tenderproof.aguia_balsamo as parser

    content = PDF.read_bytes()
    with pytest.raises(ValueError, match="artifact drift"):
        preflight(content[:-1])
    fake = SimpleNamespace(pages=[SimpleNamespace(extract_text=lambda: "\ufffd")] * EXPECTED_PAGES)
    monkeypatch.setattr(parser, "PdfReader", lambda value: fake)
    with pytest.raises(ValueError, match=r"U\+FFFD"):
        parser._pages(content)


def test_revalidate_sqlite_stays_fail_closed_without_side_effects(env):
    """The reserve is not wired into shared dispatch; revalidation must not publish it."""
    from app.models import ConcursoVersion, Source
    from app.tenderproof import publication as pub
    from app.tenderproof.contracts import Artifact, DiscoveredCandidate, DocumentCandidate
    from app.tenderproof.pdf_text import extract_pages
    from app.tenderproof.publication_models import PublicationOutbox, PublicationProposal

    db, _, user, contest, run, store = env
    source = db.get(Source, contest.source_id)
    source.source_type = "aguia_open"
    contest.external_id = "43"
    contest.orgao = "Prefeitura Municipal de Bálsamo"
    contest.edital_numero = "01/2025"
    contest.link_pagina = "https://portal.institutoaguia.org.br/edital/ver/43"
    content = PDF.read_bytes()
    artifact = Artifact(artifact_id="aguia-open-43-pdf-r2", sha256=EXPECTED_SHA256,
                        byte_len=EXPECTED_BYTES, url_requested="https://cdn.institutoaguia.org.br/edital/1/43/c382a2aac7251c1a31c0b734cd3540df.pdf",
                        url_final="https://cdn.institutoaguia.org.br/edital/1/43/c382a2aac7251c1a31c0b734cd3540df.pdf",
                        downloaded_at="2026-09-13T10:00:00Z")
    store.save_artifact_file(artifact, content)
    candidate = DiscoveredCandidate(candidate_id="aguia_open-43", external_id="43", source="aguia_open",
                                    title_observed="Prefeitura Municipal de Bálsamo - Processo Seletivo 01/2025",
                                    detail_url_observed=contest.link_pagina, observed_at="2026-09-13T10:00:00Z")
    pages, *_ = extract_pages(content, artifact_id=artifact.artifact_id)
    run.mode = "real"; run.is_synthetic_sample = False; run.source = "aguia_open"
    run.candidates = [candidate]; run.selected_candidate_id = candidate.candidate_id
    run.document = DocumentCandidate(doc_id=artifact.artifact_id, title="Edital de Abertura - Processo Seletivo 01/2025",
                                     url_requested=artifact.url_requested, url_final=artifact.url_final, kind="edital")
    run.artifact = artifact
    # Deliberately preserve the current generic extraction path; the source
    # parser is a reservation preflight and is not a shared-dispatch mutation.
    from app.tenderproof.fields import extract_fields
    run.fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    with pytest.raises(HTTPException):
        pub._revalidate(run, contest, source, store)
    assert db.scalar(select(func.count()).select_from(PublicationProposal)) == 0
    assert db.scalar(select(func.count()).select_from(ConcursoVersion)) == 0
    assert db.scalar(select(func.count()).select_from(PublicationOutbox)) == 0
