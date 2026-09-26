"""Bounded official observation for IDECAN and Aguia; raw public HTML, no browser."""
import asyncio
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
from urllib.parse import urlsplit, urljoin
import httpx
from bs4 import BeautifulSoup

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.tenderproof.inventory import public_dns
from app.tenderproof.security import validate_destination

OUTPUT=Path('tests/fixtures/tenderproof_batch30_edital')
SOURCES={'idecan_open':'https://portal.concursos.idecan.org.br/edital/index/abertos',
         'aguia_open':'https://portal.institutoaguia.org.br/edital'}


async def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    records=[]
    async with httpx.AsyncClient(timeout=12,follow_redirects=False,trust_env=False,verify=True) as client:
        for source,listing in SOURCES.items():
            urls=[listing]
            for index,url in enumerate(urls):
                record={'source':source,'url':url,'observed_at':datetime.now(timezone.utc).isoformat(),'kind':'listing' if index==0 else 'detail'}
                try:
                    validate_destination(url,allowlist=(urlsplit(listing).hostname,))
                    await public_dns(urlsplit(url).hostname)
                    async with client.stream('GET',url) as response:
                        response.raise_for_status()
                        chunks=[];size=0
                        async for chunk in response.aiter_bytes():
                            size+=len(chunk)
                            if size>2*1024*1024:raise ValueError('response exceeds 2 MiB')
                            chunks.append(chunk)
                    raw=b''.join(chunks)
                    name=f'{source}-{index}.html'
                    (OUTPUT/name).write_bytes(raw)
                    record.update(file=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),status=response.status_code)
                    soup=BeautifulSoup(raw,'lxml')
                    links=[{'label':a.get_text(' ',strip=True),'url':urljoin(url,a['href'])} for a in soup.select('a[href]')]
                    if index==0:
                        details=list(dict.fromkeys(a['url'] for a in links if urlsplit(a['url']).hostname==urlsplit(listing).hostname and '/edital/ver/' in a['url']))
                        urls.extend(details[:3])
                        record['observed_tabs']=[a for a in links if '/edital' in a['url'] and '/ver/' not in a['url']]
                    record['documents']=[a for a in links if '.pdf' in a['url'].lower()]
                    print(source,index,'docs',len(record['documents']),[a['url'] for a in record['documents'][:4]],flush=True)
                except Exception as exc:
                    record['error']=type(exc).__name__
                records.append(record)
    (OUTPUT/'manifest.json').write_text(json.dumps({'provenance':'official bounded HTTP capture; no PDF bytes or complete coverage validated','pages':records},ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':asyncio.run(main())
