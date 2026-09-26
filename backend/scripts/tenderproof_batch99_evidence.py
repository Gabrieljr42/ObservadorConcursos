"""Read-only final-batch audit of reports, durable runs, captures and PDF bytes."""
import json
from collections import defaultdict
from datetime import datetime,timezone
from tenderproof_batch60_evidence import ROOT,DOCS,BACKEND,read,digest,validate_sample,SOURCE_ADAPTERS

def main():
    output=DOCS/'tenderproof-batch99-current-validation.json'
    batch=next(b for b in read(DOCS/'tenderproof-rollout-plan.json')['batches'] if b['cumulative_sources']==99)
    sources=batch['sources'];assert len(sources)==39 and len(set(sources))==39
    directories=list((BACKEND/'tests/fixtures').glob('tenderproof_batch99*'))
    samples=defaultdict(list);attempts=[];errors=[];inputs=[]
    for path in sorted(DOCS.glob('tenderproof-batch99-*.json')):
        if path==output:continue
        report=read(path)
        if not isinstance(report,dict) or not isinstance(report.get('cycles'),list):continue
        inputs.append({'file':str(path.relative_to(ROOT)),'sha256':digest(path)})
        for cycle in report['cycles']:
            source=cycle.get('source')
            if source not in sources:continue
            for attempt in cycle.get('attempts',[]):
                row={'source':source,'report':path.name,'cycle':cycle.get('cycle'),'run_id':attempt.get('run_id'),
                    'external_id':(attempt.get('candidate') or {}).get('external_id'),
                    'execution_status':attempt.get('execution_status'),'validation_status':attempt.get('validation_status'),
                    'error':attempt.get('error'),'offline':report.get('network_requests')==0}
                attempts.append(row)
                if row['execution_status']!='completed' or row['validation_status']!='valid':continue
                try:checked=validate_sample(report,cycle,attempt,directories)
                except (ValueError,KeyError,OSError) as exc:
                    errors.append({**row,'audit_error':str(exc)});continue
                samples[source].append({**row,**checked,'total_pages':attempt.get('total_pages')})
    rows=[];files={}
    for source in sources:
        paired=defaultdict(set)
        for sample in samples[source]:
            if not sample['offline']:paired[(sample['report'],sample['external_id'])].add(sample['cycle'])
            files[sample['artifact_path']]=sample
        rows.append({'source':source,'adapter_registered':source in SOURCE_ADAPTERS,
            'two_cycles_same_candidate_verified':any({1,2}<=cycles for cycles in paired.values()),
            'samples':samples[source],'homologation_state':'pending_batch_gate',
            'coverage':'bounded explicit adapter scope only; no whole-source certification'})
    hashes={v['artifact_sha256']:v['artifact_bytes'] for v in files.values()}
    report={'generated_at':datetime.now(timezone.utc).isoformat(),'batch_gate':batch['gate'],
        'scope':'Read-only evidence audit. Does not grant gate acceptance or replace live observation with offline replay.',
        'registration':{'total_registered_adapters':len(SOURCE_ADAPTERS),'batch_registered_adapters':sum(r['adapter_registered'] for r in rows),
            'batch_missing_adapters':[r['source'] for r in rows if not r['adapter_registered']]},
        'counts':{'sources_with_verified_valid_pdf':sum(bool(r['samples']) for r in rows),
            'sources_with_two_verified_cycles':sum(r['two_cycles_same_candidate_verified'] for r in rows),
            'distinct_durable_pdf_files_verified':len(files),'distinct_pdf_sha256_verified':len(hashes),
            'physical_verified_pdf_bytes':sum(v['artifact_bytes'] for v in files.values()),'deduplicated_verified_pdf_bytes':sum(hashes.values())},
        'sources':rows,'attempts':attempts,'input_reports':inputs,'audit_errors':errors,'production_activation_performed':False}
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('registration','counts','audit_errors')},ensure_ascii=True))
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
