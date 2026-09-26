"""Build a conservative field audit from the latest preserved API response.

The report describes what the API returned. ``absent_in_api`` is deliberately
not treated as ``absent_in_source``; extraction failures and source absence
remain unresolved until the preserved document is re-read.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


FIELDS = (
    "titulo", "orgao", "cidade", "uf", "modalidade", "status",
    "edital_numero", "edital_data", "inscricao_inicio", "inscricao_fim",
    "prova_data", "vagas", "salario_min", "salario_max", "taxa",
    "escolaridade", "cargos", "publications",
)


def state(value: object, *, field: str) -> str:
    if value is None or value == "" or value == []:
        return "absent_in_api"
    if field == "cargos" and not isinstance(value, list):
        return "extraction_failure_or_untyped"
    return "present_in_api"


def build(payload: dict, source_path: str) -> dict:
    records = []
    for contest in payload.get("catalogue", []):
        field_states = {
            field: state(contest.get(field), field=field) for field in FIELDS
        }
        records.append({
            "concurso_id": contest.get("id"),
            "title": contest.get("titulo"),
            "source_origin": contest.get("source") or contest.get("banca") or "unknown_in_api",
            "detail_http": contest.get("detail_http"),
            "document_review": contest.get("review") or {},
            "history": {"amendments": contest.get("amendments") or []},
            "field_states": field_states,
            "cargos_count": len(contest["cargos"]) if isinstance(contest.get("cargos"), list) else None,
            "classification_note": "API snapshot only; absent_in_api is not source absence and may be extraction failure.",
        })
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": source_path,
        "input_at": payload.get("at"),
        "records": records,
        "counts": {
            "records": len(records),
            "with_cargos": sum(1 for r in records if r["cargos_count"] is not None),
            "without_cargos_in_api": sum(1 for r in records if r["cargos_count"] is None),
            "pending_document_review": sum(1 for r in records if (r["document_review"] or {}).get("pending") is True),
        },
        "interpretation": {
            "absent_in_api": "campo não retornado pelo snapshot API; não prova ausência na fonte",
            "extraction_failure_or_untyped": "payload incompatível com estrutura esperada; investigar extração",
            "present_in_api": "valor retornado; requer evidência documental antes de publicação",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    report = build(payload, str(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
