"""Bounded public acquisition of the files observed in the SAD-linked folder.

This evidence run does not certify lazy-loading completeness or publish data.
"""
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, parse_qs, urljoin

import httpx

from app.tenderproof.facepe_listing import download_url_from_view
from app.tenderproof.http_driver import _public_dns
from app.tenderproof.processing import ProcessingService, ProcessingLimits


def main():
    root = Path('.tenderproof/product-completion/facepe')
    observed = json.loads((root / 'parsed-sad-and-drive.json').read_text(encoding='utf-8'))
    run = root / ('documents-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    run.mkdir()
    report = {'started_at': datetime.now(timezone.utc).isoformat(), 'items': [],
              'scope_complete': False, 'approved': False, 'published': False}
    deadline = time.monotonic() + 600
    request_count = 0
    byte_count = 0
    last = 0
    processor = ProcessingService(run / 'processing')

    def save():
        (run / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    def preserve(raw, suffix):
        digest = hashlib.sha256(raw).hexdigest()
        path = run / (digest + suffix)
        if path.exists():
            if path.read_bytes() != raw:
                raise ValueError('evidence_conflict')
        else:
            path.write_bytes(raw)
        return {'sha256': digest, 'file': path.name, 'bytes': len(raw)}

    def validate(url, identity, view):
        p = urlsplit(url)
        if p.scheme != 'https' or p.fragment:
            raise ValueError('invalid_destination')
        if view:
            if p.netloc != 'drive.google.com' or p.path != '/file/d/' + identity + '/view' or p.query:
                raise ValueError('viewer_identity_changed')
        elif (p.netloc != 'drive.usercontent.google.com' or p.path not in ('/uc', '/download')
              or parse_qs(p.query, keep_blank_values=True) != {'id': [identity], 'export': ['download']}):
            raise ValueError('download_identity_changed')

    with httpx.Client(timeout=20, follow_redirects=False, trust_env=False) as client:
        def fetch(url, identity, view):
            nonlocal request_count, byte_count, last
            chain = []
            for _ in range(3):
                validate(url, identity, view)
                _public_dns(urlsplit(url).hostname)
                if request_count >= 160 or time.monotonic() >= deadline:
                    raise ValueError('operational_request_or_time_limit')
                time.sleep(max(0, last + 1 - time.monotonic()))
                last = time.monotonic()
                request_count += 1
                chain.append(url)
                with client.stream('GET', url, timeout=min(20, max(.1, deadline-time.monotonic()))) as response:
                    if response.is_redirect:
                        url = urljoin(url, response.headers.get('location', ''))
                        continue
                    raw = bytearray()
                    for chunk in response.iter_bytes():
                        raw.extend(chunk)
                        byte_count += len(chunk)
                        if len(raw) > (4 if view else 20) * 1024 * 1024 or byte_count > 150 * 1024 * 1024:
                            raise ValueError('operational_byte_limit')
                    evidence = preserve(bytes(raw), '.html' if view or not raw.startswith(b'%PDF-') else '.pdf')
                    evidence.update(url=url, chain=chain, status=response.status_code)
                    return bytes(raw), evidence
            raise ValueError('redirect_limit')

        for item in observed['folder']['items']:
            result = {'observed': item}
            report['items'].append(result)
            try:
                if not re.fullmatch(r'[A-Za-z0-9_-]{10,100}', item['file_id']):
                    raise ValueError('invalid_file_id')
                html, result['viewer'] = fetch(item['view_url'], item['file_id'], True)
                if result['viewer']['status'] != 200:
                    raise ValueError('viewer_http_error')
                download = download_url_from_view(html.decode('utf-8-sig'), item['file_id'])
                pdf, result['document'] = fetch(download, item['file_id'], False)
                if result['document']['status'] != 200 or not pdf.startswith(b'%PDF-'):
                    raise ValueError('pdf_not_acquired')
                job = processor.enqueue('facepe-current-documents', pdf, limits=ProcessingLimits(
                    max_bytes=20*1024*1024, max_pages=100, max_output_bytes=2*1024*1024))
                job = processor.execute(job['id'], 'facepe-current-documents')
                result['processing'] = {'id': job['id'], 'state': job['state'], 'error': job.get('error')}
                if job['state'] == 'succeeded':
                    pages = processor.result(job['id'], 'facepe-current-documents')
                    result['extraction'] = preserve(json.dumps(pages, ensure_ascii=False).encode('utf-8'), '-pages.json')
                    result['total_pages'] = pages['total_pages']
                    result['pages_with_text'] = sum(bool(x['text'].strip()) for x in pages['pages'])
            except Exception as exc:
                result['error'] = type(exc).__name__ + ': ' + str(exc)
            report.update(requests=request_count, received_bytes=byte_count)
            save()
            print(json.dumps({'item': len(report['items']), 'name': item['name'],
                              'pages': result.get('total_pages'), 'error': result.get('error')}, ensure_ascii=False), flush=True)
            if time.monotonic() >= deadline or request_count >= 160:
                break
    report.update(finished_at=datetime.now(timezone.utc).isoformat(),
                  visible_items_attempted=len(report['items']), visible_items_observed=len(observed['folder']['items']))
    save()
    print(json.dumps({'report': str(run/'report.json')}), flush=True)


if __name__ == '__main__':
    main()
