"""Prepare the newly discovered Floresta fee-waiver result for document review."""
import json
from pathlib import Path
from app.tenderproof.continuous_store import get_continuous_store
from app.tenderproof.store import get_store
from app.tenderproof import review_cases

def main():
    queue, store = get_continuous_store(), get_store()
    run = store.get_run('tp-tcj-e34b795398cb56cc8260c5df21b3e3e4-1')
    case = review_cases.current(queue, run) or review_cases.prepare(queue, store, run)
    path = Path('/var/lib/observador/tenderproof/product-completion/delivery-facet-review-20260909.json')
    path.write_text(json.dumps({'run_id': run.run_id, 'case': case}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'receipt': str(path), 'case_id': case['id'],
        'documents': [{'title': item['document'].get('title'), 'sha256': item['artifact']['sha256'],
            'pages': len(item['pages']), 'first_page_header': item['pages'][0]['text'].split('INSCRIÇÃO NOME')[0][:600]}
            for item in case['documents']]}, ensure_ascii=False))

if __name__ == '__main__':
    main()
