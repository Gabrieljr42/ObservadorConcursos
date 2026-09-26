"""Fail-closed review of EPL 52 retifications; fixture-only, no network/DB writes."""
import hashlib
import json
from pathlib import Path

from app.tenderproof.batch60_recovered_adapters import EPLAdapter


ROOT = Path(__file__).parents[5]
FIXTURES = ROOT / "backend" / "tests" / "fixtures" / "tenderproof_batch60_blockers"
EVIDENCE = Path(__file__).parent


def preserved_candidate():
    adapter = EPLAdapter()
    listing = (FIXTURES / "epl_open-cycle1-listing-dc7d20e042.html").read_text(encoding="utf-8")
    detail = (FIXTURES / "epl_open-cycle1-detail-2e60516108.html").read_text(encoding="utf-8")
    page = adapter.parse_listing(listing, adapter.listing_urls[0])
    candidate = next(item for item in page.candidates if item.external_id == "52")
    return adapter, candidate, detail


def test_three_pending_documents_are_exact_process_bound_publications():
    decisions = json.loads((EVIDENCE / "document-review-decisions-r1.json").read_text(encoding="utf-8"))
    adapter, candidate, detail = preserved_candidate()
    docs = {doc.url_requested: doc for doc in adapter.documents(detail, candidate)}
    rows = decisions["decisions"]
    assert len(rows) == 3
    assert [row["retificacao_number"] for row in rows] == [10, 9, 5]
    assert len({row["url_requested"] for row in rows}) == 3
    for row in rows:
        assert row["url_requested"] in docs
        assert docs[row["url_requested"]].kind == "retificacao"
        adapter.validate_document_url(row["url_requested"], candidate)
        assert row["doc_id"] == docs[row["url_requested"]].doc_id
        assert row["decision"] == "BLOCKED_MISSING_BYTES"


def test_no_unproved_content_or_dedupe_decision_can_pass():
    decisions = json.loads((EVIDENCE / "document-review-decisions-r1.json").read_text(encoding="utf-8"))
    assert decisions["local_inventory"]["retification_bytes_preserved"] is False
    assert decisions["local_inventory"]["acquisition"]["attempted"] is True
    assert decisions["local_inventory"]["acquisition"]["attempts_per_url"] == 1
    assert decisions["local_inventory"]["acquisition"]["result"] == "BLOCKED_ENVIRONMENT_NETWORK"
    for row in decisions["decisions"]:
        assert row["content"]["sha256"] is None
        assert row["content"]["byte_len"] is None
        assert row["content"]["pages"] is None
        assert row["content"]["material_change"].startswith("UNDETERMINED")
        assert row["dedupe"]["content_hash_comparable"] is False
    assert decisions["gate"] == {
        "proposal": False,
        "approve": False,
        "apply": False,
        "next": decisions["gate"]["next"],
    }


def test_inventory_contains_only_opening_artifact_hash():
    decisions = json.loads((EVIDENCE / "document-review-decisions-r1.json").read_text(encoding="utf-8"))
    artifacts = ROOT / "backend" / ".tenderproof" / "r60rec" / "artifacts"
    opening = artifacts / "art-508d44c1f6-b040f8c3ff74845185dfdfec2096b70da84a7ee10c54d228afe7b82ed205805f.pdf"
    assert opening.exists()
    assert hashlib.sha256(opening.read_bytes()).hexdigest() == decisions["local_inventory"]["opening_artifact_only"]["sha256"]
    urls = [row["url_requested"] for row in decisions["decisions"]]
    searchable = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in (ROOT / "backend" / ".tenderproof" / "r60rec").rglob("*.json"))
    assert all(url not in searchable for url in urls)
