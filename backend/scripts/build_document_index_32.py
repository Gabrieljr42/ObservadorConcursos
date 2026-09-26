"""Build a compact, non-inferential document/run index for current catalogue rows."""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

OVERRIDES = {
    3: {"document_status": "document_evidence_present", "evidence": "docs/ENTREGA-2026-09-09.md; current snapshot amendment provenance SHA abf214200dfba8427d9597ac905e5b1b6a3e7920f03b642dcdcbbd22060c0bbd p.1", "runner": "backend/scripts/delivery_apply_pedrinhas.py"},
    4: {"document_status": "document_evidence_present", "evidence": "docs/ENTREGA-LOTE-01-CONFERENCIA.md; preserved edital cited there", "runner": None},
    30: {"document_status": "not_proven_in_index", "evidence": None, "runner": "backend/scripts/ibam_caruaru_proposal.py"},
}

def build(payload: dict, source: str) -> dict:
    rows = []
    for item in payload.get("catalogue", []):
        cid = item.get("id")
        review = item.get("review") or {}
        docs = review.get("documents") or []
        override = OVERRIDES.get(cid, {})
        # Keep one deterministic usable run per record: prefer an artifact,
        # then the last stored run. The full run history remains in runtime.
        best = sorted(ms, key=lambda m: (m.get("artifact_sha256") is not None, m.get("run_id") or ""), reverse=True)[:1]
        rows.append({
            "concurso_id": cid,
            "title": item.get("titulo"),
            "source": item.get("source") or item.get("banca") or "unknown_in_api",
            "run_id": best[0].get("run_id") if best else None,
            "artifact_sha256": best[0].get("artifact_sha256") if best else None,
            "artifact_path": (best[0].get("artifact_dir") + "/" + best[0].get("artifact_storage_path")) if best and best[0].get("artifact_storage_path") else None,
            "documents_in_api_review": [{"kind": d.get("kind"), "title": d.get("title"), "url": d.get("url")} for d in docs if isinstance(d, dict)],
            "document_status": override.get("document_status", "not_in_api_snapshot"),
            "evidence": override.get("evidence"),
            "runner": override.get("runner"),
            "missing_fields": [name for name in ("cidade", "uf", "cargos", "vagas", "salario_min", "salario_max", "taxa", "escolaridade", "prova_data") if item.get(name) in (None, "", [])],
            "ambiguous_fields": [],
            "extraction_failure_fields": [],
            "detail_http": item.get("detail_http"),
        })
    return {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "input": source, "input_at": payload.get("at"), "records": rows, "counts": {"records": len(rows), "documents_with_explicit_api_review": sum(bool(r["documents_in_api_review"]) for r in rows), "runs_indexed": 0, "artifacts_indexed": 0}, "interpretation": "run/artifact nulos significam não expostos no snapshot API; não significam ausência na fonte. IDs 3 e 4 têm evidência documental externa indicada; ID 30 exige documento próprio."}

def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument("input", type=Path); p.add_argument("output", type=Path); a = p.parse_args()
    data = json.loads(a.input.read_text(encoding="utf-8")); out = build(data, str(a.input)); a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"); print(json.dumps(out["counts"])); return 0

if __name__ == "__main__": raise SystemExit(main())
