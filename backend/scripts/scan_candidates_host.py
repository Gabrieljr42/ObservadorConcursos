import json
from pathlib import Path

evidencias_dir = Path("docs/execucao/evidencias/T012")
json_files = sorted(evidencias_dir.rglob("*.json"))

print(f"Total json files: {len(json_files)}")

reviewed_runs = []
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
    cand_obj = next((c for c in cands if c.get("candidate_id") == cand_id), {})
    ext_id = cand_obj.get("external_id")
    artifact = data.get("artifact", {})
    art_sha = artifact.get("sha256")
    art_path = artifact.get("content_path")
    
    # check if art_path exists locally
    art_exists = False
    if art_path:
        p = Path(art_path)
        if not p.is_absolute():
            p = Path("backend") / p
        art_exists = p.exists() or Path(art_path).exists()
        
    fields = data.get("fields", {})
    if isinstance(fields, dict):
        field_names = list(fields.keys())
    elif isinstance(fields, list):
        field_names = [f.get("field_name") if isinstance(f, dict) else str(f) for f in fields]
    else:
        field_names = []
    
    reviewed_runs.append({
        "file": str(jf.relative_to(evidencias_dir)),
        "source": src,
        "owner": owner,
        "cand_id": cand_id,
        "ext_id": ext_id,
        "art_sha": art_sha,
        "art_path": art_path,
        "art_exists": art_exists,
        "fields": field_names,
    })

print(f"Reviewed runs found: {len(reviewed_runs)}")
for r in reviewed_runs:
    print("=" * 60)
    print(f"File: {r['file']}")
    print(f"Source: {r['source']} | ExtID: {r['ext_id']} | Owner: {r['owner']}")
    print(f"Artifact SHA: {r['art_sha']}")
    print(f"Artifact Path: {r['art_path']} (Exists locally: {r['art_exists']})")
    print(f"Fields ({len(r['fields'])}): {', '.join(r['fields'])}")
