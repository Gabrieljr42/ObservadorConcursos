"""Bounded pilot proof: public HTTP only, isolated operational artifacts.
Run from backend: PYTHONPATH=. python scripts/tenderproof_pilot_live.py
Maximum: two cycles, eight sources, one listing and three details per source/cycle.
Each successful candidate stops sampling its source; no canonical publication.
"""
import hashlib,json,os,time
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode

def redact(value):
 if isinstance(value,dict):return {k:redact(v) for k,v in value.items()}
 if isinstance(value,list):return [redact(v) for v in value]
 if isinstance(value,str) and value.startswith(('http://','https://')):
  p=urlsplit(value)
  if any(k.lower().startswith('x-amz-') or k.lower() in ('awsaccesskeyid','signature') for k,v in parse_qsl(p.query)):
   return urlunsplit((p.scheme,p.netloc,p.path,urlencode([(k,'REDACTED') for k,v in parse_qsl(p.query)]),p.fragment))
 return value
from app.tenderproof.source_adapters import get_source_adapter
from app.tenderproof.pilot_adapters import PILOT_ADAPTERS
from app.tenderproof.http_driver import BoundedHTTPDriver
from app.tenderproof.security import TenderProofSettings,TenderProofLimits
from app.tenderproof.service import TenderProofService
from app.tenderproof.store import TenderProofStore
from app.tenderproof.contracts import ExecutionStatus
ROOT=Path('.tenderproof/pilot-live-20260907').resolve()
os.environ['TENDERPROOF_ARTIFACT_DIR']=str(ROOT/'artifacts')
os.environ['TENDERPROOF_PROCESSING_MODE']='local'
os.environ['TENDERPROOF_BROWSER_LIVE_ENABLED']='false'
REPORT=Path('../docs/tenderproof-pilot-live.json')
CAPTURE=Path('tests/fixtures/tenderproof_pilot')
class CapturingDriver(BoundedHTTPDriver):
 def __init__(self,source,settings,cycle):
  super().__init__(source,settings);self.cycle=cycle;self.captures=[]
 def _save(self,kind,url,html):
  name=f'{self.adapter.source}-cycle{self.cycle}-{kind}-{hashlib.sha256((url+html).encode()).hexdigest()[:10]}.html'
  b=html.encode('utf-8');(CAPTURE/name).write_bytes(b)
  self.captures.append(dict(kind=kind,url=url,file=name,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),format='decoded HTTP HTML normalized to UTF-8',observed_at=datetime.now(timezone.utc).isoformat()))
 def open_listing(self,url):
  html=super().open_listing(url);self._save('listing',url,html);return html
 def open_detail(self,url):
  html=super().open_detail(url);self._save('detail',url,html);return html

def main():
 report={'observed_at':datetime.now(timezone.utc).isoformat(),'scope':'two bounded public HTTP cycles; no full coverage or canonical publication','browser_sessions':0,'tls_verified':True,'root':str(ROOT),'cycles':[]}
 for cycle in range(1,3):
  for adapter in PILOT_ADAPTERS:
   begin=time.monotonic();settings=TenderProofSettings(allowlist_hosts=adapter.allowed_hosts,limits=TenderProofLimits(max_candidates=5,max_documents=100,max_navigations=8,max_pages=60,total_timeout_s=120))
   service=TenderProofService(TenderProofStore(),settings);driver=CapturingDriver(adapter.source,settings,cycle)
   listing=service.start_discovery(driver,source=adapter.source,listing_url=adapter.listing_urls[0],mode='real',owner_user_id=901)
   record={'source':adapter.source,'cycle':cycle,'listing_run_id':listing.run_id,'listing_status':listing.execution_status,'candidates_sampled':len(listing.candidates),'coverage':listing.coverage,'captures':driver.captures,'attempts':[]}
   for candidate in listing.candidates[:3]:
    # A fresh persisted sample run reuses this cycle's observed list, no extra request.
    from app.tenderproof.acquisition import new_run_id
    run=listing.model_copy(deep=True);run.run_id=new_run_id();service.store.put_run(run)
    detail_driver=CapturingDriver(adapter.source,settings,cycle)
    run=service.select_and_process(run.run_id,candidate.candidate_id,detail_driver)
    row={'run_id':run.run_id,'candidate':candidate.model_dump(mode='json'),'execution_status':run.execution_status,'validation_status':run.validation_status,'error':run.error,'captures':detail_driver.captures,'document':run.document.model_dump(mode='json') if run.document else None,'artifact':run.artifact.model_dump(mode='json') if run.artifact else None,'total_pages':run.total_pages,'processed_pages':run.processed_pages,'validation':run.validation.model_dump(mode='json') if run.validation else None,'fields':[{'field':f.field_name,'state':f.state} for f in run.fields]}
    record['attempts'].append(row)
    print(adapter.source,cycle,candidate.external_id,run.execution_status,run.validation_status,run.error,flush=True)
    if run.artifact:
     # Verify durable bytes from a new store handle; subprocess recovery tested separately.
     data=TenderProofStore().load_artifact_bytes(run.artifact)
     row['durable_hash_verified']=hashlib.sha256(data).hexdigest()==run.artifact.sha256
    if run.execution_status==ExecutionStatus.COMPLETED and run.validation_status.value=='valid':break
   record['duration_s']=round(time.monotonic()-begin,3);report['cycles'].append(record)
   REPORT.write_text(json.dumps(redact(report),ensure_ascii=False,indent=2,default=str),encoding='utf-8')
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--sources',nargs='*');parser.add_argument('--report');args=parser.parse_args()
 if args.sources:PILOT_ADAPTERS=tuple(a for a in PILOT_ADAPTERS if a.source in args.sources)
 if args.report:REPORT=Path(args.report)
 main()

