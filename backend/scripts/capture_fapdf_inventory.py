"""Capture the official menu and its published leaves, preserving nested call ownership."""
import hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin,urlsplit
import httpx
from bs4 import BeautifulSoup

HOST='https://fap.df.gov.br'

def parse(raw,url):
    soup=BeautifulSoup(raw,'html.parser'); groups=[]; owned=set()
    for button in soup.select('.journal-content-article button[aria-controls]'):
        panel=soup.find(id=button['aria-controls'])
        if panel is None:raise ValueError('Missing panel')
        if panel.select('button[aria-controls]'):continue
        links=[]
        for a in panel.select('a[href]'):
            owned.add(id(a)); parent=a.find_parent(['p','li'])
            links.append({'url':urljoin(url,a['href']),'title':a.get_text(' ',strip=True),'context':parent.get_text(' ',strip=True) if parent else a.get_text(' ',strip=True)})
        groups.append({'title':button.get_text(' ',strip=True),'panel_id':button['aria-controls'],'links':links,'text':panel.get_text(' ',strip=True)})
    unassigned=[]
    for a in soup.select('.journal-content-article a[href]'):
        if id(a) not in owned:unassigned.append({'url':urljoin(url,a['href']),'title':a.get_text(' ',strip=True)})
    return {'groups':groups,'unassigned_links':unassigned}

def main():
    root=Path('.tenderproof/product-completion/fapdf')/datetime.now(timezone.utc).strftime('inventory-%Y%m%dT%H%M%SZ');root.mkdir()
    report={'pages':[],'errors':[],'source_integrated':False}
    def save():(root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with httpx.Client(timeout=25,trust_env=False,follow_redirects=False) as client:
        def get(url):
            p=urlsplit(url)
            if p.scheme!='https' or p.netloc!='fap.df.gov.br' or p.query or p.fragment:raise ValueError('Unexpected menu URL')
            with client.stream('GET',url) as r:
                r.raise_for_status();data=bytearray()
                for c in r.iter_bytes():
                    data.extend(c)
                    if len(data)>8*1024*1024:raise ValueError('HTML size limit')
            raw=bytes(data);sha=hashlib.sha256(raw).hexdigest();(root/(sha+'.html')).write_bytes(raw);return raw,sha
        raw,sha=get(HOST+'/');report['menu_sha256']=sha
        soup=BeautifulSoup(raw,'html.parser');menu=next(a.parent for a in soup.select('a[href]') if a['href']==HOST+'/category/editais')
        leaves={urljoin(HOST,a['href']):a.get_text(' ',strip=True) for a in menu.select('li a[href]') if not a.parent.find('ul',recursive=False)}
        report['leaves']=leaves;save()
        for url,title in leaves.items():
            try:
                raw,sha=get(url);report['pages'].append({'url':url,'title':title,'sha256':sha,**parse(raw,url)})
            except Exception as e:report['errors'].append({'url':url,'error':type(e).__name__+': '+str(e)})
            save();print(json.dumps({'pages':len(report['pages']),'errors':len(report['errors'])}),flush=True);time.sleep(1)
    report['finished_at']=datetime.now(timezone.utc).isoformat();save();print(root,flush=True)

if __name__=='__main__':main()
