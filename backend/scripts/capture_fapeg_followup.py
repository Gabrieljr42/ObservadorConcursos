"""Follow the public summons address explicitly published in the FAPEG notice."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urljoin

import httpx
from bs4 import BeautifulSoup
from app.tenderproof.processing import extract_pages_isolated


def main():
    base=Path('.tenderproof/product-completion/fapeg')
    review=json.loads((base/'personnel-amendment-review.json').read_text(encoding='utf-8'))
    url=review['followup_notice']['observed_url']
    if not url.startswith('https://goias.gov.br/fapeg/') or urlsplit(url).query:raise ValueError('Unexpected notice destination')
    root=base/datetime.now(timezone.utc).strftime('followup-%Y%m%dT%H%M%SZ');root.mkdir()
    report={'url':url,'parent_notice_sha256':review['followup_notice']['sha256'],'documents':[],'pending_links':[],'source_integrated':False}
    def save():(root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with httpx.Client(timeout=30,follow_redirects=False,trust_env=False) as client:
        def fetch(url,limit,notice_redirect=False):
            with client.stream('GET',url) as response:
                if response.is_redirect:
                    target=urljoin(url,response.headers.get('location',''))
                    report.setdefault('redirects',[]).append({'from':url,'to':target,'status':response.status_code});save()
                    if notice_redirect and target=='https://goias.gov.br/comunicado/':
                        report['final_notice_url']=target
                        return fetch(target,limit)
                response.raise_for_status();raw=bytearray()
                for chunk in response.iter_bytes():
                    raw.extend(chunk)
                    if len(raw)>limit:raise ValueError('Byte limit')
            return bytes(raw)
        save()
        raw=fetch(url,8*1024*1024,notice_redirect=True);sha=hashlib.sha256(raw).hexdigest();(root/(sha+'.html')).write_bytes(raw)
        report['page_sha256']=sha
        soup=BeautifulSoup(raw,'html.parser')
        content=soup.select_one('article')
        if content is None:
            report['page_text']=soup.get_text(' ',strip=True);report['error']='Official article absent';save()
            print(str(root),flush=True);return
        text=content.get_text(' ',strip=True)
        report['article_text']=text
        report['links']=[{'title':a.get_text(' ',strip=True),'url':urljoin(url,a['href'])} for a in content.select('a[href]')]
        save();seen=set()
        for link in report['links']:
            u=link['url'];p=urlsplit(u)
            if u in seen:continue
            seen.add(u)
            if not re.search(r'\.(pdf|docx?|xlsx?|odt)$',p.path,re.I):continue
            if p.scheme!='https' or p.netloc!='goias.gov.br' or not p.path.startswith('/fapeg/wp-content/uploads/') or p.query or p.fragment:
                report['pending_links'].append(link);save();continue
            row={**link};report['documents'].append(row)
            try:
                data=fetch(u,30*1024*1024);digest=hashlib.sha256(data).hexdigest();ext=p.path.rsplit('.',1)[1].lower()
                (root/(digest+'.'+ext)).write_bytes(data);row.update(sha256=digest,bytes=len(data),format=ext)
                if ext=='pdf':
                    pages,total,processed,truncated,errors=extract_pages_isolated(data,artifact_id='fapeg-followup-'+digest,owner_id='fapeg-source-audit',max_bytes=30*1024*1024,max_pages=200)
                    (root/(digest+'-pages.json')).write_text(json.dumps([p.model_dump(mode='json') for p in pages],ensure_ascii=False),encoding='utf-8')
                    row.update(total_pages=total,processed_pages=processed,truncated=truncated,errors=errors)
                else:row['reading_pending']=True
            except Exception as exc:row['error']=type(exc).__name__+': '+str(exc)
            save();print(json.dumps({'document':link['title'],'pages':row.get('processed_pages'),'error':row.get('error')}),flush=True)
    report['finished_at']=datetime.now(timezone.utc).isoformat();save();print(str(root),flush=True)


if __name__=='__main__':main()
