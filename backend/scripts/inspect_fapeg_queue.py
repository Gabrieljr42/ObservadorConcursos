"""Read current FAPEG job/run evidence without mutating the queue."""
import json,sqlite3
from datetime import datetime,timezone
from app.tenderproof.store import artifact_dir


def main():
    root=artifact_dir().parent
    queue=sqlite3.connect((root/'continuous.sqlite3').as_uri()+'?mode=ro',uri=True);queue.row_factory=sqlite3.Row
    runs=sqlite3.connect((root/'operational.sqlite3').as_uri()+'?mode=ro',uri=True)
    try:
        cycle=queue.execute("SELECT cycle_id,status FROM cycles WHERE source='fapeg_selection' ORDER BY created_at DESC LIMIT 1").fetchone()
        report={'at':datetime.now(timezone.utc).isoformat(),'cycle':dict(cycle),'jobs':[]}
        for item in queue.execute('SELECT job_id,status,attempts,run_id,error,payload FROM jobs WHERE cycle_id=? AND kind=?',(cycle['cycle_id'],'detail')):
            payload=json.loads(item['payload']);title=payload.get('title_observed','') or ''
            if '/2026' not in title and not title.startswith('45/2025 |'):continue
            row={key:item[key] for key in ('job_id','status','attempts','run_id','error')};row['title']=title
            record=runs.execute('SELECT payload FROM runs WHERE run_id=?',(item['run_id'],)).fetchone() if item['run_id'] else None
            if record:
                run=json.loads(record[0]);row.update(execution_status=run['execution_status'],validation_status=run['validation_status'],run_error=run.get('error'),
                    workbook_readings=[{'sha256':extra['artifact']['sha256'],'cells':sum(len(s['cells']) for s in (extra.get('reading') or {}).get('sheets',[]))} for extra in run.get('supplementary_documents',[]) if extra['document'].get('file_format')=='xlsx'])
            report['jobs'].append(row)
        print(json.dumps(report,ensure_ascii=True))
    finally:
        runs.close();queue.close()


if __name__=='__main__':main()
