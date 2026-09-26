"""Acquire every current FAPEPI listing target, preserving failures and raw pages."""
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import httpx
from app.tenderproof.fapepi_pages import LISTING, parse_listing, parse_detail, detail_url


def main():
    root = Path('.tenderproof/product-completion/fapepi') / datetime.now(timezone.utc).strftime('inventory-%Y%m%dT%H%M%SZ')
    root.mkdir(parents=True)
    report = {'documents': [], 'errors': [], 'source_integrated': False, 'published': False}
    def save():
        (root / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    with httpx.Client(timeout=20, trust_env=False, follow_redirects=False) as client:
        def fetch(url):
            with client.stream('GET', url) as response:
                response.raise_for_status()
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > 4 * 1024 * 1024:
                        raise ValueError('HTML excede 4 MiB')
            digest = hashlib.sha256(body).hexdigest()
            (root / (digest + '.html')).write_bytes(body)
            return body.decode('utf-8-sig'), digest
        html, digest = fetch(LISTING)
        listing = parse_listing(html)
        report.update(listing=listing, listing_sha256=digest)
        save()
        for item in listing['items']:
            url = item['url']
            try:
                detail_url(url)
                html, digest = fetch(url)
                parsed = parse_detail(html, url)
                report['documents'].append({'sha256': digest, **parsed})
            except Exception as exc:
                report['errors'].append({'url': url, 'error': type(exc).__name__ + ': ' + str(exc)})
            save()
            print(json.dumps({'processed': len(report['documents']) + len(report['errors']), 'total': len(listing['items']), 'errors': len(report['errors'])}), flush=True)
            time.sleep(1)
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    save()
    print(json.dumps({'report': str(root/'report.json'), 'details':len(report['documents']), 'errors':report['errors']}), flush=True)


if __name__ == '__main__':
    main()
