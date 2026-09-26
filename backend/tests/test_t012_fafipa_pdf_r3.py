from pathlib import Path
import json
from app.tenderproof.fafipa_t012 import EXPECTED_SHA256

ROOT = Path(__file__).parents[2]
PDF = ROOT / "docs/execucao/evidencias/T012/fafipa_open/artifacts/fafipa-4208-edital.pdf"
RUN = ROOT / "docs/execucao/evidencias/T012/fafipa_open/T012-fafipa-open-reviewed-run-r3.json"

def test_r3_evidence_is_contained_in_pdf():
    text = "\n".join((p.extract_text() or "") for p in __import__("pypdf").PdfReader(str(PDF)).pages)
    run = json.loads(RUN.read_text(encoding="utf-8"))
    assert run["artifact"]["sha256"] != EXPECTED_SHA256
    for field in run["fields"]:
        for ev in field["evidence"]:
            assert ev["document_sha256"] == run["artifact"]["sha256"]
            assert ev["snippet"] in text
