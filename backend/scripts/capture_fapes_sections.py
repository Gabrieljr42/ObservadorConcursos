"""Read observed public FAPES section links; audit failures without inventing empty results."""
import hashlib
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tenderproof.fapes_panels import parse_file_panels, discover_sections


def main():
    root = Path(__file__).resolve().parents[1] / '.tenderproof/product-completion/fapes'
    args = argparse.ArgumentParser()
    args.add_argument('--previous-verification', type=Path)
    options = args.parse_args()
    output = root / datetime.now(timezone.utc).strftime('sections-%Y%m%dT%H%M%SZ')
    output.mkdir()

    def capture(url):
        record = {'url': url, 'observed_at': datetime.now(timezone.utc).isoformat()}
        try:
            with httpx.Client(timeout=20, follow_redirects=False, trust_env=False) as client:
                with client.stream('GET', url) as response:
                    record['status'] = response.status_code
                    response.raise_for_status()
                    body = bytearray()
                    for chunk in response.iter_bytes():
                        body.extend(chunk)
                        if len(body) > 4_000_000:
                            raise ValueError('section exceeds bounded 4 MB audit limit')
            digest = hashlib.sha256(body).hexdigest()
            (output / (digest + '.html')).write_bytes(body)
            html = body.decode('utf-8', errors='strict')
            record.update(sha256=digest, byte_len=len(body))
            parsed = BeautifulSoup(html, 'html.parser')
            record['headings'] = [h.get_text(' ', strip=True) for h in parsed.select('h1, h2, h3, .paneltitle-value')]
            record['navigation'] = [{'title': a.get_text(' ', strip=True), 'href': a['href']}
                for a in parsed.select('.pagination a[href], .pager a[href]')]
            try:
                panels = parse_file_panels(html)
                (output / (digest + '-panels.json')).write_text(json.dumps(panels, ensure_ascii=False, indent=2), encoding='utf-8')
                record['panels'] = [{'panel_id': p['panel_id'], 'title': p['title'], 'document_count': len(p['documents'])} for p in panels]
            except ValueError as exc:
                record['parsing_pending'] = str(exc)
        except Exception as exc:
            record['error'] = type(exc).__name__ + ': ' + str(exc)[:180]
        return record

    entry = capture('https://fapes.es.gov.br/editais')
    (output / 'entry.json').write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding='utf-8')
    if entry.get('error') or not entry.get('sha256'):
        raise ValueError('current official menu acquisition failed')
    urls = set(discover_sections((output / (entry['sha256'] + '.html')).read_text(encoding='utf-8')))
    if options.previous_verification:
        previous = json.loads(options.previous_verification.read_text(encoding='utf-8'))
        urls -= {r['url'] for r in previous if r.get('status') == 200 and r.get('sha256')}
    records = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        for record in executor.map(capture, sorted(urls)):
            records.append(record)
            (output / 'verification.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps(record, ensure_ascii=True), flush=True)
    print(str(output), flush=True)


if __name__ == '__main__':
    main()
