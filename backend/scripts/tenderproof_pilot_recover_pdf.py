"""Recover acquired official PDF after observed 62 pages exceeded configured 60.
Offline only, exact hash/captured HTML, explicitly revised max_pages=80.
"""
import json,os,hashlib
from pathlib import Path
from app.tenderproof.source_adapters import get_source_adapter
from app.tenderproof.contracts import Artifact
from app.tenderproof.security import TenderProofSettings,TenderProofLimits
from app.tenderproof.service import TenderProofService
from app.tenderproof.store import TenderProofStore
from app.tenderproof.solari_adapter import DownloadedBytes
from datetime import datetime,timezone
r=json.loads(Path('../docs/tenderproof-pilot-live-redirect-validation.json').read_text(encoding='utf-8'))
rec=next(c for c in r['cycles'] if c['source']=='funcern_selection')
attempt=next(a for a in rec['attempts'] if a['artifact'])
os.environ['TENDERPROOF_ARTIFACT_DIR']=str(Path(r['root'])/'artifacts')
store=TenderProofStore();artifact=Artifact.model_validate(attempt['artifact']);content=store.load_artifact_bytes(artifact)
assert hashlib.sha256(content).hexdigest()==artifact.sha256
root=Path('tests/fixtures/tenderproof_pilot')
listing=(root/rec['captures'][0]['file']).read_text(encoding='utf-8');detail=(root/attempt['captures'][0]['file']).read_text(encoding='utf-8')
class Replay:
 session_id=None
 replay_available=False
 def open_listing(self,url):return listing
 def open_detail(self,url):return detail
 def download(self,url,*,max_bytes):
  assert url==artifact.url_requested
  return DownloadedBytes(url_requested=url,url_final=artifact.url_final,content=content,content_type='application/pdf',redirect_chain=[url,artifact.url_final])
 def observed_json(self):return []
 def session_records(self):return []
 def diagnostics(self):return ['offline replay of acquired official bytes; no network']
 def replay_url(self):return None
 def close(self):pass
adapter=get_source_adapter('funcern_selection');settings=TenderProofSettings(allowlist_hosts=adapter.allowed_hosts,limits=TenderProofLimits(max_candidates=5,max_documents=100,max_pages=80))
s=TenderProofService(store,settings)
run=s.start_discovery(Replay(),source=adapter.source,listing_url=adapter.listing_urls[0],mode='real',owner_user_id=901)
run=s.select_and_process(run.run_id,attempt['candidate']['candidate_id'],Replay())
report={'observed_at':datetime.now(timezone.utc).isoformat(),'scope':'offline recovery of official acquired document; no new HTTP or browser','original_run':attempt['run_id'],'original_page_limit':60,'revised_explicit_page_limit':80,'bytes_hash_verified':True,'run_id':run.run_id,'source':run.source,'execution_status':run.execution_status,'validation_status':run.validation_status,'pages':run.total_pages,'error':run.error,'artifact':run.artifact.model_dump(mode='json') if run.artifact else None,'validation':run.validation.model_dump(mode='json') if run.validation else None}
Path('../docs/tenderproof-pilot-offline-recovery.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(run.execution_status,run.validation_status,run.total_pages,run.error)
