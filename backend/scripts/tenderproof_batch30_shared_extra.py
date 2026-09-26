import asyncio,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit
import httpx
from app.tenderproof.inventory import public_dns
from app.tenderproof.security import validate_destination
async def main():
 root=Path('tests/fixtures/tenderproof_batch30_shared');m=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
 inv=json.loads(Path('../docs/tenderproof-sources-99.json').read_text(encoding='utf-8'));c=next(r for r in inv['sources'] if r['source_type']=='consulpam_open')
 ids=next(p for p in m['pages'] if p['source']=='idcap_open' and p['kind']=='listing')['detail_samples']
 urls=[('consulpam_open','own-listing',c['listing_urls'][0]),('consulpam_open','own-detail',c['detail_observations'][0]['final_url']),('consulpam_open','net-page1','https://consulpam.selecao.net.br/index/1/'),('w2_open','page2','https://www.w2consultores.com.br/index/todos/?&ord=&dir=&pg=2&q=&pp=10')]+[('idcap_open','detail-alt'+str(i),u) for i,u in enumerate(ids[1:3])]
 async with httpx.AsyncClient(timeout=20,trust_env=False,verify=True,follow_redirects=False) as client:
  for sid,kind,u in urls:
   rec=dict(source=sid,kind=kind,url=u,observed_at=datetime.now(timezone.utc).isoformat());validate_destination(u,allowlist=(urlsplit(u).hostname,));await public_dns(urlsplit(u).hostname)
   try:
    async with client.stream('GET',u) as r:
     r.raise_for_status();body=bytearray()
     async for b in r.aiter_bytes():
      body.extend(b)
      if len(body)>2*1024*1024:raise ValueError('2MiB exceeded')
    name=f'{sid}-{kind}.html';(root/name).write_bytes(body);rec.update(file=name,status=r.status_code,bytes=len(body),sha256=hashlib.sha256(body).hexdigest());print(sid,kind,len(body),flush=True)
   except Exception as e:rec['error']=str(e)
   m['pages'].append(rec)
 (root/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
asyncio.run(main())
