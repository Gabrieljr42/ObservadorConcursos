import json
from pathlib import Path

from app.tenderproof.batch60_major_adapters import BATCH60_MAJOR_ADAPTERS
from app.tenderproof.contracts import TenderProofRun


ROOT = Path(__file__).resolve().parents[5]
EVIDENCE = ROOT / "docs/execucao/evidencias/T012/avalia_open"


def test_reviewed_envelope_is_fail_closed_and_model_valid():
    envelope = json.loads((EVIDENCE / "reviewed-run-proposta.json").read_text(encoding="utf-8"))
    assert envelope["status"] == "PROPOSTA_PRONTA"
    run = TenderProofRun.model_validate(envelope["reviewed_run"])
    assert run.source == "avalia_open"
    assert run.selected_candidate_id == "avalia_open-631"
    assert {field.field_name for field in run.fields} == {"titulo", "orgao"}
    assert all(field.state.value == "supported" for field in run.fields)
    assert envelope["dispatch"]["authorized"] is False


def test_avalia_adapter_replays_preserved_selection_and_document():
    adapter = next(item for item in BATCH60_MAJOR_ADAPTERS if item.source == "avalia_open")
    fixtures = ROOT / "backend/tests/fixtures/tenderproof_batch60_major"
    listing = (fixtures / "avalia.html").read_text(encoding="utf-8")
    detail = (fixtures / "avalia631.html").read_text(encoding="utf-8")
    page = adapter.parse_listing(listing, adapter.listing_urls[0], 2000)
    candidate = next(item for item in page.candidates if item.external_id == "631")
    adapter.confirm_identity(candidate, detail, candidate.detail_url_observed)
    selected = adapter.choose_document(adapter.documents(detail, candidate))
    assert candidate.candidate_id == "avalia_open-631"
    assert selected.doc_id == "avalia_open-doc-1fe85bfc6222054c"
    assert selected.kind == "edital"
