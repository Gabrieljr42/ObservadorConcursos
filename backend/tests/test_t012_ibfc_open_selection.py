from pathlib import Path

import pytest

from app.tenderproof.batch30_own_adapters import IBFCAdapter


FIX = Path(__file__).parent / "fixtures" / "tenderproof_batch30_own"


def test_ibfc_preserved_selection_is_identity_valid_but_primary_document_fail_closed():
    adapter = IBFCAdapter()
    listing = (FIX / "ibfc_open-cycle1-listing-822e0b4c54.html").read_text(encoding="utf-8")
    detail = (FIX / "ibfc_open-cycle1-detail-59a096579c.html").read_text(encoding="utf-8")
    candidates = adapter.parse_listing(listing, "https://concursos.ibfc.org.br/index/1/").candidates
    candidate = next(c for c in candidates if c.external_id == "496")

    adapter.confirm_identity(candidate, detail, candidate.detail_url_observed)
    documents = adapter.documents(detail, candidate)
    assert any("edital-01.2026-ibge-retificado-19.08.pdf" in d.url_requested for d in documents)
    with pytest.raises(ValueError, match="nenhum edital principal inequívoco"):
        adapter.choose_document(documents)


def test_ibfc_preserved_selection_rejects_document_from_other_external_id():
    adapter = IBFCAdapter()
    listing = (FIX / "ibfc_open-cycle1-listing-822e0b4c54.html").read_text(encoding="utf-8")
    candidate = next(c for c in adapter.parse_listing(listing, "https://concursos.ibfc.org.br/index/1/").candidates if c.external_id == "496")
    with pytest.raises(ValueError):
        adapter.validate_document_url(
            "https://anexos-r2.selecao.net.br/uploads/747/concursos/495/anexos/foreign.pdf",
            candidate,
        )
