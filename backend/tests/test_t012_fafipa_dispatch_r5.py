from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from app.models import ConcursoVersion, Source
from app.tenderproof import publication as pub
from app.tenderproof.contracts import Artifact, DiscoveredCandidate, DocumentCandidate
from app.tenderproof.fields import extract_fields
from app.tenderproof.processing import extract_pages_isolated
from app.tenderproof.publication_models import PublicationOutbox, PublicationProposal
from app.tenderproof.fafipa_t012_r4 import SHA256, BYTE_LEN
from test_tenderproof_publication import env  # noqa: F401


ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "docs/execucao/evidencias/T012/fafipa_open/artifacts/fafipa-4208-edital.pdf"
DETAIL_URL = "https://concursos.fundacaofafipa.org.br/informacoes/4208/"
DOCUMENT_URL = "https://anexos-r2.selecao.net.br/uploads/281/concursos/4208/anexos/7c626742-c657-4e0c-b36c-7d59336ee942.pdf"


def _run(env):
    db, _, user, contest, run, store = env
    source = db.get(Source, contest.source_id)
    source.source_type = "fafipa_open"
    contest.external_id = "4208"; contest.orgao = "Município de Mirador - PR"; contest.edital_numero = "001/2026"
    contest.link_pagina = DETAIL_URL
    content = PDF.read_bytes()
    artifact = Artifact(artifact_id="fafipa-4208-edital", sha256=SHA256, byte_len=BYTE_LEN,
        url_requested=DOCUMENT_URL, url_final=DOCUMENT_URL, downloaded_at="2026-09-13T00:00:00Z")
    store.save_artifact_file(artifact, content)
    candidate = DiscoveredCandidate(candidate_id="fafipa_open-4208", external_id="4208", source="fafipa_open",
        title_observed="Mirador", detail_url_observed=DETAIL_URL, observed_at="2026-09-13T00:00:00Z")
    pages, *_ = extract_pages_isolated(content, artifact_id=artifact.artifact_id, owner_id="t012-fafipa", max_pages=75,
                                       max_bytes=20 * 1024 * 1024, capacity_wait_s=15, reuse_completed=False)
    run.mode = "real"; run.is_synthetic_sample = False; run.source = "fafipa_open"
    run.candidates = [candidate]; run.selected_candidate_id = candidate.candidate_id
    run.document = DocumentCandidate(doc_id=artifact.artifact_id, title="Edital de Abertura", url_requested=DOCUMENT_URL,
                                     url_final=DOCUMENT_URL, kind="edital")
    run.artifact = artifact
    extracted = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    run.fields = [field for field in extracted if field.field_name in (
        "titulo", "orgao", "edital_numero", "inscricao_inicio", "inscricao_fim", "prova_data", "cargos")]
    return db, source, contest, run, store


def test_fafipa_dispatch_revalidates_identity_without_publication(env):
    db, source, contest, run, store = _run(env)
    eligible, blocked = pub._revalidate(run, contest, source, store)
    assert eligible["orgao"] == "Município de Mirador - PR"
    assert eligible["edital_numero"] == "001/2026"
    assert eligible["titulo"] == "Concurso Público do Município de Mirador - PR"
    assert eligible["cargos"][0]["nome"] == "Auxiliar Administrativo"
    assert "orgao" not in blocked and "edital_numero" not in blocked
    assert db.scalar(select(func.count()).select_from(PublicationProposal)) == 0
    assert db.scalar(select(func.count()).select_from(ConcursoVersion)) == 0
    assert db.scalar(select(func.count()).select_from(PublicationOutbox)) == 0


@pytest.mark.parametrize("drift", ["source", "external_id", "sha256"])
def test_fafipa_dispatch_rejects_identity_or_sha_drift(env, drift):
    db, source, contest, run, store = _run(env)
    if drift == "source":
        run.source = "other_open"
    elif drift == "external_id":
        run.candidates[0].external_id = "other"
    else:
        run.artifact.sha256 = "0" * 64
    with pytest.raises(HTTPException):
        pub._revalidate(run, contest, source, store)
    assert db.scalar(select(func.count()).select_from(PublicationProposal)) == 0
