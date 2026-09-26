"""Fixture-only SHDIAS proposal checks; never performs HTTP or catalog writes."""
from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest
from pypdf import PdfReader

from app.tenderproof.batch60_recovered_adapters import SHDIASAdapter


ROOT = Path(__file__).parents[5]
FIXTURES = ROOT / "backend" / "tests" / "fixtures" / "tenderproof_batch60_blockers"
LISTING_URL = "https://www.shdias.com.br/concursos/index/?status=andamento&busca="
DETAIL_URL = "https://www.shdias.com.br/concursos/publicacoes/MTEw/MzA4"


def _candidate_and_detail():
    adapter = SHDIASAdapter()
    listing = (FIXTURES / "shdias_open-cycle1-listing-d24cf41921.html").read_text(encoding="utf-8")
    page = adapter.parse_listing(listing, LISTING_URL)
    candidate = next(c for c in page.candidates if c.external_id == "MTEw/MzA4")
    detail = (FIXTURES / "shdias_open-cycle1-detail-e633962f88.html").read_text(encoding="utf-8")
    return adapter, candidate, detail


def test_real_selection_identity_and_opening_notice_are_bound_to_process():
    adapter, candidate, detail = _candidate_and_detail()
    assert candidate.detail_url_observed == DETAIL_URL
    assert adapter.process_id(candidate) == "00308"
    adapter.confirm_identity(candidate, detail, DETAIL_URL)
    docs = adapter.documents(detail, candidate)
    opening = next(d for d in docs if d.kind == "edital")
    assert opening.url_requested == (
        "https://cdn-arquivo.concursos.srv.br/SHDIAS/00308/PUBLICACOES/"
        "01_Edital_Completo_2026_07_23_08_20_13.pdf"
    )
    assert "HORTOL" in detail.upper()
    assert "Previs" in detail and "09/2026" in detail
    assert "Guarda Municipal" in detail


def test_wrong_process_or_document_is_rejected():
    adapter, candidate, detail = _candidate_and_detail()
    with pytest.raises(ValueError):
        adapter.confirm_identity(candidate, detail, "https://www.shdias.com.br/concursos/publicacoes/OTQ=/MzA5")
    with pytest.raises(ValueError):
        adapter.validate_document_url(
            "https://cdn-arquivo.concursos.srv.br/SHDIAS/00309/PUBLICACOES/01_Edital.pdf",
            candidate,
        )
    with pytest.raises(ValueError):
        adapter.candidate_from_url(
            "https://www.shdias.com.br/concursos/publicacoes/MTEw/MzA4x",
            "CONCURSO PÚBLICO MUNICÍPIO DE HORTOLÂNDIA-SP",
        )


def test_envelope_receipt_and_hash_are_reviewed_reference_only():
    envelope = json.loads((Path(__file__).parent / "proposal-envelope.json").read_text(encoding="utf-8"))
    receipt = json.loads((Path(__file__).parent / "proposal-receipt.json").read_text(encoding="utf-8"))
    handoff = json.loads((Path(__file__).parent / "reviewed-run-handoff.json").read_text(encoding="utf-8"))
    content = json.loads((Path(__file__).parent / "content-receipt.json").read_text(encoding="utf-8"))
    detail_path = FIXTURES / "shdias_open-cycle1-detail-e633962f88.html"
    pdf_path = Path(__file__).parent / "artifacts" / "01_Edital_Completo_2026_07_23_08_20_13.pdf"
    digest = sha256(detail_path.read_bytes()).hexdigest().upper()
    pdf_digest = sha256(pdf_path.read_bytes()).hexdigest().upper()
    assert digest == envelope["artifact"]["sha256"] == handoff["provenance"]["detail_sha256"]
    assert envelope["state"] == receipt["state"] == handoff["state"] == "PROPOSTA_PRONTA"
    assert envelope["candidate"]["external_id"] == receipt["candidate_external_id"] == "MTEw/MzA4"
    assert envelope["source"] == receipt["source"] == handoff["source"]["source_id"] == "shdias_open"
    assert envelope["import_handoff"]["reference_only"] is True
    assert envelope["import_handoff"]["apply"] is False
    assert envelope["provenance"]["catalogue_mutated"] is False
    assert content["document"]["sha256"] == pdf_digest == envelope["documents"]["opening_notice"]["sha256"]
    assert content["document"]["bytes"] == pdf_path.stat().st_size == 697485
    assert content["document"]["pages"] == 44
    assert handoff["provenance"]["opening_pdf_sha256"] == pdf_digest


def test_promoted_field_snippets_are_literal_and_point_to_real_pages_and_paths():
    manifest = json.loads((Path(__file__).parent / "field-evidence.json").read_text(encoding="utf-8"))
    pdf_path = Path(__file__).parent / "artifacts" / "01_Edital_Completo_2026_07_23_08_20_13.pdf"
    digest = sha256(pdf_path.read_bytes()).hexdigest().upper()
    pages = [(page.extract_text() or "") for page in PdfReader(str(pdf_path)).pages]
    assert manifest["artifact_sha256"] == digest
    assert manifest["fields"]
    for field in manifest["fields"]:
        assert field["evidence"]
        for evidence in field["evidence"]:
            assert evidence["document_sha256"] == digest
            assert evidence["json_path"]
            assert "\ufffd" not in evidence["snippet"]
            page = evidence["page_number"]
            assert 1 <= page <= len(pages)
            assert evidence["snippet"] in pages[page - 1]
    paths = {e["json_path"] for f in manifest["fields"] for e in f["evidence"]}
    assert {"titulo", "taxa_inscricao", "prova_data", "cargos[0]", "cargos[1]", "cargos.vagas_total"} <= paths
