"""Read identities and timezone clauses from the three preserved artifacts."""
import hashlib
import json
from app.tenderproof.store import get_store
from app.tenderproof.processing import extract_pages_isolated
from delivery_next_reextract_three_2026 import TARGETS

store = get_store()
for source, run_id in TARGETS.items():
    run = store.get_run(run_id)
    candidate = next(c for c in run.candidates if c.candidate_id == run.selected_candidate_id)
    data = store.load_artifact_bytes(run.artifact)
    assert hashlib.sha256(data).hexdigest() == run.artifact.sha256
    pages, total, processed, truncated, errors = extract_pages_isolated(data,
        artifact_id=run.artifact.artifact_id, owner_id=str(run.owner_user_id),
        max_bytes=max(len(data), 30*1024*1024), max_pages=200, reuse_completed=True)
    assert total == processed and not truncated and not errors
    clauses = []
    for page in pages:
        lines = page.text.splitlines()
        for index, line in enumerate(lines):
            if any(word in line.casefold() for word in ('brasília', 'brasilia', 'fuso')):
                clauses.append({'page': page.page_number, 'snippet': '\n'.join(lines[max(0,index-1):index+2])})
    print(json.dumps({'source': source, 'external_id': candidate.external_id, 'sha256': run.artifact.sha256, 'timezone_clauses': clauses}, ensure_ascii=False))
