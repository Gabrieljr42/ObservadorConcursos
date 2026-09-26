"""Bounded public official-page investigation; no source certification."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup, UnicodeDammit

FIXTURES = Path('tests/fixtures/tenderproof_batch99_regions')


def capture(row):
    result = {**row, 'observed_at':datetime.now(timezone.utc).isoformat(), 'tls_verified':True}
    try:
        with httpx.Client(timeout=25,follow_redirects=False,trust_env=False,headers={'User-Agent':'ObservadorDeConcursos/1.0','Accept':'text/html,application/xhtml+xml'}) as client:
            with client.stream('GET',row['url']) as response:
                chunks,size=[],0
                for chunk in response.iter_bytes():
                    size+=len(chunk)
                    if size>2*1024*1024:raise ValueError('HTML exceeds 2MiB')
                    chunks.append(chunk)
                raw=b''.join(chunks)
                sha=hashlib.sha256(raw).hexdigest()
                file=row['source']+'-'+hashlib.sha256(row['url'].encode()).hexdigest()[:8]+'-'+sha[:10]+'.html'
                (FIXTURES/file).write_bytes(raw)
                decoded=UnicodeDammit(raw,is_html=True)
                soup=BeautifulSoup(decoded.unicode_markup or '', 'html.parser')
                result.update(status=response.status_code,location=response.headers.get('location'),bytes=len(raw),sha256=sha,file=file,encoding=decoded.original_encoding,
                    title=soup.title.get_text(' ',strip=True) if soup.title else None,
                    links=[{'url':urljoin(row['url'],a['href']),'title':a.get_text(' ',strip=True)} for a in soup.select('a[href]')],
                    scripts=[urljoin(row['url'],a['src']) for a in soup.select('script[src]')])
    except Exception as exc:result.update(error_type=type(exc).__name__,error=str(exc)[:450])
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--targets',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    FIXTURES.mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(capture,json.loads(args.targets.read_text(encoding='utf8'))))
    args.output.write_text(json.dumps({'scope':'Read-only public official URLs; TLS verified; no redirects followed; 25s/2MiB; no PDF/browser/login/publication','pages':rows},ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps([{k:r.get(k) for k in ('source','status','title','location','error')} for r in rows],ensure_ascii=False,indent=2))
