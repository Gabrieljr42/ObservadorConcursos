"""Fresh, read-only delivery snapshot; keeps earlier delivery receipts immutable."""
import contextlib
import io
import json
import runpy
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def main():
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        runpy.run_path(str(Path(__file__).with_name('delivery_snapshot.py')))
    report = json.loads(output.getvalue())
    root = Path('/var/lib/observador/tenderproof')
    with sqlite3.connect((root / 'solari-budget.sqlite3').as_uri() + '?mode=ro', uri=True) as db:
        report['solari'] = {
            'authorized_usd': db.execute('SELECT cents FROM budget WHERE id=1').fetchone()[0] / 100,
            'reserved_usd': db.execute('SELECT coalesce(sum(cents),0) FROM reservations').fetchone()[0] / 100,
            'sessions': db.execute('SELECT count(*) FROM reservations').fetchone()[0],
            'unclosed': db.execute('SELECT count(*) FROM reservations WHERE closed_at IS NULL').fetchone()[0],
            'confirmed_billed_usd': None,
        }
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    path = root / 'product-completion' / ('delivery-current-' + stamp + '.json')
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({
        'receipt': str(path), 'contests': len(report['catalogue']),
        'sources_in_catalogue': len({c['source_id'] for c in report['catalogue']}),
        'adapters': report['registered_adapters'],
        'enabled': sum(bool(s['enabled']) for s in report['sources']),
        'historical_success_sources': sum(s['historical_detail_jobs'].get('succeeded', 0) > 0 for s in report['sources']),
        'solari': report['solari'],
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
