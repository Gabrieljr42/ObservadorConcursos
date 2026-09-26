"""Traverse FAPERO via production driver and repeat one documentary acquisition."""
import hashlib,json,time
from dataclasses import replace
from datetime import datetime,timezone
from pathlib import Path
from app.tenderproof.http_driver import BoundedHTTPDriver
from app.tenderproof.security import TenderProofSettings


def main():
    root=Path('.tenderproof/product-completion/fapero')/datetime.now(timezone.utc).strftime('adapter-%Y%m%dT%H%M%SZ');root.mkdir()
    settings=TenderProofSettings();settings=replace(settings,limits=replace(settings.limits,max_navigations=200,total_timeout_s=600))
    driver=BoundedHTTPDriver('fapero_selection',settings);report={'pages':[],'errors':[],'source_integrated':False,'published':False}
    def save():(root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    try:
        a=driver.adapter;pending=list(a.listing_urls);seen=set();candidates={}
        while pending:
            url=pending.pop(0)
            if url in seen:continue
            seen.add(url)
            try:
                body=driver.open_listing(url);sha=hashlib.sha256(body.encode()).hexdigest();(root/(sha+'.json')).write_text(body,encoding='utf-8')
                page=a.parse_listing(body,url);report['pages'].append({'url':url,'sha256':sha,'count':len(page.candidates),'truncated':page.truncated,'diagnostics':page.diagnostics})
                pending.extend(page.next_urls)
                for c in page.candidates:candidates[c.detail_url_observed]=c
            except Exception as exc:report['errors'].append({'url':url,'error':type(exc).__name__+': '+str(exc)})
            save();time.sleep(1)
        report['unique_candidates']=len(candidates)
        if candidates:
            c=next(c for c in candidates.values() if 'Empreender' in (c.title_observed or ''));driver.set_candidate(c);body=driver.open_detail(c.detail_url_observed)
            (root/'detail.html').write_text(body,encoding='utf-8');docs=a.documents(body,c);original=a.choose_document(docs)
            result=driver.download(original.url_requested,max_bytes=30*1024*1024);sha=hashlib.sha256(result.content).hexdigest();(root/(sha+'.pdf')).write_bytes(result.content)
            report['detail']={'candidate':c.model_dump(mode='json'),'documents':[d.model_dump(mode='json') for d in docs],'original_sha256':sha,'bytes':len(result.content)}
        report['finished_at']=datetime.now(timezone.utc).isoformat();save()
    finally:driver.close()
    print(json.dumps({'report':str(root/'report.json'),'candidates':report.get('unique_candidates'),'errors':report['errors']}),flush=True)


if __name__=='__main__':main()
