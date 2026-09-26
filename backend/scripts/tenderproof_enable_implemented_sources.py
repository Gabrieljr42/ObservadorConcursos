"""Configure real HTTP collection without granting publication or browser use.

Existing source policies are preserved. The immutable report records the
before/after configuration; reruns do not overwrite it or reset active cycles.
"""
import argparse
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.tenderproof.source_adapters import SOURCE_ADAPTERS
from app.tenderproof.continuous_store import get_continuous_store, SourcePolicy
from app.tenderproof.continuous import operator_authorized, continuous_enabled


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--owner',type=int,required=True)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--source', action='append', choices=sorted(SOURCE_ADAPTERS),
                        help='Limit configuration to these registered sources; repeat to select several.')
    args=parser.parse_args()
    if not operator_authorized(args.owner) or not continuous_enabled():
        raise ValueError('Authorized continuous operator and enabled runtime required')
    queue=get_continuous_store();plan=[]
    for source,adapter in SOURCE_ADAPTERS.items():
        if args.source and source not in args.source:
            continue
        existing=queue.configuration(args.owner,source)
        state=getattr(adapter,'implementation_state','implemented')
        if existing:
            plan.append({'source':source,'action':'preserve','before':existing});continue
        if state!='implemented':
            plan.append({'source':source,'action':'implementation_pending','state':state});continue
        for url in adapter.listing_urls:adapter.validate_listing_url(url)
        policy=SourcePolicy(enabled=True,mode='real',interval_s=86400,
            max_listing_pages=100,max_candidates=500,max_documents=500,max_pdf_pages=200,
            max_attempts=3,min_request_gap_s=2,job_timeout_s=300,cycle_timeout_s=86400,
            allow_browser=False,max_browser_seconds=0)
        plan.append({'source':source,'action':'configure_http','before':None,
                     'listing_urls':list(adapter.listing_urls),'policy':policy.model_dump()})
    report={'created_at':datetime.now(timezone.utc).isoformat(),'owner':args.owner,
            'scope':'Configuration and acquisition only; no source completion or publication granted',
            'applied':False,'sources':plan}
    if args.apply:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        # Exclusive creation prevents accidentally reusing an old authorization
        # record as the record of a different configuration operation.
        with args.report.open('x',encoding='utf-8') as output:
            json.dump(report,output,ensure_ascii=False,indent=2)
        for item in plan:
            if item['action']=='configure_http':
                queue.configure(args.owner,item['source'],SourcePolicy.model_validate(item['policy']))
        report['applied']=True
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    from collections import Counter
    print(json.dumps({'applied':report['applied'],'actions':dict(Counter(p['action'] for p in plan))}))


if __name__=='__main__':main()
