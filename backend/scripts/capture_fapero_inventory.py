"""Traverse observed FAPERO annual links; exclude the state-wide service directory."""
import hashlib,json,re,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin,urlsplit
import httpx
from bs4 import BeautifulSoup

ROOT='https://rondonia.ro.gov.br/fapero/'

def annual_links(html):
    s=BeautifulSoup(html,'html.parser');links={}
    for a in s.select('a[href]'):
        u=urljoin(ROOT,a['href'])
        if re.fullmatch(r'https://rondonia.ro.gov.br/fapero/publicacoes/\d{4}-\d+/(?:editais/)?',u):links[u]=a.get_text(' ',strip=True)
    if not links:raise ValueError('Annual menu missing')
    return links

def parse(html,url):
    s=BeautifulSoup(html,'html.parser');body=s.select_one('.conteudo-pagina-full .entry, .conteudo-pagina .entry')
    if body is None:raise ValueError('Source article missing')
    groups=[];owned=set()
    for section in body.select('section'):
        heading=section.find(['h2','h3'])
        if heading is None:continue
        links=[]
        for a in section.select('a[href]'):
            owned.add(id(a));links.append({'url':urljoin(url,a['href']),'title':a.get_text(' ',strip=True)})
        groups.append({'title':heading.get_text(' ',strip=True),'links':links,'text':section.get_text(' ',strip=True)})
    unassigned=[{'url':urljoin(url,a['href']),'title':a.get_text(' ',strip=True)} for a in body.select('a[href]') if id(a) not in owned]
    return {'groups':groups,'unassigned_links':unassigned,'text':body.get_text(' ',strip=True)}

def main():
    root=Path('.tenderproof/product-completion/fapero')/datetime.now(timezone.utc).strftime('inventory-%Y%m%dT%H%M%SZ');root.mkdir()
    report={'pages':[],'errors':[],'source_integrated':False}
    def save():(root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with httpx.Client(timeout=25,trust_env=False,follow_redirects=False) as c:
        def get(url):
            with c.stream('GET',url) as r:
                r.raise_for_status();raw=bytearray()
                for part in r.iter_bytes():
                    raw.extend(part)
                    if len(raw)>4*1024*1024:raise ValueError('HTML limit')
            raw=bytes(raw);sha=hashlib.sha256(raw).hexdigest();(root/(sha+'.html')).write_bytes(raw);return raw,sha
        raw,sha=get(ROOT);report.update(menu_sha256=sha,annual_links=annual_links(raw))
        for url,label in report['annual_links'].items():
            try:
                raw,sha=get(url);report['pages'].append({'url':url,'menu_label':label,'sha256':sha,**parse(raw,url)})
            except Exception as e:report['errors'].append({'url':url,'error':type(e).__name__+': '+str(e)})
            save();print(json.dumps({'pages':len(report['pages']),'errors':len(report['errors'])}),flush=True);time.sleep(1)
    report['finished_at']=datetime.now(timezone.utc).isoformat();save();print(root,flush=True)

if __name__=='__main__':main()
