"""Build the deterministic offline ID17 reviewed-run envelope.

The output is a checked-in receipt input, not a pilot operation.  It uses the
preserved PDF and the same ReviewedRun model/importer used by production.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.tenderproof.contracts import Artifact
from app.tenderproof.fields import _evidence
from app.tenderproof.pdf_text import extract_pages
from app.tenderproof.contemax_cubati_jobs import (
    ARTIFACT_ID, EXTERNAL_ID, SHA256, BYTE_LEN, extract_cubati_jobs,
)
from app.tenderproof.reviewed_run_import import ReviewedRun, _run_id

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "docs/execucao/evidencias/T011/artifacts/T011-ID17-contemax-001-2024-art-06e60acb05.pdf"
OUT = ROOT / "docs/execucao/evidencias/T011/T011-reviewed-run-id17.json"
DETAIL = "https://www.contemaxconsultoria.com.br/site/concursos-em-andamento/prefeitura-municipal-de-cubati-pb"
DOCUMENT = "https://www.contemaxconsultoria.com.br/site/wp-content/uploads/2024/09/Edital-CUBATI.pdf"
TITLE = "Concurso Público n.º 001/2024 — Prefeitura Municipal de Cubati/PB"


def build() -> dict:
    content = PDF.read_bytes()
    assert len(content) == BYTE_LEN and hashlib.sha256(content).hexdigest() == SHA256
    artifact = Artifact(artifact_id=ARTIFACT_ID, sha256=SHA256, byte_len=BYTE_LEN,
                        url_requested=DOCUMENT, url_final=DOCUMENT,
                        content_type="application/pdf", downloaded_at="2026-09-08T16:11:28.760592Z")
    pages = extract_pages(content, artifact_id=ARTIFACT_ID)[0]
    cargos = extract_cubati_jobs(artifact, pages, _evidence, source="contemax_open", external_id=EXTERNAL_ID)
    assert cargos.state.value == "supported"
    p1 = next(p for p in pages if p.page_number == 1)
    p2 = next(p for p in pages if p.page_number == 2)
    fields = [
        {"field_name": "titulo", "value": TITLE,
         "evidence": [_evidence(artifact=artifact, page=p1, snippet="Concurso Público n.º 001/2024").model_dump(mode="json")]},
        {"field_name": "orgao", "value": "PREFEITURA MUNICIPAL DE CUBATI-PB",
         "evidence": [_evidence(artifact=artifact, page=p2, snippet="PREFEITURA MUNICIPAL DE CUBATI E ADOTA OUTRAS").model_dump(mode="json")]},
        {"field_name": "edital_numero", "value": "001/2024",
         "evidence": [_evidence(artifact=artifact, page=p1, snippet="Concurso Público n.º 001/2024").model_dump(mode="json")]},
        {"field_name": "cargos", "value": cargos.value,
         "evidence": [e.model_dump(mode="json") for e in cargos.evidence], "units": cargos.units},
    ]
    return {"schema": "tenderproof.reviewed-run.v1", "source": "contemax_open", "concurso_id": 17,
            "external_id": EXTERNAL_ID, "title": TITLE, "detail_url": DETAIL,
            "artifact": {k: v for k, v in artifact.model_dump(mode="json").items() if v is not None}
            | {"content_path": str(PDF.relative_to(ROOT))},
            "fields": fields, "pending_fields": [], "reference_only": True,
            "owner_user_id": 1, "observed_at": "2026-09-12T00:00:00Z"}


if __name__ == "__main__":
    envelope = build()
    model = ReviewedRun.model_validate(envelope)
    OUT.write_text(json.dumps(envelope, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(OUT), "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
                      "run_id": _run_id(model), "byte_len": OUT.stat().st_size}, ensure_ascii=False))
