import json
import glob
from pathlib import Path
from app.tenderproof.reviewed_run_import import import_reviewed_run
from app.tenderproof.store import TenderProofStore

store = TenderProofStore()
evidencias_dir = Path("/app/docs/execucao/evidencias/T012")
if not evidencias_dir.exists():
    # check fallback
    evidencias_dir = Path("docs/execucao/evidencias/T012")

json_files = list(evidencias_dir.rglob("*.json"))

candidates = []
for jf in json_files:
    if "reviewed" not in jf.name.lower() and "envelope" not in jf.name.lower():
        continue
    try:
        data = json.loads(jf.read_text(encoding="utf-8"))
    except Exception:
        continue
    if not isinstance(data, dict):
        continue
    schema = data.get("schema", "")
    if "reviewed-run" not in schema:
        continue
    
    src = data.get("source")
    owner = data.get("owner_user_id")
    cands = data.get("candidates", [])
    cand_id = data.get("selected_candidate_id")
    artifact = data.get("artifact", {})
    art_sha = artifact.get("sha256")
    art_path = artifact.get("content_path")
    
    # test dry run
    try:
        dry_result = import_reviewed_run(data, store, dry_run=True)
        status = "dry_run_ok"
    except Exception as e:
        status = f"dry_run_failed: {e}"
        
    candidates.append({
        "file": str(jf.relative_to(evidencias_dir)),
        "source": src,
        "owner": owner,
        "cand_id": cand_id,
        "artifact_sha": art_sha,
        "artifact_path": art_path,
        "status": status,
        "fields": list(data.get("fields", {}).keys())
    })

print(f"Total reviewed-run candidates found: {len(candidates)}")
for c in candidates:
    print("-" * 50)
    print(f"File: {c['file']}")
    print(f"Source: {c['source']}, Cand: {c['cand_id']}, Status: {c['status']}")
    print(f"Fields: {c['fields']}")
