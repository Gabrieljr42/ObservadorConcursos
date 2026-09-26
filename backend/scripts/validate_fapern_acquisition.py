"""Two bounded live acquisitions of an observed selection; not source acceptance."""
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from urllib.parse import unquote_plus
from app.tenderproof.http_driver import BoundedHTTPDriver
from app.tenderproof.security import TenderProofSettings


def main():
    root=Path('.tenderproof/product-completion/fapern');results=[]
    for attempt in (1,2):
        settings=TenderProofSettings()
        settings=replace(settings,limits=replace(settings.limits,max_navigations=80,
            max_download_bytes=45_000_000,total_timeout_s=240))
        driver=BoundedHTTPDriver('fapern_selection',settings)
        try:
            adapter=driver.adapter;url=adapter.listing_urls[0]
            body=driver.open_listing(url)
            (root/f'adapter-root-{attempt}.json').write_text(body,encoding='utf-8')
            page=adapter.parse_listing(body,url)
            year=next(u for u in page.next_urls if 'Editais 2026' in unquote_plus(u))
            body=driver.open_listing(year)
            (root/f'adapter-year-{attempt}.json').write_text(body,encoding='utf-8')
            page=adapter.parse_listing(body,year)
            detail=next(u for u in page.next_urls if 'PESQUISADORES EMPARN' in unquote_plus(u))
            body=driver.open_listing(detail);page=adapter.parse_listing(body,detail)
            assert len(page.candidates)==1
            candidate=page.candidates[0];driver.set_candidate(candidate)
            body=driver.open_detail(detail)
            (root/f'adapter-detail-{attempt}.json').write_text(body,encoding='utf-8')
            docs=adapter.documents(body,candidate);chosen=adapter.choose_document(docs)
            pdf=driver.download(chosen.url_requested,max_bytes=45_000_000)
            result={'attempt':attempt,'candidate':candidate.model_dump(mode='json'),
                'documents':[d.model_dump(mode='json') for d in docs],'selected':chosen.model_dump(mode='json'),
                'sha256':hashlib.sha256(pdf.content).hexdigest(),'bytes':len(pdf.content),'http_requests':driver.requests}
            results.append(result)
            (root/'adapter-repeated-acquisition.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps({'attempt':attempt,'documents':len(docs),'sha256':result['sha256'],'bytes':len(pdf.content)}),flush=True)
        finally:
            driver.close()
    assert results[0]['sha256']==results[1]['sha256']


if __name__=='__main__': main()
