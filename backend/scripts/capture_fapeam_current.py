"""Repeat public discovery through the registered adapter and preserve current PDFs."""
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from app.tenderproof.fapeam_detail import parse_detail
from app.tenderproof.http_driver import BoundedHTTPDriver
from app.tenderproof.security import TenderProofLimits, TenderProofSettings
from app.tenderproof.source_adapters import get_source_adapter


def main():
    root=Path('.tenderproof/product-completion/fapeam')
    run=root/('traversal-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    run.mkdir(parents=True,exist_ok=False)
    report={'started_at':datetime.now(timezone.utc).isoformat(),'mode':'live registered HTTP adapter',
            'pages':[],'current_details':[],'scope_complete':False,'errors':[]}
    def save():
        (run/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    def preserve(raw,suffix):
        sha=hashlib.sha256(raw).hexdigest();path=run/(sha+suffix)
        if path.exists():
            if path.read_bytes()!=raw:raise ValueError('existing evidence differs')
        else:path.write_bytes(raw)
        return {'sha256':sha,'file':path.name,'bytes':len(raw)}
    adapter=get_source_adapter('fapeam_selection')
    settings=TenderProofSettings(allowlist_hosts=adapter.allowed_hosts,
        limits=TenderProofLimits(max_navigations=100,total_timeout_s=300,max_candidates=2000))
    driver=BoundedHTTPDriver(adapter.source,settings)
    last=[0.0]
    def gap():
        remaining=max(0,last[0]+1-time.monotonic())
        if remaining:time.sleep(remaining)
        last[0]=time.monotonic()
    driver.request_guard=gap
    pending=list(adapter.listing_urls);seen=set();candidates={};current={}
    try:
        while pending:
            if len(seen)>=60:raise ValueError('operational listing limit reached; traversal incomplete')
            url=pending.pop(0)
            if url in seen:continue
            html=driver.open_listing(url);page=adapter.parse_listing(html,url,limit=2000)
            evidence=preserve(html.encode('utf-8'),'.json');seen.add(url)
            report['pages'].append({'url':url,**evidence,'candidates':len(page.candidates),
                'next_urls':page.next_urls,'terminal_evidence':page.terminal_evidence,'truncated':page.truncated})
            if page.truncated:raise ValueError('candidate page truncated')
            for candidate in page.candidates:
                previous=candidates.get(candidate.external_id)
                if previous and previous.detail_url_observed!=candidate.detail_url_observed:
                    raise ValueError('conflicting candidate URL across tabs')
                candidates[candidate.external_id]=candidate
                if '?aba=editais-abertos&' in url or '?aba=fluxo-continuo&' in url:
                    current[candidate.external_id]=candidate
            for target in page.next_urls:
                adapter.validate_listing_url(target)
                if target not in seen and target not in pending:pending.append(target)
            report['unique_ids']=len(candidates);save()
        report['published_listing_links_exhausted']=True
        report['candidates']=[c.model_dump(mode='json') for c in candidates.values()]
        save()
        for candidate in current.values():
            result={'candidate':candidate.model_dump(mode='json')}
            report['current_details'].append(result)
            try:
                driver.set_candidate(candidate)
                # Preserve bytes before detail parsing, including changed page contracts.
                base=candidate.detail_url_observed.split('#')[0]
                def validate(url):
                    if url!=base:raise ValueError('detail redirect changes identity')
                response=driver._fetch(base,validate,2*1024*1024)
                result['html']=preserve(response.content,'.html')
                html=response.content.decode('utf-8-sig')
                adapter.confirm_identity(candidate,html,candidate.detail_url_observed)
                parsed=parse_detail(html,url=base,external_id=candidate.external_id)
                result['external_references']=parsed['external_references']
                documents=adapter.documents(html,candidate)
                result['documents']=[d.model_dump(mode='json') for d in documents]
                selected=adapter.choose_document(documents)
                pdf=driver.download(selected.url_requested,max_bytes=settings.limits.max_download_bytes)
                result['principal_pdf']={**preserve(pdf.content,'.pdf'),'url':pdf.url_final}
            except Exception as exc:
                result['error']=type(exc).__name__+': '+str(exc)
            save()
    except Exception as exc:
        report['errors'].append(type(exc).__name__+': '+str(exc))
    finally:
        driver.close();report['finished_at']=datetime.now(timezone.utc).isoformat()
        report['requests']=driver.requests;report['remaining_listing_cursors']=pending;save()
    print(json.dumps({'report':str(run/'report.json'),'pages':len(report['pages']),
        'unique_ids':len(candidates),'current_details':len(report['current_details']),
        'pdfs':sum('principal_pdf' in d for d in report['current_details']),
        'errors':report['errors'],'detail_errors':[d.get('error') for d in report['current_details'] if d.get('error')]}))


if __name__=='__main__':main()
