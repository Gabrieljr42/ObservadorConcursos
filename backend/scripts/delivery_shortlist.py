"""Bounded read-only shortlist from preserved operational runs; no acquisition."""
import json
import sqlite3
from pathlib import Path

root = Path('/var/lib/observador/tenderproof')
def reader(name):
    db = sqlite3.connect((root / name).as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    return db

q, r = reader('continuous.sqlite3'), reader('operational.sqlite3')
items = []
for row in q.execute('SELECT * FROM known_candidates'):
    saved = r.execute('SELECT payload FROM runs WHERE run_id=?', (row['last_run_id'],)).fetchone()
    if not saved:
        continue
    run = json.loads(saved[0])
    if run['execution_status'] != 'completed' or run['validation_status'] != 'valid':
        continue
    review = q.execute('SELECT pending_documents FROM document_review_state WHERE source=? AND candidate_key=? AND owner=? AND mode=?', (row['source'], row['candidate_key'], row['owner'], row['mode'])).fetchone()
    if not review or json.loads(review[0]):
        continue
    fields = {f['field_name']: f['value'] for f in run['fields'] if f['state'] == 'supported'}
    if not all(fields.get(k) for k in ('titulo','orgao','edital_numero')):
        continue
    items.append({'source':row['source'], 'key':row['candidate_key'], 'run_id':row['last_run_id'], 'fields':{k:v for k,v in fields.items() if k != 'remuneracao'}, 'document':run['artifact']['url_final']})
items.sort(key=lambda i: (i['fields'].get('inscricao_fim','') >= '2026-09-09', i['fields'].get('inscricao_fim','')), reverse=True)
selected, seen = [], set()
for item in items:
    if item['source'] not in seen:
        selected.append(item)
        seen.add(item['source'])
print(json.dumps({'eligible_sources_before_revalidation':len(seen), 'eligible_candidates_before_revalidation':len(items), 'shortlist':selected[:12]}, ensure_ascii=False))
