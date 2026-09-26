"""Prepare one explicitly selected preserved run through the document review service."""
import argparse
import json
from pathlib import Path
from app.tenderproof.continuous_store import get_continuous_store
from app.tenderproof.store import get_store
from app.tenderproof import review_cases

ROOT = Path('/var/lib/observador/tenderproof/product-completion')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    assert Path(args.output).name == args.output and args.output.endswith('.json')
    path = ROOT / args.output
    queue, store = get_continuous_store(), get_store()
    run = store.get_run(args.run)
    assert run
    case = review_cases.current(queue, run) or review_cases.prepare(queue, store, run)
    path.write_text(json.dumps({'run_id': run.run_id, 'case': case}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'receipt': str(path), 'case_id': case['id'],
        'documents': [{'title': document['document'].get('title'), 'sha256': document['artifact']['sha256'],
            'pages': len(document['pages'])} for document in case['documents']]}, ensure_ascii=False))

if __name__ == '__main__':
    main()
