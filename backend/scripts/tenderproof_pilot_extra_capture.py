import asyncio,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
import httpx
from app.tenderproof.inventory import public_dns
from app.tenderproof.security import validate_destination
from urllib.parse import urlsplit
async def main():
 root=Path('tests/fixtures/tenderproof_pilot'); m=json.loads((root/'manifest.json').read_text())
 async with httpx.AsyncClient(timeout=20,trust_env=False,verify=True,follow_redirects=False) as c:
  for sid,kind,u in [('fgv_open','detail','https://conhecimento.fgv.br/concursos/seplagrj'),('fgv_open','page2','https://conhecimento.fgv.br/concursos?page=1'),('funcern_selection','detail','https://funcern.br/concursos/concurso-equador-2026/'),('funcern_selection','page2','https://funcern.br/concursos/?page=2')]:
   validate_destination(u,allowlist=(urlsplit(u).hostname,));await public_dns(urlsplit(u).hostname)
   rec={'source':sid,'kind':kind,'url':u,'observed_at':datetime.now(timezone.utc).isoformat()}
   try:
    async with c.stream('GET',u) as r:
     r.raise_for_status();b=bytearray()
     async for chunk in r.aiter_bytes():
      b.extend(chunk)
      if len(b)>2*1024*1024:raise ValueError('2MiB exceeded')
    name=f'{sid}-{kind}.html';(root/name).write_bytes(b);rec.update(file=name,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),status=r.status_code)
   except Exception as e:rec['error']=str(e)
   m['pages'].append(rec);print(sid,kind,rec.get('bytes',rec.get('error')))
 (root/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
asyncio.run(main())
