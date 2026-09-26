"""Preserve Garibaldi's pending documents in the legitimate review case store."""
import json
from datetime import datetime, timezone
from pathlib import Path
from app.tenderproof.continuous_store import get_continuous_store
from app.tenderproof.store import get_store
from app.tenderproof import review_cases

def main():
    queue, store = get_continuous_store(), get_store()
    run = store.get_run('tp-tcj-b043232758f45dcaabd67471231c3608-1')
    case = review_cases.current(queue, run) or review_cases.prepare(queue, store, run)
    path = Path('/var/lib/observador/tenderproof/product-completion') / (
        'delivery-legalle-review-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
    path.write_text(json.dumps({'run_id': run.run_id, 'case': case}, ensure_ascii=False, indent=2), encoding='utf-8')
    # Full classification data stays private in the case. Print only two amendment pages.
    print(json.dumps({'receipt': str(path), 'case_id': case['id'], 'revision_hash': case['revision_hash'],
        'documents': [{'title': d['document'].get('title'), 'sha256': d['artifact']['sha256'],
            'pages': d['pages'] if len(d['pages']) == 1 else '[private multiple-page document]'} for d in case['documents']]}, ensure_ascii=False))

if __name__ == '__main__':
    main()
