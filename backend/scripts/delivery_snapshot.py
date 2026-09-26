"""Read-only delivery snapshot; never approves or publishes catalogue data."""
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import text
from app.database import engine
from app.tenderproof.source_adapters import SOURCE_ADAPTERS

root = Path('/var/lib/observador/tenderproof')
def reader(name):
    db = sqlite3.connect((root / name).as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    return db

q = reader('continuous.sqlite3')
r = reader('operational.sqlite3')
report = {'at': datetime.now(timezone.utc).isoformat(), 'registered_adapters': len(SOURCE_ADAPTERS)}
with engine.connect() as db:
    db.execute(text('SET TRANSACTION READ ONLY'))
    report['catalogue'] = [dict(row) for row in db.execute(text('SELECT id, source_id, external_id, banca, titulo, orgao, edital_numero, inscricao_inicio, inscricao_fim, cargos, link_pagina, link_edital FROM concursos ORDER BY id')).mappings()]
    report['proposals'] = [dict(row) for row in db.execute(text('SELECT id, run_id, state, concurso_id FROM tenderproof_publication_proposals')).mappings()]
report['sources'] = []
for row in q.execute('SELECT source,enabled FROM source_config ORDER BY source'):
    source = row['source']
    cycle = q.execute('SELECT cycle_id,status,reasons FROM cycles WHERE source=? ORDER BY created_at DESC LIMIT 1',(source,)).fetchone()
    counts = dict(q.execute('SELECT j.status,count(*) FROM jobs j JOIN cycles c USING(cycle_id) WHERE c.source=? AND j.kind=? GROUP BY j.status',(source,'detail')).fetchall())
    report['sources'].append({'source':source,'enabled':row['enabled'],'latest_cycle':dict(cycle) if cycle else None,'historical_detail_jobs':counts})
report['batch_candidates'] = []
for row in q.execute("SELECT * FROM known_candidates WHERE source IN ('access_open','abcp_open','fenix_open') ORDER BY source,candidate_key"):
    runrow = r.execute('SELECT payload FROM runs WHERE run_id=?',(row['last_run_id'],)).fetchone()
    if not runrow: continue
    run = json.loads(runrow[0])
    review = q.execute('SELECT pending_documents FROM document_review_state WHERE source=? AND candidate_key=? AND owner=? AND mode=?',(row['source'],row['candidate_key'],row['owner'],row['mode'])).fetchone()
    report['batch_candidates'].append({'source':row['source'],'key':row['candidate_key'],'candidate':json.loads(row['candidate']),'run_id':row['last_run_id'],'execution':run['execution_status'],'validation':run['validation_status'],'fields':run['fields'],'pending_documents':json.loads(review[0]) if review else None})
print(json.dumps(report,ensure_ascii=False,default=str))

