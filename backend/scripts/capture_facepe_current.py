"""Repeat FACEPE discovery through the registered HTTP adapter, preserving evidence."""
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from app.tenderproof.http_driver import BoundedHTTPDriver
from app.tenderproof.security import TenderProofLimits, TenderProofSettings
from app.tenderproof.source_adapters import get_source_adapter


def main():
    adapter = get_source_adapter('facepe_selection')
    root = Path('.tenderproof/product-completion/facepe') / ('adapter-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    root.mkdir()
    report = {'pages': [], 'details': [], 'errors': [], 'scope_complete': False, 'published': False}
    driver = BoundedHTTPDriver(adapter.source, TenderProofSettings(allowlist_hosts=adapter.allowed_hosts,
        limits=TenderProofLimits(max_navigations=50, total_timeout_s=180, max_candidates=1000)))
    last = [0.0]
    def gap():
        time.sleep(max(0, last[0] + 1 - time.monotonic()))
        last[0] = time.monotonic()
    driver.request_guard = gap
    def save():
        (root/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    def preserve(raw, suffix):
        h = hashlib.sha256(raw).hexdigest()
        path = root/(h+suffix)
        if not path.exists():
            path.write_bytes(raw)
        elif path.read_bytes() != raw:
            raise ValueError('evidence_conflict')
        return {'sha256': h, 'file': path.name, 'bytes': len(raw)}
    pending = list(adapter.listing_urls)
    seen = set()
    candidates = {}
    try:
        while pending:
            url = pending.pop(0)
            if url in seen:
                continue
            html = driver.open_listing(url)
            page = adapter.parse_listing(html, url, 1000)
            seen.add(url)
            report['pages'].append({'url': url, **preserve(html.encode('utf-8'), '.html'),
                                   'next_urls': page.next_urls, 'candidates': len(page.candidates),
                                   'truncated': page.truncated, 'terminal_evidence': page.terminal_evidence})
            for c in page.candidates:
                candidates[c.external_id] = c
            pending.extend(x for x in page.next_urls if x not in seen and x not in pending)
            save()
            if page.truncated:
                raise ValueError('candidate_limit')
        for candidate in candidates.values():
            item = {'candidate': candidate.model_dump(mode='json')}
            report['details'].append(item)
            try:
                html = driver.open_detail(candidate.detail_url_observed)
                item['detail'] = preserve(html.encode('utf-8'), '.json')
                documents = adapter.documents(html, candidate)
                item['documents'] = [d.model_dump(mode='json') for d in documents]
                chosen = adapter.choose_document(documents)
                pdf = driver.download(chosen.url_requested, max_bytes=30*1024*1024)
                item['original'] = {**preserve(pdf.content, '.pdf'), 'url_final': pdf.url_final}
            except Exception as exc:
                item['error'] = type(exc).__name__ + ': ' + str(exc)
            save()
    except Exception as exc:
        report['errors'].append(type(exc).__name__ + ': ' + str(exc))
    finally:
        driver.close()
        report.update(requests=driver.requests, remaining_cursors=pending,
                      finished_at=datetime.now(timezone.utc).isoformat())
        save()
    print(json.dumps({'report': str(root/'report.json'), 'pages': len(report['pages']),
                      'candidates': len(candidates), 'errors': report['errors'],
                      'details': [{'documents': len(x.get('documents', [])), 'error': x.get('error')} for x in report['details']]}))


if __name__ == '__main__':
    main()
