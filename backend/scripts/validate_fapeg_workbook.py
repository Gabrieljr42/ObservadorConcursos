"""Live source-detail binding and public workbook acquisition with production limits."""
import hashlib,json
from dataclasses import replace
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin
from app.tenderproof.http_driver import BoundedHTTPDriver
from app.tenderproof.fapeg_workbook import acquire_public_workbook,share_folder
from app.tenderproof.fapeg_adapter import RESEARCH_LISTINGS
from app.tenderproof.security import TenderProofSettings


def main():
    base=Path('.tenderproof/product-completion/fapeg')
    root=base/datetime.now(timezone.utc).strftime('workbook-adapter-%Y%m%dT%H%M%SZ');root.mkdir()
    report={'source_integrated':False,'driver_closed':False,'documents':[]}
    settings=TenderProofSettings();settings=replace(settings,limits=replace(settings.limits,max_navigations=30,total_timeout_s=300))
    driver=BoundedHTTPDriver('fapeg_selection',settings)
    try:
        html=driver.open_listing(RESEARCH_LISTINGS[1]);adapter=driver.adapter
        page=adapter.parse_listing(html,RESEARCH_LISTINGS[1],1000)
        candidate=next(c for c in page.candidates if c.title_observed.startswith('45/2025 |'))
        driver.set_candidate(candidate);detail=driver.open_detail(candidate.detail_url_observed)
        body=adapter._research_article(candidate,detail,candidate.detail_url_observed)
        sha=hashlib.sha256(detail.encode()).hexdigest();(root/(sha+'.html')).write_text(detail,encoding='utf-8')
        report.update(candidate=candidate.model_dump(mode='json'),detail_sha256=sha)
        for anchor in body.select('a[href]'):
            url=urljoin(candidate.detail_url_observed,anchor['href'])
            if 'sharepoint.com' not in url:continue
            share_folder(url)
            data,metadata=acquire_public_workbook(url,driver._fetch,max_bytes=8*1024*1024)
            digest=hashlib.sha256(data.content).hexdigest();(root/(digest+'.xlsx')).write_bytes(data.content)
            previous=json.loads((base/'sharepoint-20260909T185055Z/download-receipt.json').read_text(encoding='utf-8'))
            report['documents'].append({'observed_title':anchor.get_text(' ',strip=True),'observed_url':url,'sha256':digest,'bytes':len(data.content),'metadata':metadata,'identical_to_previous':digest==previous['sha256']})
    finally:
        driver.close();report['driver_closed']=True;report['finished_at']=datetime.now(timezone.utc).isoformat()
        (root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'documents':len(report['documents']),'identical':[d['identical_to_previous'] for d in report['documents']],'driver_closed':report['driver_closed'],'report':str(root/'report.json')}))


if __name__=='__main__':main()
