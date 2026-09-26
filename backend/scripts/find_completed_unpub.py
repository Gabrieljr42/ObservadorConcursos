import sqlite3
import json
from app.tenderproof.store import get_store
from app.tenderproof.continuous_store import get_continuous_store
from app.database import SessionLocal
from app.models import Concurso, Source

db = SessionLocal()
published_source_ids = {c.source_id for c in db.query(Concurso.source_id).distinct().all()}

conn = sqlite3.connect('/var/lib/observador/tenderproof/operational.sqlite3')
cur = conn.cursor()
cur.execute("SELECT run_id, payload FROM runs")
rows = cur.fetchall()

store = get_store()
queue = get_continuous_store()

unpub_runs = []
for rid, payload_str in rows:
    p = json.loads(payload_str)
    if p.get('execution_status') != 'completed':
        continue
    src_type = p.get('source')
    # find source_id
    src_obj = db.query(Source).filter_by(source_type=src_type).first()
    if not src_obj or src_obj.id in published_source_ids:
        continue
    
    cand = p.get('selected_candidate_id')
    art = p.get('artifact', {})
    art_sha = art.get('sha256') if art else None
    
    run = store.get_run(rid)
    rev = queue.review_for_run(run) if run else {'pending': True}
    
    unpub_runs.append({
        'run_id': rid,
        'source_name': src_obj.name,
        'source_id': src_obj.id,
        'source_type': src_type,
        'candidate_id': cand,
        'artifact_sha': art_sha,
        'review_pending': rev.get('pending'),
        'review_docs_count': len(rev.get('documents', []))
    })

print(f"Total completed runs for unpublished sources: {len(unpub_runs)}")
for u in unpub_runs:
    print(f"Source {u['source_id']:2d} ({u['source_type']}): Run {u['run_id']} | Cand: {u['candidate_id']} | RevPending: {u['review_pending']} (docs: {u['review_docs_count']})")
db.close()
