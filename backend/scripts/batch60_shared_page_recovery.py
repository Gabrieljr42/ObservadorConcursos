"""Explicit local recovery after measured147/83-page PDFs exceed default60.

No network, defaults unchanged. Reuses both original live cycles' verified bytes.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone
from pypdf import PdfReader
from io import BytesIO
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.tenderproof.service import TenderProofService
from app.tenderproof.store import TenderProofStore
from app.tenderproof.security import TenderProofSettings,TenderProofLimits
from app.tenderproof.source_adapters import get_source_adapter
from tenderproof_pilot_continuous_replay import PreservedDriver,capture
from tenderproof_batch30_recovery_validation import environment


if __name__=='__main__':
    origin=Path('../docs/tenderproof-batch60-shared-fixed-live.json')
    report=json.loads(origin.read_text(encoding='utf-8'))
    root=Path('.tenderproof/b60pages').resolve()
    root.mkdir(parents=True,exist_ok=False)
    captures=[Path('tests/fixtures/tenderproof_batch60_shared')]
    fixtures=[]
    os.environ['TENDERPROOF_ARTIFACT_DIR']=str(Path(report['root'])/'artifacts')
    for cycle in report['cycles']:
        attempt=next(a for a in cycle['attempts'] if a['candidate']['external_id']=={'fundep_open':'72','facet_open':'44'}[cycle['source']])
        run=TenderProofStore().get_run(attempt['run_id'])
        pdf=TenderProofStore().load_artifact_bytes(run.artifact)
        assert hashlib.sha256(pdf).hexdigest()==run.artifact.sha256
        pages=len(PdfReader(BytesIO(pdf),strict=True).pages)
        limit=next(n for n in (80,120,160,200) if n>=pages)
        candidate=next(c for c in run.candidates if c.candidate_id==run.selected_candidate_id)
        data=dict(run=run,candidate=candidate,pdf=pdf,listing_url=cycle['captures'][0]['url'],
            listing_html=capture(cycle['captures'][0],captures),detail_html=capture(attempt['captures'][0],captures),
            replay_document_url=run.document.url_requested)
        fixtures.append((cycle,attempt,data,pages,limit))
    environment(root)
    result=dict(observed_at=datetime.now(timezone.utc).isoformat(),root=str(root),origin_report=str(origin),
        scope='offline recovery of two preserved live cycles per source; original60page failure preserved; explicit local page limits only',
        network_requests=0,browser_sessions=0,canonical_writes=0,original_page_limit=60,cycles=[])
    for cycle,attempt,data,pages,limit in fixtures:
        source=cycle['source'];adapter=get_source_adapter(source)
        settings=TenderProofSettings(allowlist_hosts=adapter.allowed_hosts,limits=TenderProofLimits(
            max_candidates=5,max_documents=100,max_navigations=4,max_pages=limit,total_timeout_s=120))
        service=TenderProofService(TenderProofStore(),settings)
        listing=service.start_discovery(PreservedDriver(data),source=source,listing_url=data['listing_url'],mode='real',owner_user_id=901)
        candidate=next(c for c in listing.candidates if c.external_id==data['candidate'].external_id)
        run=service.select_and_process(listing.run_id,candidate.candidate_id,PreservedDriver(data))
        row=dict(run_id=run.run_id,original_run_id=attempt['run_id'],candidate=candidate.model_dump(mode='json'),
            execution_status=run.execution_status,validation_status=run.validation_status,error=run.error,
            measured_pages=pages,explicit_page_limit=limit,artifact=run.artifact.model_dump(mode='json') if run.artifact else None,
            document=run.document.model_dump(mode='json') if run.document else None,
            validation=run.validation.model_dump(mode='json') if run.validation else None,
            total_pages=run.total_pages,processed_pages=run.processed_pages,captures=attempt['captures'])
        row['durable_hash_verified']=bool(run.artifact and hashlib.sha256(TenderProofStore().load_artifact_bytes(run.artifact)).hexdigest()==data['run'].artifact.sha256)
        result['cycles'].append(dict(source=source,cycle=cycle['cycle'],listing_run_id=listing.run_id,
            captures=cycle['captures'],coverage=listing.coverage,attempts=[row]))
        Path('../docs/tenderproof-batch60-shared-page-recovery.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
        print(source,cycle['cycle'],pages,limit,run.execution_status,run.validation_status,run.error,flush=True)
        assert run.validation_status.value=='valid' and row['durable_hash_verified']
    result['passed']=len(result['cycles'])==4
    Path('../docs/tenderproof-batch60-shared-page-recovery.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
