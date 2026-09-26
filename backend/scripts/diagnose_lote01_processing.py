"""Read preserved bytes and run extraction with each source's current limits."""
import hashlib, json, os, sys
from pathlib import Path
sys.path.insert(0, '/app')
from app.tenderproof.store import get_store
from app.tenderproof.processing import extract_pages_isolated, ProcessingError
from app.tenderproof.continuous_store import get_continuous_store

RUNS = {
    "abcp_2868_garca": "tp-tcj-b7b17f29eeac52a9a43f71c360753e43-1",
    "idib_362": "tp-tcj-b6372819d87e51c185e6427865a5bf62-1",
    "cebraspe_ponta_pora": "tp-tcj-2b58bacc0b6a5a028ffc292908b9b6da-1",
    "fepese_caxambu": "tp-tcj-8c4428c810c45812a92132a23bf42958-1",
}

def main():
    store = get_store(); queue = get_continuous_store(); report = {}
    for label, run_id in RUNS.items():
        run = store.get_run(run_id); row = {"run_id": run_id}
        if not run:
            row["error"] = "run_missing"; report[label] = row; continue
        row.update(source=run.source, owner_user_id=run.owner_user_id,
                   execution_status=str(run.execution_status), selected_candidate_id=run.selected_candidate_id,
                   artifact_id=run.artifact.artifact_id if run.artifact else None,
                   declared_bytes=run.artifact.byte_len if run.artifact else None,
                   declared_sha256=run.artifact.sha256 if run.artifact else None)
        conf = queue.configuration(run.owner_user_id, run.source)
        policy = (conf or {}).get("policy", {})
        row["policy"] = {k: policy.get(k) for k in ("max_pdf_pages", "max_download_bytes", "job_timeout_s", "processing_timeout_s")}
        content = store.load_artifact_bytes(run.artifact) if run.artifact else None
        row["actual"] = {"bytes": len(content) if content else None, "sha256": hashlib.sha256(content).hexdigest() if content else None}
        if content and run.artifact:
            try:
                pages, total, processed, truncated, errors = extract_pages_isolated(
                    content, artifact_id=run.artifact.artifact_id, owner_id=str(run.owner_user_id),
                    max_pages=int(policy.get("max_pdf_pages", 60)), max_bytes=int(policy.get("max_download_bytes", 30*1024*1024)),
                    capacity_wait_s=60, operation="extract_pdf", reuse_completed=False)
                row["extraction"] = {"total": total, "processed": processed, "truncated": truncated, "errors": errors,
                                     "nonempty_pages": sum(bool(p.text.strip()) for p in pages)}
            except Exception as exc:
                row["extraction_error"] = {"type": type(exc).__name__, "message": str(exc)}
        report[label] = row
    out = Path('/var/lib/observador/tenderproof/product-completion/lote-01-review')
    out.mkdir(parents=True, exist_ok=True); (out/'processing-diagnosis.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
if __name__ == '__main__': main()
