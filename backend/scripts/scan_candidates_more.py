import json
from pathlib import Path

evidencias_dir = Path("docs/execucao/evidencias/T012")

targets = [
    "fapece_selection", "faperj_selection", "fapesq_selection", 
    "funpec_selection", "zambini_open", "consulplan_open", "idcap_open"
]

for target in targets:
    t_dir = evidencias_dir / target
    if not t_dir.exists():
        continue
    files = list(t_dir.glob("*.json"))
    print("=" * 70)
    print(f"TARGET: {target} (files: {len(files)})")
    for f in files:
        if not ("envelope" in f.name.lower() or "reviewed" in f.name.lower() or "candidate" in f.name.lower() or "propost" in f.name.lower() or "receipt" in f.name.lower()):
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(d, dict):
            schema = d.get("schema")
            state = d.get("state")
            print(f"  - {f.name} | schema: {schema} | state: {state}")
