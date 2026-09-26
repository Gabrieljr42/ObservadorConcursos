"""Exercise the actual acquisition service in an isolated evidence store."""
import json,os
from dataclasses import replace
from datetime import datetime,timezone
from pathlib import Path
from app.tenderproof.http_driver import BoundedHTTPDriver
from app.tenderproof.service import TenderProofService
from app.tenderproof.store import TenderProofStore
from app.tenderproof.security import TenderProofSettings
from app.tenderproof.fapeg_adapter import FapegAdapter,RESEARCH_LISTINGS


def main():
    root=Path('.tenderproof/product-completion/fapeg')/datetime.now(timezone.utc).strftime('workbook-service-%Y%m%dT%H%M%SZ');root.mkdir()
    os.environ['TENDERPROOF_ARTIFACT_DIR']=str((root/'artifacts').resolve())
    settings=TenderProofSettings();settings=replace(settings,allowlist_hosts=FapegAdapter().allowed_hosts,limits=replace(settings.limits,max_navigations=50,total_timeout_s=300,max_documents=500,max_pages=200,max_candidates=1000))
    store=TenderProofStore();service=TenderProofService(store,settings)
    run=service.start_discovery(BoundedHTTPDriver('fapeg_selection',settings),source='fapeg_selection',listing_url=RESEARCH_LISTINGS[1],mode='real')
    candidate=next(c for c in run.candidates if c.title_observed.startswith('45/2025 |'))
    run=service.select_and_process(run.run_id,candidate.candidate_id,BoundedHTTPDriver('fapeg_selection',settings),mode='real')
    artifacts=([run.artifact] if run.artifact else [])+[s.artifact for s in run.supplementary_documents]
    report={'run_id':run.run_id,'execution_status':run.execution_status.value,'error':run.error,'candidate':candidate.model_dump(mode='json'),'artifacts':[{'sha256':a.sha256,'bytes':a.byte_len,'storage_path':a.storage_path,'content_type':a.content_type,'reload_verified':TenderProofStore().load_artifact_bytes(a) is not None} for a in artifacts],'source_integrated':False}
    report.update(validation_status=run.validation_status.value,workbook_readings=[{'sha256':extra.artifact.sha256,'cells':sum(len(s['cells']) for s in extra.reading['sheets']),'pending_features':extra.reading['pending_features']} for extra in run.supplementary_documents if extra.reading],pending_fields=[f.model_dump(mode='json') for f in run.fields if f.field_name=='anexos_estruturados'])
    (root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=True));print(str(root))


if __name__=='__main__':main()
