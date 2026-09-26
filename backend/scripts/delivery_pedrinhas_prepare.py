"""Prepare the actual Pedrinhas document review; never approve or publish."""
import json
from datetime import datetime, timezone
from pathlib import Path
from app.tenderproof.continuous_store import get_continuous_store
from app.tenderproof.store import get_store
from app.tenderproof import review_cases


def main():
    queue, store = get_continuous_store(), get_store()
    with queue._db() as db:
        rows = db.execute("SELECT candidate,last_run_id FROM known_candidates WHERE source='fenix_open' AND mode='real'").fetchall()
    matches = [r for r in rows if str(json.loads(r['candidate']).get('external_id')) == '129']
    if len(matches) != 1:
        raise ValueError('Expected exactly one Pedrinhas candidate')
    run = store.get_run(matches[0]['last_run_id'])
    case = review_cases.current(queue, run) or review_cases.prepare(queue, store, run)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    path = Path('/var/lib/observador/tenderproof/product-completion') / ('delivery-pedrinhas-review-' + stamp + '.json')
    path.write_text(json.dumps({'run_id': run.run_id, 'case': case}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'receipt': str(path), 'run_id': run.run_id, 'case_id': case['id'],
        'documents': [{'title': d['document'].get('title'), 'sha256': d['artifact']['sha256'],
                       'pages': len(d['pages'])} for d in case['documents']]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
