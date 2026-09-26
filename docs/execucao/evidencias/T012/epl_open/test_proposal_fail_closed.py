"""Evidence for T012 #21 EPL; fixture/artifact-only, no network or DB writes."""
import hashlib
import json
from pathlib import Path

import pytest

from app.tenderproof.batch60_recovered_adapters import EPLAdapter
from app.tenderproof.reviewed_run_import import ReviewedRun


ROOT = Path(__file__).parents[5]
FIXTURES = ROOT / "backend" / "tests" / "fixtures" / "tenderproof_batch60_blockers"
ARTIFACT = ROOT / "backend" / ".tenderproof" / "r60rec" / "artifacts" / "art-8c5dbef058-b040f8c3ff74845185dfdfec2096b70da84a7ee10c54d228afe7b82ed205805f.pdf"
EVIDENCE = Path(__file__).parent


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def preserved():
    adapter = EPLAdapter()
    listing = fixture("epl_open-cycle1-listing-dc7d20e042.html")
    detail = fixture("epl_open-cycle1-detail-2e60516108.html")
    page = adapter.parse_listing(listing, adapter.listing_urls[0])
    candidate = next(item for item in page.candidates if item.external_id == "52")
    return adapter, listing, candidate, detail


def test_proposal_identity_document_and_proven_facts():
    adapter, listing, candidate, detail = preserved()
    adapter.confirm_identity(candidate, detail, candidate.detail_url_observed)
    documents = adapter.documents(detail, candidate)
    opening = adapter.choose_document(documents)
    assert opening.kind == "edital"
    assert "/EPL_CONCURSOS/00052/PUBLICA" in opening.url_requested
    assert "FUNDAÇÃO HOSPITALAR SANTA TEREZINHA" in detail
    assert "Inscrições de 23/10/2023" in detail
    processing = ROOT / "backend" / ".tenderproof" / "r60rec" / "processing"
    output_path = next(
        path
        for path in processing.rglob("output.json")
        if json.loads(path.read_text(encoding="utf-8")).get("input_sha256")
        == "b040f8c3ff74845185dfdfec2096b70da84a7ee10c54d228afe7b82ed205805f"
    )
    assert "R$ 2.377,90" in output_path.read_text(encoding="utf-8")
    assert hashlib.sha256(ARTIFACT.read_bytes()).hexdigest() == "b040f8c3ff74845185dfdfec2096b70da84a7ee10c54d228afe7b82ed205805f"
    assert len(page := adapter.parse_listing(listing, adapter.listing_urls[0]).candidates) >= 5


def test_identity_process_and_query_substitution_fail_closed():
    adapter, _, candidate, detail = preserved()
    with pytest.raises(ValueError, match="título"):
        adapter.confirm_identity(candidate.model_copy(update={"title_observed": "Município inexistente"}), detail, candidate.detail_url_observed)
    opening = adapter.choose_document(adapter.documents(detail, candidate))
    with pytest.raises(ValueError, match="processo"):
        adapter.validate_document_url(opening.url_requested.replace("/00052/", "/99999/"), candidate)
    with pytest.raises(ValueError):
        adapter.confirm_identity(candidate, detail, candidate.detail_url_observed + "?id=2")


def test_duplicate_cycles_and_ambiguous_document_do_not_import():
    adapter, _, candidate, detail = preserved()
    opening = adapter.choose_document(adapter.documents(detail, candidate))
    duplicate = opening.model_copy(update={"doc_id": "duplicate", "url_requested": opening.url_requested.replace(".pdf", "-other.pdf")})
    with pytest.raises(ValueError):
        adapter.choose_document([opening, duplicate])
    envelope = json.loads((EVIDENCE / "proposal-envelope.json").read_text(encoding="utf-8"))
    receipt = json.loads((EVIDENCE / "proposal-receipt.json").read_text(encoding="utf-8"))
    assert envelope["state"] == receipt["state"] == "PROPOSTA_PRONTA"
    assert envelope["candidate"]["external_id"] == receipt["candidate_external_id"] == "52"
    assert envelope["import_handoff"]["apply"] is False
    assert envelope["import_handoff"]["concurso_id"] is None
    assert receipt["catalogue_mutated"] is False


def test_content_receipt_and_reviewed_handoff_are_replayable_but_unallocated():
    receipt = json.loads((EVIDENCE / "content-receipt.json").read_text(encoding="utf-8"))
    handoff = json.loads((EVIDENCE / "reviewed-run-handoff.json").read_text(encoding="utf-8"))
    content = ARTIFACT.read_bytes()
    assert len(content) == receipt["byte_len"] == 784614
    assert hashlib.sha256(content).hexdigest() == receipt["sha256"]
    reviewed = handoff["reviewed_run"]
    assert handoff["source"]["source_number"] == 21
    assert reviewed["concurso_id"] is None
    assert reviewed["reference_only"] is True
    assert all(field["evidence"] and all(item["page_number"] and item["snippet"] for item in field["evidence"])
               for field in reviewed["fields"])
    with pytest.raises(ValueError, match="concurso_id"):
        ReviewedRun.model_validate(reviewed)
    rejected = {**reviewed, "concurso_id": 1, "reference_only": False}
    with pytest.raises(ValueError):
        ReviewedRun.model_validate(rejected)
