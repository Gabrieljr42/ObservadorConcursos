"""Bounded public address inspection for every currently missing adapter.

This is evidence gathering, not a claim of integration or source emptiness.
Redirect targets are recorded for inspection and are never followed blindly.
"""
import json
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin,urlsplit
import sys
import httpx
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend'))
from app.tenderproof.source_adapters import SOURCE_ADAPTERS
from app.tenderproof.security import validate_destination
from app.tenderproof.http_driver import _public_dns


def inspect(source,root):
    rows=[]
    for index,url in enumerate(source['listing_urls']):
        row={'source':source['source_type'],'url':url,'checked_at':datetime.now(timezone.utc).isoformat()}
        try:
            host=urlsplit(url).hostname
            validate_destination(url,allowlist=(host,));_public_dns(host)
            started=time.monotonic()
            with httpx.Client(timeout=12,follow_redirects=False,trust_env=False) as client:
                with client.stream('GET',url) as response:
                    content=bytearray()
                    for chunk in response.iter_bytes():
                        content.extend(chunk)
                        if len(content)>2*1024*1024 or time.monotonic()-started>25:
                            raise ValueError('inspection byte/time limit reached')
                    name=f"{source['source_type']}-{index}.html"
                    (root/name).write_bytes(content)
                    row.update(status=response.status_code,file=name,sha256=hashlib.sha256(content).hexdigest(),bytes=len(content))
                    if response.is_redirect:row['redirect']=urljoin(url,response.headers.get('location',''))
                    soup=BeautifulSoup(bytes(content),'lxml')
                    row['title']=soup.title.get_text(' ',strip=True) if soup.title else None
                    row['links']=[{'text':a.get_text(' ',strip=True),'url':urljoin(url,a['href'])} for a in soup.select('a[href]')]
                    row['scripts']=[urljoin(url,s['src']) for s in soup.select('script[src]')]
        except Exception as error:
            row['error_type']=type(error).__name__;row['error']=str(error)[:250]
        rows.append(row)
    return rows


def main():
    inventory=json.loads((ROOT/'docs/tenderproof-sources-99.json').read_text(encoding='utf-8'))['sources']
    missing=[s for s in inventory if s['source_type'] not in SOURCE_ADAPTERS]
    root=ROOT/'backend/.tenderproof/product-completion/missing-sources'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    root.mkdir(parents=True,exist_ok=False);rows=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(inspect,source,root) for source in missing]
        for future in as_completed(futures):
            results=future.result();rows.extend(results)
            (root/'report.json').write_text(json.dumps({'missing_sources':len(missing),'pages':rows},ensure_ascii=False,indent=2),encoding='utf-8')
            for row in results:print(json.dumps({k:row[k] for k in ('source','status','error_type','redirect','title') if k in row}),flush=True)
    print(json.dumps({'report':str(root/'report.json'),'sources':len(missing),'requests':len(rows)}),flush=True)


if __name__=='__main__':main()
