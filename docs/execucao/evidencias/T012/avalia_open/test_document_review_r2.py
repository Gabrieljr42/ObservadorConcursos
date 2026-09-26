import hashlib
import json
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent


def test_bounded_receipts_match_preserved_bytes_and_identity():
    receipts = json.loads((ROOT / "content-receipts-r2.json").read_text(encoding="utf-8"))
    assert receipts["network_requests"] == 2
    assert receipts["db_write"] is False
    for document in receipts["documents"]:
        pdf = ROOT / "artifacts" / "document-review" / Path(document["file"]).name
        raw = pdf.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == document["sha256"]
        reader = PdfReader(str(pdf))
        assert len(reader.pages) == document["pages"]
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        for snippet in document["snippets"]:
            assert snippet["text"] in text


def test_decision_manifest_is_review_only_and_sha_bound():
    manifest = json.loads((ROOT / "decision-manifest-r2.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "DISPATCHABLE_FOR_REVIEW"
    assert len(manifest["decisions"]) == 2
    assert all(item["decision"] == "ACCEPT" for item in manifest["decisions"])
    assert all(item["promoted_fields"] == [] for item in manifest["decisions"])
    assert manifest["dispatch_payload"] == {
        "review_only": True,
        "approve": False,
        "apply": False,
        "proposal_retry": False,
        "next_gate": "document-review acceptance/revalidation, then normal proposal regeneration with SHA-bound effects",
    }
