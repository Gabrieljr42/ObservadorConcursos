import json
from pathlib import Path

evidencias_dir = Path("docs/execucao/evidencias/T012")

targets = ["klc_open", "ufu_selection", "apta_open", "avalia_open"]

for target in targets:
    t_dir = evidencias_dir / target
    if not t_dir.exists():
        continue
    print("=" * 70)
    print(f"TARGET: {target}")
    files = list(t_dir.glob("*.json"))
    candidate_envelopes = []
    for f in files:
        if not ("envelope" in f.name.lower() or "reviewed" in f.name.lower() or "candidate" in f.name.lower()):
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(d, dict) and "schema" in d:
            candidate_envelopes.append((f.name, d))
            
    print(f"Envelopes found: {len(candidate_envelopes)}")
    for name, d in candidate_envelopes:
        schema = d.get("schema")
        art = d.get("artifact", {})
        art_sha = art.get("sha256")
        art_path = art.get("content_path")
        fields = d.get("fields", {})
        if isinstance(fields, dict):
            field_names = list(fields.keys())
        elif isinstance(fields, list):
            field_names = [f.get("field_name") if isinstance(f, dict) else str(f) for f in fields]
        else:
            field_names = []
        print(f"  - {name}")
        print(f"    Schema: {schema} | RunID: {d.get('run_id')} | Owner: {d.get('owner_user_id')}")
        print(f"    Artifact SHA: {art_sha}")
        print(f"    Artifact Path: {art_path}")
        print(f"    Fields: {field_names}")
