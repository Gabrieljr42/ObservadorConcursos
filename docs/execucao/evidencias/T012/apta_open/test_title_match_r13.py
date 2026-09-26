import html
import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).parent


def norm(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", html.unescape(value)).split()).casefold()


def test_manifest_and_request_title_mismatch_survives_normalization():
    receipt = json.loads((ROOT / "live-document-review-receipt-r12-20260913.json").read_text(encoding="utf-8"))
    expected = receipt["pending_before"]["manifest_title"]
    sent = receipt["request"]["title"]
    assert expected != sent
    assert expected.encode("utf-8") != sent.encode("utf-8")
    assert unicodedata.normalize("NFC", expected) != unicodedata.normalize("NFC", sent)
    assert norm(expected) != norm(sent)
    assert norm(html.unescape(expected)) != norm(html.unescape(sent))


def test_receipt_contains_complete_expected_manifest_title():
    receipt = json.loads((ROOT / "live-document-review-receipt-r12-20260913.json").read_text(encoding="utf-8"))
    assert receipt["pending_before"]["manifest_title"] == "Edital de Retificação I ao Edital de Abertura de Inscrições"
