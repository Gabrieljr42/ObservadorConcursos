"""Read one IBGP candidate through existing connector; compare in disposable DB.

No Browser, publication, notifications or configured database connection.
Run from backend; preserves new observations separately from historical run.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.connectors.ibgp import IBGPConnector, IBGPCandidate
from app.database import Base
from app.tenderproof.contracts import TenderProofRun
from app.tenderproof.processing import extract_pages_isolated
from app.tenderproof.fields import extract_fields
from app.tenderproof.compare import compare
from app.tenderproof.publication_demo import seed_isolated_baseline
from app.tenderproof.service import read_only_baseline_from_concurso
from app.versioning import jsonable


def main():
    root = Path(__file__).resolve().parents[1] / '.tenderproof'
    historical = TenderProofRun.model_validate_json((root/'review/runs/tpr-c84fdce378eb.json').read_text(encoding='utf-8'))
    receipt = []
    allowed = {f'https://novo.ibgpconcursos.com.br/rest/concurso/{suffix}' for suffix in ('704','cargos/704','editais/704')}
    class BoundedReader:
        def get(self, url):
            if url not in allowed or len(receipt) >= 3: raise ValueError('unexpected source request')
            with httpx.stream('GET', url, timeout=20, follow_redirects=False) as response:
                data = b''
                for chunk in response.iter_bytes():
                    data += chunk
                    if len(data) > 2_000_000: raise ValueError('source response limit')
                receipt.append({'path':url.split('.br')[1],'status':response.status_code,
                    'sha256':hashlib.sha256(data).hexdigest(), 'observed_at':datetime.now(timezone.utc).isoformat()})
                return httpx.Response(response.status_code, content=data)
    item = IBGPConnector()._fetch_and_parse_json(IBGPCandidate(cod='704'), client=BoundedReader())
    if not item: raise ValueError('baseline observation unavailable')
    root.mkdir(exist_ok=True)
    observed = {'kind':'traditional_connector_observation','origin':'IBGPConnector one explicit candidate 704',
        'collected_at':datetime.now(timezone.utc).isoformat()}
    (root/'real-baseline-704.json').write_text(json.dumps(jsonable({'snapshot':item,'provenance':observed,'responses':receipt}),ensure_ascii=False,indent=2),encoding='utf-8')
    with tempfile.TemporaryDirectory(prefix='tenderproof-real-baseline-') as directory:
        os.environ['TENDERPROOF_PROCESSING_DIR'] = str(Path(directory)/'processing')
        engine = create_engine(f'sqlite:///{directory}/isolated.sqlite')
        Base.metadata.create_all(engine)
        try:
            with Session(engine) as db:
                contest, seed = seed_isolated_baseline(db, canonical_snapshot=item,
                    source_snapshot={'name':'IBGP','base_url':'https://novo.ibgpconcursos.com.br','source_type':'ibgp_open'}, provenance=observed)
                baseline, collected, origin = read_only_baseline_from_concurso(contest)
                content=(root/'review/artifacts'/Path(historical.artifact.storage_path).name).read_bytes()
                assert hashlib.sha256(content).hexdigest()==historical.artifact.sha256
                pages,*_=extract_pages_isolated(content,artifact_id=historical.artifact.artifact_id,owner_id='isolated-real-baseline')
                selected=next(c for c in historical.candidates if c.candidate_id==historical.selected_candidate_id)
                fields=extract_fields(candidate=selected,artifact=historical.artifact,pages=pages)
                result=compare(baseline=baseline,baseline_collected_at=collected,baseline_origin=origin,fields=fields)
                report={'label':'Real preserved PDF + new traditional connector observation; isolated comparison, no publication',
                    'historical_run':'tpr-c84fdce378eb','document_sha256':historical.artifact.sha256,
                    'seed':seed,'responses':receipt,'fields':[f.model_dump(mode='json') for f in fields],
                    'comparison':result.model_dump(mode='json'),'resources_created':0}
                (root/'real-baseline-comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
                print(json.dumps({'responses':[x['status'] for x in receipt], 'fields':{f.field_name:{'state':f.state.value,'value':f.value} for f in fields},'comparisons':len(result.fields),'canonical_writes':'disposable SQLite seed only'},ensure_ascii=True))
        finally: engine.dispose()


if __name__=='__main__': main()
