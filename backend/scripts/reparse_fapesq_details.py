"""Rebuild manifests from hash-verified receipts without rewriting acquisition evidence."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from app.tenderproof.fapesq_detail import parse_detail


def main():
    base = Path('.tenderproof/product-completion/fapesq')
    acquisition = json.loads((base / 'detail-inventory-summary.json').read_text(encoding='utf-8'))
    output = Path(acquisition['output'])
    results = []
    for receipt in sorted(output.glob('*.json')):
        row = json.loads(receipt.read_text(encoding='utf-8'))
        result = {'url': row['url'], 'receipt': str(receipt), 'acquisition_error': row.get('error')}
        try:
            if row.get('status') != 200:
                raise ValueError('acquisition did not return HTTP 200')
            file = output / row['file']
            if file.resolve().parent != output.resolve():
                raise ValueError('receipt file outside acquisition directory')
            raw = file.read_bytes()
            if hashlib.sha256(raw).hexdigest() != row['sha256']:
                raise ValueError('acquisition hash mismatch')
            result['sha256'] = row['sha256']
            result['manifest'] = parse_detail(raw.decode('utf-8'), row['url'])
        except Exception as exc:
            result['error'] = type(exc).__name__ + ': ' + str(exc)
        results.append(result)
    manifests = [r['manifest'] for r in results if 'manifest' in r]
    report = {
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'inventory_sha256': acquisition['inventory_sha256'],
        'expected': acquisition['expected'], 'receipts': len(results),
        'pending_acquisition': acquisition['expected'] - len(results),
        'parsed': len(manifests),
        'documents': sum(len(m['documents']) for m in manifests),
        'unresolved_links': sum(len(m['unresolved_links']) for m in manifests),
        'incomplete_manifests': sum(not m['manifest_complete'] for m in manifests),
        'errors': [{k: r[k] for k in ('url', 'error')} for r in results if 'error' in r],
        'source_integrated': False, 'published': False, 'results': results,
    }
    (base / 'detail-reparse-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'results'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
