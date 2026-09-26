"""Traverse the live adapter graph and exercise document acquisition; no publication."""
import hashlib
import json
import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from app.tenderproof.http_driver import BoundedHTTPDriver
from app.tenderproof.security import TenderProofSettings


def main():
    root = Path('.tenderproof/product-completion/fapesq') / ('adapter-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    root.mkdir(parents=True)
    settings = TenderProofSettings()
    settings = replace(settings, limits=replace(settings.limits, max_navigations=100, total_timeout_s=300, max_download_bytes=30_000_000))
    driver = BoundedHTTPDriver('fapesq_selection', settings)
    report = {'pages': [], 'errors': [], 'detail_attempts': [], 'source_integrated': False, 'published': False}
    def save():
        (root / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    def preserve(url, body):
        name = hashlib.sha256(url.encode()).hexdigest() + '.json'
        (root / name).write_text(body, encoding='utf-8')
        return {'file': name, 'sha256': hashlib.sha256(body.encode()).hexdigest()}
    try:
        adapter = driver.adapter
        pending = list(adapter.listing_urls)
        seen = set()
        candidates = {}
        while pending:
            url = pending.pop(0)
            if url in seen:
                continue
            seen.add(url)
            try:
                body = driver.open_listing(url)
                page = adapter.parse_listing(body, url)
                report['pages'].append({'url': url, **preserve(url, body), 'count': len(page.candidates),
                    'truncated': page.truncated, 'diagnostics': page.diagnostics, 'next_urls': page.next_urls,
                    'terminal_evidence': page.terminal_evidence})
                pending.extend(page.next_urls)
                candidates.update({c.detail_url_observed: c for c in page.candidates})
            except Exception as exc:
                report['errors'].append({'url': url, 'error': type(exc).__name__ + ': ' + str(exc)})
            save()
            time.sleep(1)
        report['unique_candidates'] = len(candidates)
        # Bounded acceptance exercise only; the graph above is not sampled.
        for candidate in list(candidates.values())[:5]:
            row = {'url': candidate.detail_url_observed}
            report['detail_attempts'].append(row)
            try:
                driver.set_candidate(candidate)
                body = driver.open_detail(candidate.detail_url_observed)
                row.update(preserve(candidate.detail_url_observed, body))
                docs = adapter.documents(body, candidate)
                row['documents'] = [d.model_dump(mode='json') for d in docs]
                chosen = adapter.choose_document(docs)
                result = driver.download(chosen.url_requested, max_bytes=30_000_000)
                digest = hashlib.sha256(result.content).hexdigest()
                (root / (digest + '.pdf')).write_bytes(result.content)
                row.update(selected=chosen.model_dump(mode='json'), pdf_sha256=digest, bytes=len(result.content))
                save()
                break
            except Exception as exc:
                row['error'] = type(exc).__name__ + ': ' + str(exc)
                save()
        report['http_requests'] = driver.requests
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        save()
    finally:
        driver.close()
    print(json.dumps({'report': str(root / 'report.json'), 'pages': len(report['pages']),
        'candidates': report.get('unique_candidates'), 'errors': report['errors'],
        'details': [{k: v for k, v in row.items() if k not in ('documents', 'selected')} for row in report['detail_attempts']]}), flush=True)


if __name__ == '__main__':
    main()
