"""Bounded public captures for batch60 own/blocked portals; no adapter claims."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
from pathlib import Path
import socket
import sys
import time
from urllib.parse import urlsplit, urljoin
import httpx
from bs4 import BeautifulSoup, UnicodeDammit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.tenderproof.security import validate_destination

ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/'tests/fixtures/tenderproof_batch60_own'
DELEGATED={'fundep_open','facet_open','educapb_open','idib_open','jcm_open','ibam_open','fcc_open','cesgranrio_open','cebraspe_open','avalia_open'}

def fetch(item):
    source,url,label=item
    row={'source':source,'url':url,'kind':label,'observed_at':datetime.now(timezone.utc).isoformat()}
    try:
        host=urlsplit(url).hostname
        validate_destination(url,allowlist=(host,))
        if any(not ipaddress.ip_address(r[4][0]).is_global for r in socket.getaddrinfo(host,None,type=socket.SOCK_STREAM)):
            raise ValueError('non_public_dns')
        start=time.monotonic()
        headers={'User-Agent':'Mozilla/5.0','Accept':'text/html,application/json'}
        if source=='elo_open' and host=='api.gestaoselecoes.com.br':
            headers['X-TenantID']='eloassessoria'  # literal public component configuration
        with httpx.Client(timeout=25,verify=True,trust_env=False,follow_redirects=False,headers=headers) as client:
            with client.stream('GET',url) as response:
                raw=bytearray()
                for chunk in response.iter_bytes():
                    raw.extend(chunk)
                    if len(raw)>2097152 or time.monotonic()-start>25:raise ValueError('response_limit')
                encoding=UnicodeDammit(bytes(raw)).original_encoding
                soup=BeautifulSoup(bytes(raw),'lxml')
                file=f'{source}-{label}.html'
                (FIX/file).write_bytes(raw)
                links=[{'url':urljoin(url,a['href']),'title':a.get_text(' ',strip=True)[:200]} for a in soup.select('a[href]') if urlsplit(urljoin(url,a['href'])).scheme in ('http','https')]
                row.update(status=response.status_code,location=response.headers.get('location'),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),file=file,encoding=encoding,title=soup.title.get_text(' ',strip=True) if soup.title else None,links=links[:180],scripts=[urljoin(url,a['src']) for a in soup.select('script[src]')][:25])
    except Exception as exc:
        row['error_type']=type(exc).__name__
        row['error']=str(exc)[:250]
    return row

def main():
    FIX.mkdir(parents=True,exist_ok=True)
    plan=json.loads((ROOT.parent/'docs/tenderproof-rollout-plan.json').read_text(encoding='utf-8'))
    ids=set(next(b['sources'] for b in plan['batches'] if b['cumulative_sources']==60))-DELEGATED
    inventory=json.loads((ROOT.parent/'docs/tenderproof-phases11-13-probe.json').read_text(encoding='utf-8'))
    targets=[(s['source_type'],o.get('final_url',o['requested_url']),f'listing{i}') for s in inventory['sources'] if s['source_type'] in ids for i,o in enumerate(s['url_observations'])]
    phase='initial'
    if len(sys.argv)>1:
        phase=Path(sys.argv[1]).stem
        targets=[tuple(r) for r in json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))]
    with ThreadPoolExecutor(4) as pool:rows=list(pool.map(fetch,targets))
    report={'observed_at':datetime.now(timezone.utc).isoformat(),'scope':'Read-only observed URLs; TLS verified; redirects recorded, not followed; max2MiB25s; no PDFs or browser; not adapter certification.','pages':rows}
    (FIX/f'{phase}-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for r in rows:print(json.dumps({k:r.get(k) for k in ('source','kind','status','bytes','title','location','error_type')},ensure_ascii=True),flush=True)

if __name__=='__main__':main()
