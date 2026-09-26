"""Validate current call discovery and repeat open-call originals through production HTTP driver."""
import argparse,hashlib,json
from dataclasses import replace
from datetime import datetime,timezone
from pathlib import Path
from app.tenderproof.fapeg_adapter import RESEARCH_LISTINGS
from app.tenderproof.http_driver import BoundedHTTPDriver
from app.tenderproof.security import TenderProofSettings


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--capture',type=Path,default=Path('.tenderproof/product-completion/fapeg/research-20260909T181827Z/report.json'))
    parser.add_argument('--state',choices=('inscricoes-abertas','em-andamento','encerrados'),default='inscricoes-abertas')
    parser.add_argument('--capture-only',action='store_true',help='Repeat only detail URLs present in the supplied audit capture')
    args=parser.parse_args()
    base=Path('.tenderproof/product-completion/fapeg')
    previous=json.loads(args.capture.read_text(encoding='utf-8'))
    known={d['url']:d.get('sha256') for d in previous['documents']}
    root=base/datetime.now(timezone.utc).strftime('research-adapter-%Y%m%dT%H%M%SZ');root.mkdir()
    report={'listings':[],'repeated_originals':[],'errors':[],'source_integrated':False,'driver_closed':False,'capture':str(args.capture),'acquisition_state':args.state}
    def save():(root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    settings=TenderProofSettings();settings=replace(settings,limits=replace(settings.limits,max_navigations=100,total_timeout_s=600,max_documents=500))
    driver=BoundedHTTPDriver('fapeg_selection',settings)
    try:
        adapter=driver.adapter;opened=[]
        for url in RESEARCH_LISTINGS:
            html=driver.open_listing(url);sha=hashlib.sha256(html.encode()).hexdigest();(root/(sha+'.html')).write_text(html,encoding='utf-8')
            page=adapter.parse_listing(html,url,1000)
            report['listings'].append({'url':url,'sha256':sha,'candidates':len(page.candidates),'truncated':page.truncated,'diagnostics':page.diagnostics})
            if url.endswith('/'+args.state+'/'):opened=page.candidates
            save()
        if args.capture_only:
            captured_urls={d['url'] for d in previous['details']}
            report['audit_capture_only']=True
            report['excluded_candidate_count']=sum(c.detail_url_observed not in captured_urls for c in opened)
            opened=[c for c in opened if c.detail_url_observed in captured_urls]
            report['captured_urls_missing_from_discovery']=sorted(captured_urls-{c.detail_url_observed for c in opened})
        for candidate in opened:
            row={'candidate':candidate.model_dump(mode='json')};report['repeated_originals'].append(row)
            try:
                driver.set_candidate(candidate);html=driver.open_detail(candidate.detail_url_observed);sha=hashlib.sha256(html.encode()).hexdigest();(root/(sha+'.html')).write_text(html,encoding='utf-8')
                adapter.confirm_identity(candidate,html,candidate.detail_url_observed)
                docs=adapter.documents(html,candidate);original=adapter.choose_document(docs)
                result=driver.download(original.url_requested,max_bytes=30*1024*1024);digest=hashlib.sha256(result.content).hexdigest();(root/(digest+'.pdf')).write_bytes(result.content)
                row.update(detail_sha256=sha,documents=[d.model_dump(mode='json') for d in docs],original_sha256=digest,identical_to_previous=known.get(original.url_requested)==digest)
            except Exception as exc:row['error']=type(exc).__name__+': '+str(exc)
            save();print(json.dumps({'candidate':candidate.title_observed,'identical':row.get('identical_to_previous'),'error':row.get('error')}),flush=True)
    finally:
        driver.close();report['driver_closed']=True;report['finished_at']=datetime.now(timezone.utc).isoformat();save()
    print(str(root),flush=True)


if __name__=='__main__':main()
