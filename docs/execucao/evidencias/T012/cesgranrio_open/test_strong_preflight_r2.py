from pathlib import Path

import pytest
from fastapi import HTTPException

from app.models import Source
from app.tenderproof import publication as pub
from app.tenderproof.contracts import Artifact, DiscoveredCandidate, DocumentCandidate
from app.tenderproof.fields import extract_fields
from app.tenderproof.pdf_text import extract_pages
from test_tenderproof_publication import env  # noqa: F401
from cesgranrio27_parser_r2 import extract_identity_fields


ROOT = Path(__file__).resolve().parents[5]
PDF = ROOT / "backend/.tenderproof/batch60-major-cesgranrio-live-20260908/artifacts/art-262c2f6ba7-e053d5c0f3f81b0fa93eb47912fe34398c7dd7d4a9be759ad43c96054d7ef39f.pdf"
PDF_URL = "https://concursos.cesgranrio.org.br/media/gpoweb-prd-hibrido3/eventos/27/conteudos/9454893c-7962-4e4f-8be8-fb3c79821d8f.pdf"
DETAIL_URL = "https://concursos.cesgranrio.org.br/api/PortalEventoConteudos/publico/27"
SHA = "e053d5c0f3f81b0fa93eb47912fe34398c7dd7d4a9be759ad43c96054d7ef39f"


def test_cesgranrio_strong_binding_revalidate_real_bytes_in_ephemeral_sqlite(env, monkeypatch):
    db, _, user, contest, run, store = env
    content = PDF.read_bytes()
    artifact = Artifact(
        artifact_id="art-262c2f6ba7",
        sha256=SHA,
        byte_len=len(content),
        url_requested=PDF_URL,
        url_final=PDF_URL,
        content_type="application/pdf",
        downloaded_at="2026-09-08T14:19:29.055463Z",
        storage_path=PDF.name,
    )
    pages, *_ = extract_pages(content, artifact_id=artifact.artifact_id)
    assert len(pages) == 60
    candidate = DiscoveredCandidate(
        candidate_id="cesgranrio_open-27",
        external_id="27",
        title_observed="EDITAL Nº 01/2026 - Concurso Público SEMA/MT",
        detail_url_observed=DETAIL_URL,
        observed_at="2026-09-08T14:19:29Z",
        source="cesgranrio_open",
    )
    source = db.get(Source, contest.source_id)
    source.source_type = "cesgranrio_open"
    contest.external_id = "27"
    contest.link_pagina = DETAIL_URL
    contest.link_edital = PDF_URL
    contest.orgao = "Secretaria de Estado de Meio Ambiente do Estado de Mato Grosso - SEMA/MT"
    contest.edital_numero = "01/2026"
    run.source = "cesgranrio_open"
    run.owner_user_id = user.id
    run.candidates = [candidate]
    run.selected_candidate_id = candidate.candidate_id
    run.document = DocumentCandidate(
        doc_id="cesgranrio_open-ef63456bb29b61f912",
        title="EDITAL Nº 01/2026",
        url_requested=PDF_URL,
        url_final=PDF_URL,
        kind="edital",
    )
    run.artifact = artifact
    generic_fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    pinned = {field.field_name: field for field in extract_identity_fields(artifact=artifact, pages=pages)}
    run.fields = [pinned.get(field.field_name, field) for field in generic_fields]
    original_extract = pub.extract_fields
    monkeypatch.setattr(
        pub,
        "extract_fields",
        lambda *, candidate, artifact, pages: [
            pinned.get(field.field_name, field)
            for field in original_extract(candidate=candidate, artifact=artifact, pages=pages)
        ],
    )
    store.save_artifact_file(artifact, content)
    fresh = {field.field_name: field for field in run.fields}
    assert fresh["orgao"].state.value == "supported"
    assert fresh["edital_numero"].state.value == "supported"
    with pytest.raises(HTTPException, match="processamento documental falhou") as exc:
        pub._revalidate(run, contest, source, store)
    assert exc.value.status_code == 422
    assert contest.id is not None


def test_cesgranrio27_parser_fails_closed_on_binding_drift():
    content = PDF.read_bytes()
    artifact = Artifact(
        artifact_id="art-262c2f6ba7", sha256=SHA, byte_len=len(content),
        url_requested=PDF_URL, url_final=PDF_URL,
        downloaded_at="2026-09-08T14:19:29.055463Z",
    )
    pages, *_ = extract_pages(content, artifact_id=artifact.artifact_id)
    assert extract_identity_fields(artifact=artifact, pages=pages)
    assert extract_identity_fields(artifact=artifact, pages=pages, source="other_open") is None
    assert extract_identity_fields(artifact=artifact, pages=pages, external_id="28") is None
    assert extract_identity_fields(artifact=artifact.model_copy(update={"sha256": "0" * 64}), pages=pages) is None
    assert extract_identity_fields(artifact=artifact.model_copy(update={"byte_len": len(content) - 1}), pages=pages) is None
