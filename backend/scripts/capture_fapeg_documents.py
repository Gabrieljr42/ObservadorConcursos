"""Acquire every observed public FAPEG personnel export through the bounded driver."""
import hashlib
import json
import time
import argparse
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from app.tenderproof.http_driver import BoundedHTTPDriver
from app.tenderproof.security import TenderProofSettings
from app.tenderproof.processing import extract_pages_isolated


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--retry-report',type=Path)
    args=parser.parse_args()
    prior=json.loads(args.retry_report.read_text(encoding='utf-8')) if args.retry_report else None
    retry_ids={d['doc_id'] for d in prior['documents'] if d.get('error') or d['kind']=='edital'} if prior else None
    root=Path('.tenderproof/product-completion/fapeg')/datetime.now(timezone.utc).strftime('documents-%Y%m%dT%H%M%SZ')
    root.mkdir(parents=True)
    settings=TenderProofSettings()
    settings=replace(settings,limits=replace(settings.limits,max_navigations=100,total_timeout_s=1200))
    driver=BoundedHTTPDriver('fapeg_selection',settings)
    report={'documents':[],'source_integrated':False,'published':False,'driver_closed':False}
    if prior:report.update(scope='Fresh discovery; retry failed exports and repeat original only',previous_report=str(args.retry_report))
    def save():
        (root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    try:
        adapter=driver.adapter
        listing=driver.open_listing(adapter.listing_urls[0])
        (root/'listing.html').write_text(listing,encoding='utf-8')
        candidates=adapter.parse_listing(listing,adapter.listing_urls[0]).candidates
        report['candidates']=[c.model_dump(mode='json') for c in candidates]
        for candidate in candidates:
            driver.set_candidate(candidate)
            html=driver.open_detail(candidate.detail_url_observed)
            digest=hashlib.sha256(html.encode()).hexdigest()
            (root/(digest+'.html')).write_text(html,encoding='utf-8')
            for document in adapter.documents(html,candidate):
                if retry_ids is not None and document.doc_id not in retry_ids:continue
                row={'candidate':candidate.external_id,'detail_sha256':digest,**document.model_dump(mode='json')}
                report['documents'].append(row)
                try:
                    result=driver.download_document(document,candidate,max_bytes=30*1024*1024)
                    sha=hashlib.sha256(result.content).hexdigest()
                    (root/(sha+'.pdf')).write_bytes(result.content)
                    pages,total,processed,truncated,errors=extract_pages_isolated(result.content,artifact_id='fapeg-'+sha,owner_id='fapeg-source-audit',max_bytes=30*1024*1024,max_pages=200)
                    (root/(sha+'-pages.json')).write_text(json.dumps([p.model_dump(mode='json') for p in pages],ensure_ascii=False),encoding='utf-8')
                    row.update(sha256=sha,bytes=len(result.content),total_pages=total,processed_pages=processed,truncated=truncated,errors=errors)
                except Exception as exc:
                    row['error']=type(exc).__name__+': '+str(exc)
                save()
                print(json.dumps({'document':document.doc_id,'pages':row.get('processed_pages'),'error':row.get('error')}),flush=True)
                time.sleep(1)
    finally:
        driver.close()
        report['driver_closed']=True
        report['finished_at']=datetime.now(timezone.utc).isoformat()
        save()
    print(str(root),flush=True)


if __name__=='__main__':
    main()
