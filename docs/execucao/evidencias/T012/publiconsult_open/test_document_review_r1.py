"""Fail-closed reproduction for the pending Publiconsult/681 TAF document."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
RECEIPT = ROOT / "docs/execucao/evidencias/T012/publiconsult_open/live-proposal-receipt-20260913.json"
PRINCIPAL = "https://gsistbucket.s3.amazonaws.com/publiconsult/Anexos/681/PM%20VOTUPORANGA%20-%20PS%201-2026%20-EDITAL%20DE%20CONVOCA%C3%87%C3%83O%20TAF.pdf"


def test_pending_taf_is_not_mistaken_for_preserved_principal():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    pending = receipt["document_review_pending"]
    assert receipt["source_id"] == 56 and receipt["external_id"] == "681"
    assert pending["kind"] == "outro"
    assert pending["url"] == PRINCIPAL
    assert "Convocação" in pending["title"] and "Teste de Aptidão Física" in pending["title"]
    assert receipt["artifact"]["sha256"] == "7e3bc67ae2d209679dabaa791d7d63fb12369dd53e1da85cda9831721bd9917f"
    # The live envelope artifact is the opening edital, not the pending TAF.
    assert "Edital%20de%20Abertura" in receipt["envelope"]["path"] or receipt["envelope"]["path"].endswith("canonical35.json")
    assert pending["url"] != "https://gsistbucket.s3.amazonaws.com/publiconsult/Anexos/681/PM%20VOTUPORANGA%20-%20PS%201-2026%20-Edital%20de%20Abertura%20de%20Inscri%C3%A7%C3%B5es.pdf"
    # No pending-document bytes/receipt means approval must remain blocked.
    assert receipt["proposal_attempt"]["http"] == 409
    assert receipt["proposal_attempt"]["retry"] is False
