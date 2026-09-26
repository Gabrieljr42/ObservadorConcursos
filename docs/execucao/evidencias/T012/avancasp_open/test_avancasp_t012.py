"""Offline, source-specific gate for the Avança SP proposal.

This test intentionally exercises preserved captures only.  It does not call
the website, the pilot API, a database, or the catalogue.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest
from bs4 import UnicodeDammit

ROOT = Path(__file__).resolve().parents[5]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.tenderproof.reviewed_run_import import ReviewedRun, import_reviewed_run  # noqa: E402
from app.tenderproof.source_adapters import get_source_adapter  # noqa: E402
from app.tenderproof.store import TenderProofStore  # noqa: E402


FIXTURES = BACKEND / "tests" / "fixtures" / "tenderproof_pilot"
ENVELOPE = Path(__file__).with_name("reviewed-envelope.json")
DETAIL = FIXTURES / "avancasp_open-detail.html"
LISTING = FIXTURES / "avancasp_open-listing.html"
DETAIL_URL = "https://avancasp.selecao.net.br/informacoes/272/"
PDF_URL = (
    "https://anexos-r2.selecao.net.br/uploads/301/concursos/272/anexos/"
    """aa3e927b-faeb-414e-ae6c-28800427a051.pdf"""
)


def _html(path: Path) -> str:
    return UnicodeDammit(path.read_bytes(), is_html=True).unicode_markup


def test_reviewed_envelope_is_closed_and_dry_run_validates() -> None:
    payload = json.loads(ENVELOPE.read_text(encoding="utf-8"))
    model = ReviewedRun.model_validate(payload)
    assert model.source == "avancasp_open"
    assert model.external_id == "272"
    assert model.detail_url == DETAIL_URL
    assert model.reference_only is True
    assert model.pending_fields == []
    assert [field.field_name for field in model.fields] == ["cargos"]
    assert len(model.fields[0].value) == 14

    raw = DETAIL.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == model.artifact.sha256
    assert len(raw) == model.artifact.byte_len
    # The import contract resolves content_path from the backend working
    # directory; make the fixture absolute in this offline test only.
    payload["artifact"]["content_path"] = str(DETAIL)
    result = import_reviewed_run(payload, TenderProofStore(), dry_run=True)
    assert result["status"] == "validated"
    assert result["fields"] == ["cargos"]


def test_identity_document_and_no_duplicate_candidate_are_proven() -> None:
    adapter = get_source_adapter("avancasp_open")
    listing_page = adapter.parse_listing(_html(LISTING), "https://avancasp.selecao.net.br/index/abertos/", 1000)
    ids = [candidate.external_id for candidate in listing_page.candidates]
    assert len(ids) == len(set(ids))
    candidate = next(item for item in listing_page.candidates if item.external_id == "272")
    assert candidate.detail_url_observed == DETAIL_URL
    assert "vestibular" not in candidate.title_observed.casefold()
    assert "bolsa" not in candidate.title_observed.casefold()

    detail = _html(DETAIL)
    adapter.confirm_identity(candidate, detail, DETAIL_URL)
    documents = adapter.documents(detail, candidate)
    assert len(documents) == 1
    assert documents[0].url_requested == PDF_URL
    adapter.validate_document_url(PDF_URL, candidate)


@pytest.mark.parametrize(
    "bad_url",
    [
        "https://evil.test/uploads/301/concursos/272/anexos/edital.pdf",
        "https://anexos-r2.selecao.net.br/uploads/999/concursos/272/anexos/edital.pdf",
        "https://anexos-r2.selecao.net.br/uploads/301/concursos/999/anexos/edital.pdf",
        "https://127.0.0.1/uploads/301/concursos/272/anexos/edital.pdf",
    ],
)
def test_document_identity_and_destination_fail_closed(bad_url: str) -> None:
    adapter = get_source_adapter("avancasp_open")
    listing_page = adapter.parse_listing(_html(LISTING), "https://avancasp.selecao.net.br/index/abertos/", 1000)
    candidate = next(item for item in listing_page.candidates if item.external_id == "272")
    with pytest.raises(Exception):
        adapter.validate_document_url(bad_url, candidate)


def test_detail_identity_mismatch_fails_closed() -> None:
    adapter = get_source_adapter("avancasp_open")
    listing_page = adapter.parse_listing(_html(LISTING), "https://avancasp.selecao.net.br/index/abertos/", 1000)
    candidate = next(item for item in listing_page.candidates if item.external_id == "272")
    with pytest.raises(ValueError):
        adapter.confirm_identity(candidate, _html(DETAIL), "https://avancasp.selecao.net.br/informacoes/273/")
    with pytest.raises(ValueError):
        adapter.confirm_identity(candidate.model_copy(update={"external_id": "273"}), _html(DETAIL), DETAIL_URL)
