"""Bounded dated public HTTP captures; no redirects without a verified next call."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import ipaddress
import json
from pathlib import Path
import socket
import re
from urllib.parse import urlsplit,urlunsplit,parse_qsl
import httpx
from bs4 import BeautifulSoup,UnicodeDammit

ROOT=Path(__file__).resolve().parents[1]
FIXTURES=ROOT/'tests/fixtures/tenderproof_batch60_major'
URLS={'ibam':'https://www.ibam-concursos.org.br','fcc':'https://www.concursosfcc.com.br/concursoAndamento.html','cebraspe':'https://www.cebraspe.org.br/concursos/','cesgranrio':'https://www.cesgranrio.org.br/concursos/','avalia':'https://www2.avalia.org.br/concursos.jsp'}
MAX_JS_BYTES=2*1024*1024

def sanitize_json(value):
    if isinstance(value,dict):return {k:sanitize_json(v) for k,v in value.items()}
    if isinstance(value,list):return [sanitize_json(v) for v in value]
    if not isinstance(value,str):return value
    def clean(match):
        url=match.group();p=urlsplit(url)
        if any(k.lower() in ('sig','signature','awsaccesskeyid') or k.lower().startswith('x-amz-') for k,v in parse_qsl(p.query)):
            return urlunsplit((p.scheme,p.netloc,p.path,'',p.fragment))
        return url
    return re.sub(r'https?://[^\s\"\'<>]+',clean,value)

def fetch(pair):
    name,url=pair
    row={'name':name,'url':url,'observed_at':datetime.now(timezone.utc).isoformat()}
    try:
        parts=urlsplit(url)
        limit=MAX_JS_BYTES if parts.path.endswith('.js') else 2*1024*1024
        row['max_bytes']=limit
        if parts.scheme!='https' or parts.username or parts.password:raise ValueError('unsafe URL')
        if any(not ipaddress.ip_address(x[4][0]).is_global for x in socket.getaddrinfo(parts.hostname,443,type=socket.SOCK_STREAM)):raise ValueError('private DNS')
        with httpx.Client(timeout=25,follow_redirects=False,verify=True,trust_env=False,headers={'User-Agent':'Mozilla/5.0'}) as client:
            with client.stream('GET',url) as response:
                chunks=[];size=0
                for part in response.iter_bytes():
                    size+=len(part)
                    if size>limit:raise ValueError('configured byte limit exceeded')
                    chunks.append(part)
                raw=b''.join(chunks)
                is_js='javascript' in response.headers.get('content-type','') or parts.path.endswith('.js')
                is_json='application/json' in response.headers.get('content-type','')
                if is_json:content=json.dumps(sanitize_json(json.loads(raw)),ensure_ascii=False).encode('utf-8')
                elif is_js:content=raw
                else:
                    soup=BeautifulSoup(UnicodeDammit(raw,is_html=True).unicode_markup,'html.parser')
                    for node in soup.select('input[type=hidden]'):node.attrs.pop('value',None)
                    content=str(soup).encode('utf-8')
                path=FIXTURES/(name+('.js' if is_js else '.json' if is_json else '.html'));path.write_bytes(content)
                row.update(status=response.status_code,location=response.headers.get('location'),bytes=size,original_sha256=hashlib.sha256(raw).hexdigest(),fixture_sha256=hashlib.sha256(content).hexdigest(),file=path.name,format='public JSON; signed URL queries removed' if is_json else 'raw JavaScript' if is_js else 'decoded UTF8 HTML; hidden values removed')
    except Exception as exc:row.update(error=type(exc).__name__,reason=str(exc) if isinstance(exc,ValueError) else 'bounded acquisition failed')
    return row

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--url');p.add_argument('--name');p.add_argument('--phase',default='initial');p.add_argument('--max-js-mib',type=int,choices=[2,8],default=2);args=p.parse_args()
    MAX_JS_BYTES=args.max_js_mib*1024*1024
    FIXTURES.mkdir(parents=True,exist_ok=True)
    targets={args.name:args.url} if args.url else URLS
    rows=list(ThreadPoolExecutor(5).map(fetch,targets.items()))
    (FIXTURES/('manifest-'+args.phase+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(rows,ensure_ascii=False))
