"""Acquire the public counterpart of a preview link with matching article identity."""
import hashlib,json,re
from dataclasses import replace
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import parse_qs,urlsplit
from bs4 import BeautifulSoup
from app.tenderproof.http_driver import BoundedHTTPDriver
from app.tenderproof.security import TenderProofSettings
from app.tenderproof.processing import extract_pages_isolated


def main():
    base=Path('.tenderproof/product-completion/fapeg')
    public=json.loads((base/'call33-public-address.json').read_text(encoding='utf-8'))
    inventory=json.loads((base/'research-20260909T183835Z/report.json').read_text(encoding='utf-8'))
    row=next(c for c in inventory['calls'] if c['number']=='33/2025' and c['state']=='em-andamento')
    post_id=parse_qs(urlsplit(row['url']).query)['p'][0]
    root=base/datetime.now(timezone.utc).strftime('resolved-call-%Y%m%dT%H%M%SZ');root.mkdir()
    report={'observed_listing_row':row,'public_url':public['url'],'documents':[],'driver_closed':False,'source_integrated':False}
    def save():(root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    settings=TenderProofSettings();settings=replace(settings,limits=replace(settings.limits,max_navigations=20,total_timeout_s=600,max_documents=10))
    driver=BoundedHTTPDriver('fapeg_selection',settings)
    try:
        adapter=driver.adapter
        listing_url='https://goias.gov.br/fapeg/editais/em-andamento/'
        listing=driver.open_listing(listing_url)
        listing_sha=hashlib.sha256(listing.encode()).hexdigest()
        (root/(listing_sha+'.html')).write_text(listing,encoding='utf-8')
        discovery=adapter.parse_listing(listing,listing_url,1000)
        matches=[c for c in discovery.candidates if c.detail_url_observed==public['url']]
        if len(matches)!=1:raise ValueError('Public call not discovered by production listing acquisition')
        candidate=matches[0]
        report.update(listing_sha256=listing_sha,listing_candidates=len(discovery.candidates),listing_truncated=discovery.truncated,listing_diagnostics=discovery.diagnostics,discovered_by_production=True)
        driver.set_candidate(candidate);html=driver.open_detail(public['url'])
        articles=BeautifulSoup(html,'html.parser').select('article')
        if len(articles)!=1 or articles[0].get('id')!='post-'+post_id:raise ValueError('Public article does not match observed preview identifier')
        adapter.confirm_identity(candidate,html,public['url'])
        sha=hashlib.sha256(html.encode()).hexdigest();(root/(sha+'.html')).write_text(html,encoding='utf-8')
        report.update(detail_sha256=sha,article_id='post-'+post_id,identity_confirmed=True)
        for doc in adapter.documents(html,candidate):
            item=doc.model_dump(mode='json');report['documents'].append(item)
            try:
                data=driver.download(doc.url_requested,max_bytes=30*1024*1024).content
                digest=hashlib.sha256(data).hexdigest();(root/(digest+'.pdf')).write_bytes(data)
                pages,total,processed,truncated,errors=extract_pages_isolated(data,artifact_id='fapeg-resolved-'+digest,owner_id='fapeg-source-audit',max_bytes=30*1024*1024,max_pages=200)
                (root/(digest+'-pages.json')).write_text(json.dumps([p.model_dump(mode='json') for p in pages],ensure_ascii=False),encoding='utf-8')
                item.update(sha256=digest,bytes=len(data),total_pages=total,processed_pages=processed,truncated=truncated,errors=errors)
            except Exception as exc:item['error']=type(exc).__name__+': '+str(exc)
            save();print(json.dumps({'documents':len(report['documents']),'pages':item.get('processed_pages'),'error':item.get('error')}),flush=True)
    finally:
        driver.close();report['driver_closed']=True;report['finished_at']=datetime.now(timezone.utc).isoformat();save()
    print(str(root),flush=True)


if __name__=='__main__':main()
