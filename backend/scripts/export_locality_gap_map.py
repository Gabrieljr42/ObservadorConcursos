"""Export locality gaps without inferring a city from a contest title."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def build(payload: dict, source: str) -> dict:
    rows = []
    for item in payload.get("catalogue", []):
        city = item.get("cidade")
        uf = item.get("uf")
        rows.append({
            "concurso_id": item.get("id"),
            "title": item.get("titulo"),
            "cidade": city,
            "uf": uf,
            "localidade_state": "present_in_api" if city or uf else "absent_in_api",
            "title_is_not_locality_evidence": True,
            "detail_http": item.get("detail_http"),
            "document_review": item.get("review") or {},
            "amendments": item.get("amendments") or [],
        })
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": source,
        "input_at": payload.get("at"),
        "records": rows,
        "counts": {
            "records": len(rows),
            "locality_present_in_api": sum(r["localidade_state"] == "present_in_api" for r in rows),
            "locality_absent_in_api": sum(r["localidade_state"] == "absent_in_api" for r in rows),
        },
        "next_action": "Reextrair cidade/UF somente de edital/detalhe preservado e anexar página, trecho, SHA-256 e URL; não usar título isolado.",
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
