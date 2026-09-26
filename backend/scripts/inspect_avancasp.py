import sqlite3
import json
from app.tenderproof.store import get_store
from app.tenderproof.continuous_store import get_continuous_store

conn = sqlite3.connect('/var/lib/observador/tenderproof/operational.sqlite3')
cur = conn.cursor()
cur.execute("SELECT run_id, payload FROM runs")
rows = cur.fetchall()

avancasp_runs = []
for rid, payload_str in rows:
    p = json.loads(payload_str)
    if p.get('source') == 'avancasp_open' or 'avancasp' in rid:
        avancasp_runs.append((rid, p))

print(f"Total AvancaSP runs: {len(avancasp_runs)}")
queue = get_continuous_store()
store = get_store()
for rid, p in avancasp_runs:
    cand = p.get('selected_candidate_id')
    status = p.get('execution_status')
    art = p.get('artifact', {})
    print(f"Run: {rid} | Cand: {cand} | Status: {status} | Art: {art.get('sha256') if art else None}")
    run = store.get_run(rid)
    if run:
        rev = queue.review_for_run(run)
        print(f"  Review pending: {rev.get('pending')} | docs: {len(rev.get('documents', []))}")
