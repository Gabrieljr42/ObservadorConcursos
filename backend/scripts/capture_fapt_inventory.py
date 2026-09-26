"""Traverse FAPT's published edital graph and preserve document links with their context."""
import hashlib,json,time,re
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin,urlsplit
import httpx
from bs4 import BeautifulSoup

HOST='https://www.to.gov.br'
LISTING=HOST+'/fapt/'

def page_url(url):
    p=urlsplit(url)
    if p.scheme not in ('http','https') or p.netloc!='www.to.gov.br' or p.query or p.fragment or not re.fullmatch(r'/fapt/(?:[a-z0-9-]+/[a-z0-9]+)?',p.path):raise ValueError('FAPT page boundary')
    return 'https://'+p.netloc+p.path

def parse(raw,url):
    s=BeautifulSoup(raw,'html.parser');body=s.select_one('.page_main_content');h=s.select_one('.page_headline h1')
    if body is None or h is None:raise ValueError('FAPT content missing')
    children={};docs=[];pending=[]
    for a in body.select('a[href]'):
        title=a.get_text(' ',strip=True)
        for icon in a.select('i'):icon.decompose()
        title=a.get_text(' ',strip=True);target=urljoin(url,a['href'])
        if a['href'].startswith(('#','mailto:','tel:')):continue
        if re.fullmatch(r'https://central.to.gov.br/download/[0-9]+',target):
            docs.append({'title':title,'url':target});continue
        try:children[page_url(target)]=title
        except ValueError:pending.append({'url':target,'title':title})
    return {'title':h.get_text(' ',strip=True),'children':children,'documents':docs,'pending_links':pending,'text':body.get_text(' ',strip=True)}

def main():
    root=Path('.tenderproof/product-completion/fapt')/datetime.now(timezone.utc).strftime('inventory-%Y%m%dT%H%M%SZ');root.mkdir()
    report={'pages':[],'errors':[],'source_integrated':False}
    def save():(root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with httpx.Client(timeout=25,trust_env=False,follow_redirects=False) as client:
        def get(url):
            with client.stream('GET',url) as r:
                r.raise_for_status();raw=bytearray()
                for c in r.iter_bytes():
                    raw.extend(c)
                    if len(raw)>4*1024*1024:raise ValueError('HTML limit')
            raw=bytes(raw);sha=hashlib.sha256(raw).hexdigest();(root/(sha+'.html')).write_bytes(raw);return raw,sha
        raw,sha=get(LISTING);s=BeautifulSoup(raw,'html.parser');seeds={}
        for a in s.select('a[href]'):
            if any(t in (a.get_text(' ',strip=True)).lower() for t in ['editais','edital']):
                try:seeds[page_url(urljoin(LISTING,a['href']))]=a.get_text(' ',strip=True)
                except ValueError:pass
        report.update(listing_sha256=sha,seeds=seeds);pending=list(seeds);seen=set()
        while pending:
            url=pending.pop(0)
            if url in seen:continue
            if len(seen)>=500:raise ValueError('Graph limit')
            seen.add(url)
            try:
                raw,sha=get(url);parsed=parse(raw,url);report['pages'].append({'url':url,'sha256':sha,**parsed});pending.extend(parsed['children'])
            except Exception as e:report['errors'].append({'url':url,'error':type(e).__name__+': '+str(e)})
            save();print(json.dumps({'pages':len(report['pages']),'pending':len(pending),'errors':len(report['errors'])}),flush=True);time.sleep(1)
    report['finished_at']=datetime.now(timezone.utc).isoformat();save();print(root,flush=True)

if __name__=='__main__':main()
