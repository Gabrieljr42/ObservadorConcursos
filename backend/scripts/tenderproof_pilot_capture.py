import asyncio, hashlib, json
from pathlib import Path
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup
from app.tenderproof.inventory import public_dns
from app.tenderproof.security import validate_destination
from urllib.parse import urlsplit, urljoin

OUT=Path('tests/fixtures/tenderproof_pilot')
IDS=['access_open','abcp_open','avancasp_open','ibade_open','fenix_open','legalle_open','fgv_open','funcern_selection']
async def main():
 OUT.mkdir(parents=True,exist_ok=True)
 inv=json.loads(Path('../docs/tenderproof-sources-99.json').read_text(encoding='utf-8'))
 rows={r['source_type']:r for r in inv['sources']}
 result=[]
 async with httpx.AsyncClient(timeout=20,follow_redirects=False,trust_env=False,verify=True) as c:
  for sid in IDS:
   row=rows[sid]; urls=row['listing_urls'][:1]+[d['final_url'] for d in row.get('detail_observations',[])[:1]]
   for i,url in enumerate(urls):
    rec={'source':sid,'kind':'listing' if i==0 else 'detail','url':url,'observed_at':datetime.now(timezone.utc).isoformat()}
    try:
     validate_destination(url,allowlist=tuple(row['allowed_probe_hosts'])); await public_dns(urlsplit(url).hostname)
     async with c.stream('GET',url) as r:
      r.raise_for_status(); data=bytearray()
      async for chunk in r.aiter_bytes():
       data.extend(chunk)
       if len(data)>2*1024*1024: raise ValueError('2 MiB exceeded')
     name=f'{sid}-{rec["kind"]}.html'; (OUT/name).write_bytes(data)
     rec.update(file=name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),status=r.status_code)
     soup=BeautifulSoup(bytes(data),'lxml')
     print(sid,rec['kind'],len(data))
     if sid in ['fgv_open','funcern_selection']:
      for a in soup.select('a[href]'):
       u=urljoin(url,a['href']); label=a.get_text(' ',strip=True)
       if ('concurso' in u or 'seletiv' in u or 'edital' in u):print(label[:150],u)
    except Exception as e:rec['error']=type(e).__name__+': '+str(e)
    result.append(rec)
 (OUT/'manifest.json').write_text(json.dumps({'provenance':'bounded unauthenticated public HTTP; raw HTML; no browser; no complete coverage claim','pages':result},ensure_ascii=False,indent=2),encoding='utf-8')
asyncio.run(main())

