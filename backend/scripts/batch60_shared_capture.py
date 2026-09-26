"""Bounded public HTTP capture of URLs already observed in the source inventory."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin, urlsplit
import httpx
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1] / 'tests/fixtures/tenderproof_batch60_shared'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('name')
    parser.add_argument('url')
    args = parser.parse_args()
    assert args.url.startswith('https://')
    ROOT.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=25, follow_redirects=False) as client:
        with client.stream('GET', args.url) as response:
            body = bytearray()
            for chunk in response.iter_bytes():
                body.extend(chunk)
                if len(body) > 2 * 1024 * 1024:
                    raise ValueError('page exceeds2MiB')
            encoding = response.encoding or 'utf-8'
            decoded = body.decode(encoding, errors='strict')
            # Some Selecao portals misdeclare ISO although actual bytes are UTF8.
            if encoding.lower() in ('iso-8859-1', 'latin-1', 'windows-1252'):
                try:
                    decoded = body.decode('utf-8', errors='strict')
                    encoding = 'utf-8 (valid bytes override declared legacy charset)'
                except UnicodeError:
                    pass
            content = decoded.encode('utf-8')
            filename = args.name + '.html'
            (ROOT / filename).write_bytes(content)
            record = dict(url=args.url, observed_at=datetime.now(timezone.utc).isoformat(), status=response.status_code,
                redirect=response.headers.get('location'), bytes=len(body), encoding=encoding,
                raw_sha256=hashlib.sha256(body).hexdigest(), fixture_sha256=hashlib.sha256(content).hexdigest(), file=filename)
            (ROOT / (args.name + '.json')).write_text(json.dumps(record, indent=2), encoding='utf-8')
            soup = BeautifulSoup(decoded, 'lxml')
            links = [(a.get_text(' ',strip=True)[:90], urljoin(args.url,a['href'])) for a in soup.select('a[href]')]
            print(json.dumps(record))
            print(json.dumps(links, ensure_ascii=True))
