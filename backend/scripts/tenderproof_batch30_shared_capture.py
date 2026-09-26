import asyncio,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit,urljoin
import httpx
from bs4 import BeautifulSoup,UnicodeDammit
from app.tenderproof.inventory import public_dns
from app.tenderproof.security import validate_destination
IDS=['exame_open','objetiva_open','cotec_open','quadrix_open','rbo_open','sigma_open','fafipa_open','omni_open','w2_open','consulpam_open','idcap_open']
ROOT=Path('tests/fixtures/tenderproof_batch30_shared')
async def main():
 ROOT.mkdir(parents=True,exist_ok=True);inv=json.loads(Path('../docs/tenderproof-sources-99.json').read_text(encoding='utf-8'));rows={r['source_type']:r for r in inv['sources']};records=[]
 async with httpx.AsyncClient(timeout=20,follow_redirects=False,trust_env=False,verify=True) as client:
  for sid in IDS:
   r=rows[sid];url=r['listing_urls'][0];allowed=tuple(r['allowed_probe_hosts'])
   if sid=='consulpam_open':url=r['listing_urls'][1]
   targets=[('listing',url)]
   for kind,url in targets:
    rec=dict(source=sid,kind=kind,url=url,observed_at=datetime.now(timezone.utc).isoformat())
    try:
     validate_destination(url,allowlist=allowed);await public_dns(urlsplit(url).hostname)
     async with client.stream('GET',url) as response:
      response.raise_for_status();body=bytearray()
      async for b in response.aiter_bytes():
       body.extend(b)
       if len(body)>2*1024*1024:raise ValueError('2MiB exceeded')
     name=f'{sid}-{kind}.html';(ROOT/name).write_bytes(body);rec.update(file=name,sha256=hashlib.sha256(body).hexdigest(),bytes=len(body),status=response.status_code)
     soup=BeautifulSoup(bytes(body),'lxml')
     if kind=='listing':
      details=list(dict.fromkeys(urljoin(url,a['href']) for a in soup.select('a[href]') if '/informacoes/' in a['href'] and urlsplit(urljoin(url,a['href'])).hostname==urlsplit(url).hostname))
      targets.extend([('detail',d) for d in details[:1]])
      rec['observed_tabs']=list(dict.fromkeys(urljoin(url,a['href']) for a in soup.select('a[href]') if urlsplit(urljoin(url,a['href'])).hostname==urlsplit(url).hostname and urlsplit(urljoin(url,a['href'])).path.startswith('/index/')))
      rec['detail_samples']=details[:5]
     else:
      rec['document_samples']=[{'url':urljoin(url,a['href']),'title':a.get_text(' ',strip=True)} for a in soup.select('a[href]') if '.pdf' in a['href'].lower()][:5]
     print(sid,kind,len(body),rec.get('observed_tabs'),rec.get('document_samples'),flush=True)
    except Exception as e:rec['error']=str(e);print(sid,kind,type(e).__name__,flush=True)
    records.append(rec)
 (ROOT/'manifest.json').write_text(json.dumps({'scope':'bounded real unauthenticated public HTTP, TLS verified, no browser','pages':records},ensure_ascii=False,indent=2),encoding='utf-8')
asyncio.run(main())
