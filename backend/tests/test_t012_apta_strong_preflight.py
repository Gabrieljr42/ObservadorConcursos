import hashlib
from datetime import date
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.tenderproof.apta_aragarcas_parser import EXPECTED_SHA256, EXPECTED_BYTE_LEN, extract_identity, preflight
from app.tenderproof.contracts import Artifact, DiscoveredCandidate, DocumentCandidate, PageText
from app.tenderproof.fields import extract_fields
from app.tenderproof.pdf_text import extract_pages
from app.tenderproof import publication as pub
from app.models import Source
from test_tenderproof_publication import env  # noqa: F401


ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "backend/.tenderproof/r60rec/artifacts/art-18bef50e17-db9c6d26a285102ae051761500d893c81616b07b69a086ec5353307d5975d79c.pdf"


def test_apta_current_identity_is_pinned_and_fail_closed():
    content = PDF.read_bytes()
    assert len(content) == EXPECTED_BYTE_LEN
    result = preflight(content, as_of=date(2026, 9, 13))
    assert result["current"] is True and result["edital_numero"] == "01/2026"
    with pytest.raises(ValueError, match="SHA/byte drift"):
        preflight(content[:-1], as_of=date(2026, 9, 13))
    assert preflight(content, as_of=date(2026, 9, 21))["current"] is False


def test_apta_identity_field_is_evidence_bound_and_page_drift_fails():
    content = PDF.read_bytes()
    from pypdf import PdfReader
    from io import BytesIO
    pages = [PageText(artifact_id="art-18bef50e17", page_number=i + 1, text=p.extract_text() or "")
             for i, p in enumerate(PdfReader(BytesIO(content)).pages)]
    artifact = Artifact(artifact_id="art-18bef50e17", sha256=EXPECTED_SHA256, byte_len=len(content),
                        url_requested="https://cdn-arquivo.concursos.srv.br/APTA/00708/PUBLICACOES/Edital_Completo_2026_07_31_09_13_43.pdf",
                        url_final="https://cdn-arquivo.concursos.srv.br/APTA/00708/PUBLICACOES/Edital_Completo_2026_07_31_09_13_43.pdf",
                        downloaded_at="2026-09-08T14:13:29.857615Z")
    fields = extract_identity(artifact, pages, source="apta_open", external_id="708", as_of=date(2026, 9, 13))
    assert [field.field_name for field in fields] == ["titulo", "orgao", "edital_numero"]
    assert all(field.state.value == "supported" for field in fields)
    assert fields[-1].value == "01/2026"
    assert extract_identity(artifact, pages, source="apta_open", external_id="708", as_of=date(2026, 9, 21))[0].state.value == "failed"
    pages[1] = pages[1].model_copy(update={"truncated": True})
    assert extract_identity(artifact, pages, source="apta_open", external_id="708", as_of=date(2026, 9, 13))[0].state.value == "failed"


def test_apta_real_revalidate_accepts_pinned_orgao_edital_fallback(env):
    db, _, user, contest, run, store = env
    source = db.get(Source, contest.source_id)
    source.source_type = "apta_open"
    contest.external_id = "708"
    contest.orgao = "Câmara Municipal De Aragarças"
    contest.edital_numero = "01/2026"
    contest.link_pagina = "https://www.aptaconcursos.com.br/concursos/publicacoes/Câmara+Municipal+de+Aragarças+/708"
    content = PDF.read_bytes()
    document_url = "https://cdn-arquivo.concursos.srv.br/APTA/00708/PUBLICACOES/Edital_Completo_2026_07_31_09_13_43.pdf"
    artifact = Artifact(artifact_id="art-18bef50e17", sha256=EXPECTED_SHA256, byte_len=len(content),
                        url_requested=document_url, url_final=document_url, downloaded_at="2026-09-08T14:13:29.857615Z")
    store.save_artifact_file(artifact, content)
    candidate = DiscoveredCandidate(candidate_id="apta_open-708", external_id="708", source="apta_open",
        title_observed="Câmara Municipal de Aragarças", detail_url_observed=contest.link_pagina,
        observed_at="2026-09-08T14:13:28.861827Z")
    pages, *_ = extract_pages(content, artifact_id=artifact.artifact_id)
    run.mode = "real"; run.is_synthetic_sample = False; run.source = "apta_open"
    run.candidates = [candidate]; run.selected_candidate_id = candidate.candidate_id
    run.document = DocumentCandidate(doc_id="apta_open-doc-84249009acfafaab", title="Edital de Abertura de Inscrições",
                                     url_requested=document_url, url_final=document_url, kind="edital")
    run.artifact = artifact; run.fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    eligible, blocked = pub._revalidate(run, contest, source, store)
    assert eligible["orgao"] == contest.orgao
    assert eligible["edital_numero"] == "01/2026"
    assert "edital_numero" not in blocked
