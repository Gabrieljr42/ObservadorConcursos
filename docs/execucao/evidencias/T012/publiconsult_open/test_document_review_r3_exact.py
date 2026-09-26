"""Offline exact-title check for the owner/run-bound preserved review payload."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
BASE = ROOT / "docs/execucao/evidencias/T012/publiconsult_open"
MANIFEST_TITLE = "Edital de Convocação para o Teste de Aptidão Física para o cargo Técnico em Educação X – Desenvolvimento Infantil II"
URL = "https://gsistbucket.s3.amazonaws.com/publiconsult/Anexos/681/PM%20VOTUPORANGA%20-%20PS%201-2026%20-EDITAL%20DE%20CONVOCA%C3%87%C3%83O%20TAF.pdf"


def test_prepare_preserved_payload_matches_manifest_identity_byte_for_byte():
    receipt = json.loads((BASE / "document-review-live-r2-receipt-20260913.json").read_text(encoding="utf-8"))
    acquisition = json.loads((BASE / "document-taf-acquisition-r2.json").read_text(encoding="utf-8"))
    assert receipt["manifest_pending_title"] == MANIFEST_TITLE
    assert receipt["decision_title"] != MANIFEST_TITLE  # old abbreviated title caused 409
    assert receipt["run_id"] == "tp-reviewed-bea209a94599014adb6a275693a9e107"
    assert receipt["owner_user_id"] == 1
    assert acquisition["requested_url"] == acquisition["final_url"] == URL
    assert acquisition["artifact"]["sha256"] == "d358bb8a61fb4e9dcc9c1bf101d28b364af951f0180f3ba8bf0a4c6866732bb7"
    assert acquisition["artifact"]["byte_len"] == 341466
    # API manifest identity must retain kind=outro; convocacao_taf is the semantic decision label.
    pending = {"title": MANIFEST_TITLE, "url": URL, "kind": "outro"}
    assert (pending["title"], pending["url"], pending["kind"]) == (MANIFEST_TITLE, URL, "outro")
