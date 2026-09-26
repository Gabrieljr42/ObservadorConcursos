import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
EVIDENCE = ROOT / "docs/execucao/evidencias/T012/avancasp_open"


def _procedure():
    return json.loads((EVIDENCE / "document-review-operational-r5.json").read_text(encoding="utf-8"))


def test_old_case_is_incomplete_and_must_not_be_approved():
    procedure = _procedure()
    old = procedure["old_case"]
    assert old["case_id"] == "drc-preserved-1d4a34207027a52670a51a736a125257"
    assert old["prepared_documents"] == 1
    assert old["field_states"] == "all failed"
    assert old["disposition"] == "STALE_INCOMPLETE_DO_NOT_APPROVE"
    assert len(procedure["expected_documents"]) == 2


def test_parser_pin_gap_is_exact_and_not_a_store_transformation():
    procedure = _procedure()
    old = procedure["root_cause"]["production_pin"]
    staged = procedure["root_cause"]["staged_pin"]
    assert old["sha256"] != staged["sha256"]
    assert old["byte_len"] != staged["byte_len"]
    assert old["url"] != staged["url"]
    assert procedure["blocking_gap"]["status"] == "BLOCKED_UNTIL_PARSER_DEPLOYMENT"
    assert procedure["root_cause"]["staged_pin"]["pages"] == 48


def test_review_cases_code_proves_reuse_and_two_document_retry_semantics():
    code = (ROOT / "backend/app/tenderproof/review_cases.py").read_text(encoding="utf-8")
    assert "len(existing.get('documents', [])) == 1" in code
    assert "existe uma revisão preservada diferente" in code
    assert "expected = sorted(repr(document_identity(document)) for document in baseline['pending'])" in code
    assert "actual == expected" in code
    assert "case_id='drc-'+uuid.uuid4().hex" in code
    assert "len(decisions)!=len(expected)" in code


def test_replacement_must_contain_both_distinct_sha_bound_pdfs():
    procedure = _procedure()
    expected = procedure["expected_documents"]
    assert {doc["sha256"] for doc in expected} == {
        "c60fcc60f0037c4f28907460cf8a60ec6832b115b28988e81d77ebbb66441637",
        "49b2137790ee4915ef3ef058e15d94bde937e8bd766840681a278b59d5eb5cfd",
    }
    assert expected[0]["pages"] == 48
    assert expected[1]["pages"] == 49
    assert procedure["safe_reprocessing_procedure"][1].startswith("Do not call prepare-preserved")


def test_r5_is_read_only_and_does_not_authorize_live_actions():
    procedure = _procedure()
    receipt = json.loads((EVIDENCE / "document-review-operational-r5-receipt.json").read_text(encoding="utf-8"))
    assert all(value is False for value in receipt["side_effects"].values())
    assert procedure["blocking_gap"]["gap"]
    assert receipt["old_case_action"].startswith("retain audit row")
