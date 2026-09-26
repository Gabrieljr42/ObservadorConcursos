from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from app.models import ConcursoVersion, Source
from app.tenderproof import publication as pub
from app.tenderproof.contracts import Artifact, DiscoveredCandidate, DocumentCandidate
from app.tenderproof.fields import extract_fields
from app.tenderproof.pdf_text import extract_pages
from app.tenderproof.publication_models import PublicationOutbox, PublicationProposal
from app.tenderproof.shdias_hortolandia import EXPECTED_BYTES, EXPECTED_SHA256
from test_tenderproof_publication import env  # noqa: F401


ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "docs/execucao/evidencias/T012/shdias_open/artifacts/01_Edital_Completo_2026_07_23_08_20_13.pdf"
DOCUMENT_URL = "https://cdn-arquivo.concursos.srv.br/SHDIAS/00308/PUBLICACOES/01_Edital_Completo_2026_07_23_08_20_13.pdf"
DETAIL_URL = "https://www.shdias.com.br/concursos/publicacoes/MTEw/MzA4"


def _run(env):
    db, _, user, contest, run, store = env
    source = db.get(Source, contest.source_id)
    source.source_type = "shdias_open"
    contest.external_id = "MTEw/MzA4"
    contest.orgao = "Município de Hortolândia"
    contest.edital_numero = "001/2026"
    contest.link_pagina = DETAIL_URL
    content = PDF.read_bytes()
    artifact = Artifact(artifact_id="shdias-open-00308-edital-2026", sha256=EXPECTED_SHA256.lower(),
        byte_len=EXPECTED_BYTES, url_requested=DOCUMENT_URL, url_final=DOCUMENT_URL,
        downloaded_at="2026-09-08T14:07:32.165650Z")
    store.save_artifact_file(artifact, content)
    candidate = DiscoveredCandidate(candidate_id="shdias_open-MTEw/MzA4", external_id="MTEw/MzA4",
        source="shdias_open", title_observed="CONCURSO PÚBLICO CPMH 001/2026 - Guarda",
        detail_url_observed=DETAIL_URL, observed_at="2026-09-08T14:07:32.165650Z")
    pages, *_ = extract_pages(content, artifact_id=artifact.artifact_id)
    run.mode = "real"; run.is_synthetic_sample = False; run.source = "shdias_open"
    run.candidates = [candidate]; run.selected_candidate_id = candidate.candidate_id
    run.document = DocumentCandidate(doc_id=artifact.artifact_id, title="Edital Completo com Programa de Prova",
                                     url_requested=DOCUMENT_URL, url_final=DOCUMENT_URL, kind="edital")
    run.artifact = artifact
    run.fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    return db, source, contest, run, store, user


def test_shdias_dispatch_revalidates_real_pdf_without_publication(env):
    db, source, contest, run, store, _ = _run(env)
    assert "taxa" in pub.PUBLISHABLE
    eligible, blocked = pub._revalidate(run, contest, source, store)
    assert "titulo" not in blocked and "orgao" not in blocked and "edital_numero" not in blocked
    assert eligible["orgao"] == "Município de Hortolândia"
    assert eligible["edital_numero"] == "001/2026"
    assert eligible["taxa"] == "63.25"
    assert len(eligible["cargos"]) == 2 and eligible["prova_data"] == "2026-09-27"
    assert db.scalar(select(func.count()).select_from(PublicationProposal)) == 0
    assert db.scalar(select(func.count()).select_from(ConcursoVersion)) == 0
    assert db.scalar(select(func.count()).select_from(PublicationOutbox)) == 0


@pytest.mark.parametrize("drift", [
    "source", "external_id", "sha256",
])
def test_shdias_dispatch_parser_rejects_identity_or_sha_drift(env, drift):
    db, source, contest, run, store, _ = _run(env)
    if drift == "source":
        run.source = "other_open"
    elif drift == "external_id":
        run.candidates[0].external_id = "other"
    else:
        run.artifact.sha256 = "0" * 64
    with pytest.raises(HTTPException):
        pub._revalidate(run, contest, source, store)
    assert db.scalar(select(func.count()).select_from(PublicationProposal)) == 0


def test_shdias_dispatch_rejects_replacement_character(monkeypatch, env):
    import app.tenderproof.shdias_hortolandia as parser
    from types import SimpleNamespace
    fake_pages = [SimpleNamespace(extract_text=lambda: "\ufffd")] * parser.EXPECTED_PAGES
    monkeypatch.setattr(parser, "PdfReader", lambda value: SimpleNamespace(pages=fake_pages))
    with pytest.raises(ValueError, match=r"U\+FFFD"):
        parser.preflight(PDF.read_bytes())
