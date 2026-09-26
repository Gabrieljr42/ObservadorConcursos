"""Compose a non-authoritative 99-source matrix candidate from preserved receipts."""
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CSV = ROOT / "docs/execucao/tarefas/T005-matriz-candidata-20260912.csv"
SNAP = ROOT / "backend/.tenderproof/product-completion/delivery-current-20260912T195125613173Z.json"
OUT = ROOT / "docs/execucao/tarefas/T005-matriz-candidata-20260912.json"

def main():
    with CSV.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    snap = json.loads(SNAP.read_text(encoding="utf-8"))
    current = {str(x.get("source")): x for x in snap.get("sources", [])}
    try:
        from app.tenderproof.source_adapters import SOURCE_ADAPTERS
        adapters = {k: type(v).__name__ for k, v in SOURCE_ADAPTERS.items()}
        states = {k: getattr(v, "implementation_state", "implemented") for k, v in SOURCE_ADAPTERS.items()}
    except Exception:
        adapters, states = {}, {}
    result = []
    for row in rows:
        source = row["fonte"]
        c = current.get(source, {})
        cycle = c.get("latest_cycle") or {}
        item = {
            "numero": int(row["numero"]), "source": source, "name": row["nome"],
            "status_from_preserved_matrix": row["status_objetivo"],
            "adapter_current": adapters.get(source),
            "adapter_state_current": states.get(source, row.get("implementation_state_historico") or "pending"),
            "enabled_snapshot": bool(c.get("enabled")),
            "cycle_id": cycle.get("cycle_id"), "cycle_status": cycle.get("status"),
            "detail_jobs_snapshot": c.get("historical_detail_jobs") or {},
            "published_contest_ids": [int(x) if x.isdigit() else x for x in row.get("concursos_no_aplicativo", "").split(",") if x],
            "sync_evidence": row.get("evidencia_especifica", ""),
            "coverage_gaps": row.get("lacunas", ""),
            "next_action": row.get("acao_minima", ""),
        }
        if source == "fapemat_selection":
            item["status_candidate"] = "internal_pending_external_probe"
            item["external_block"] = "unconfirmed_transport_reset"
            item["next_action"] = "Revalidar transporte público em nova janela; testar apenas aliases já preservados e rota Editais, sem TLS bypass/login."
        else:
            item["status_candidate"] = row["status_objetivo"]
        result.append(item)
    assert len(result) == 99 and {x["numero"] for x in result} == set(range(1, 100))
    OUT.write_text(json.dumps({"generated_from": [str(CSV), str(SNAP)], "authoritative": False, "sources": result}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(OUT), "sources": len(result), "fapemat_status": next(x["status_candidate"] for x in result if x["source"] == "fapemat_selection")}))

if __name__ == "__main__": main()
