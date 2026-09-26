"""Repeat the live FAPES menu graph through the production HTTP adapter."""
import hashlib
import json
import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from app.tenderproof.http_driver import BoundedHTTPDriver
from app.tenderproof.security import TenderProofSettings


def main():
    root = Path('.tenderproof/product-completion/fapes') / datetime.now(timezone.utc).strftime('adapter-%Y%m%dT%H%M%SZ')
    root.mkdir(parents=True)
    settings = TenderProofSettings()
    settings = replace(settings, limits=replace(settings.limits, max_navigations=150, total_timeout_s=600, max_download_bytes=30_000_000))
    driver = BoundedHTTPDriver('fapes_selection', settings)
    report = {'pages': [], 'errors': [], 'manifests': [], 'source_integrated': False, 'published': False}
    def save():
        (root / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    try:
        adapter = driver.adapter
        pending, seen = list(adapter.listing_urls), set()
        while pending:
            url = pending.pop(0)
            if url in seen:
                continue
            seen.add(url)
            try:
                body = driver.open_listing(url)
                digest = hashlib.sha256(body.encode()).hexdigest()
                (root / (digest + '.json')).write_text(body, encoding='utf-8')
                page = adapter.parse_listing(body, url)
                report['pages'].append({'url': url, 'sha256': digest, 'count': len(page.candidates),
                    'truncated': page.truncated, 'diagnostics': page.diagnostics})
                pending.extend(page.next_urls)
                for candidate in page.candidates:
                    row = {'candidate': candidate.model_dump(mode='json')}
                    report['manifests'].append(row)
                    try:
                        adapter.confirm_identity(candidate, body, candidate.detail_url_observed)
                        docs = adapter.documents(body, candidate)
                        row['documents'] = [d.model_dump(mode='json') for d in docs]
                        row['original'] = adapter.choose_document(docs).url_requested
                    except ValueError as exc:
                        row['review_pending'] = str(exc)
            except Exception as exc:
                report['errors'].append({'url': url, 'error': type(exc).__name__ + ': ' + str(exc)})
            save()
            time.sleep(1)
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        report['requests'] = driver.requests
        save()
    finally:
        driver.close()
    print(json.dumps({'report': str(root / 'report.json'), 'pages': len(report['pages']),
        'calls': len(report['manifests']), 'originals': sum('original' in r for r in report['manifests']),
        'errors': report['errors']}), flush=True)


if __name__ == '__main__':
    main()
