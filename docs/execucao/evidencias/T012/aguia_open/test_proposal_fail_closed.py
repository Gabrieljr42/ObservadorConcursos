"""Executable local evidence for T012 #27; fixture-only, no network or DB writes."""
import hashlib
import json
from pathlib import Path

import pytest
from bs4 import UnicodeDammit

from app.tenderproof.batch30_edital_adapters import AguiaAdapter


ROOT = Path(__file__).parents[5] / "backend" / "tests" / "fixtures" / "tenderproof_batch30_edital"


def fixture(name: str) -> str:
    return UnicodeDammit((ROOT / name).read_bytes(), is_html=True).unicode_markup


def test_proposal_identity_and_fields_are_fixture_backed():
    adapter = AguiaAdapter()
    listing_url = "https://portal.institutoaguia.org.br/edital"
    page = adapter.parse_listing(fixture("aguia_open-0.html"), listing_url, 1000)
    candidate = next(item for item in page.candidates if item.external_id == "43")
    detail_url = "https://portal.institutoaguia.org.br/edital/ver/43"
    detail = fixture("aguia_open-cycle1-detail-a49b5d9ccc.html")
    adapter.confirm_identity(candidate, detail, detail_url)
    documents = adapter.documents(detail, candidate)
    opening = adapter.choose_document(documents)
    assert opening.kind == "edital"
    assert opening.url_requested.endswith("c382a2aac7251c1a31c0b734cd3540df.pdf")
    assert "Processo Seletivo 01/2025" in detail
    assert "05/12/2025" in detail and "16/12/2025" in detail
    assert "3.445,71" in detail


def test_wrong_identity_and_document_substitution_fail_closed():
    adapter = AguiaAdapter()
    candidate = adapter.parse_listing(fixture("aguia_open-0.html"), "https://portal.institutoaguia.org.br/edital", 1000).candidates[0]
    detail = fixture("aguia_open-cycle1-detail-a49b5d9ccc.html")
    with pytest.raises(ValueError):
        adapter.confirm_identity(candidate, detail, "https://portal.institutoaguia.org.br/edital/ver/42")
    with pytest.raises(ValueError):
        adapter.validate_document_url("https://cdn.institutoaguia.org.br/edital/1/42/c382a2aac7251c1a31c0b734cd3540df.pdf", candidate)
    with pytest.raises(ValueError):
        adapter.choose_document(adapter.documents(detail.replace("EDITAL DE ABERTURA", "EDITAL DE CONVOCAÇÃO"), candidate))


def test_envelope_is_proposal_only():
    envelope = json.loads((Path(__file__).parent / "proposal-envelope.json").read_text(encoding="utf-8"))
    assert envelope["state"] == "PROPOSTA_PRONTA"
    assert envelope["import_handoff"]["concurso_id"] is None
    assert envelope["import_handoff"]["apply"] is False
    assert envelope["import_handoff"]["reference_only"] is True
    assert envelope["artifact"]["sha256"] == hashlib.sha256((ROOT / "aguia_open-cycle1-detail-a49b5d9ccc.html").read_bytes()).hexdigest().upper()
