"""Read-only audit of stored document labels against the current classifier."""
import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tenderproof.continuous_store import get_continuous_store
from app.tenderproof.pilot_adapters import document_kind


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--owner', type=int, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    queue = get_continuous_store()
    changes, inspected, complete = [], 0, False
    for offset in range(0, 10000, 200):
        observations = queue.observations(args.owner, limit=200, offset=offset)
        if not observations:
            complete = True
            break
        for observation in observations:
            inspected += 1
            summary = observation['summary']
            selected = summary.get('selected_document') or {}
            for doc in summary.get('documents', []):
                title, url = doc.get('title'), doc.get('url')
                if not title or not url:
                    continue
                classified = document_kind(title, url)
                old = doc.get('kind')
                if (old == 'edital' and classified not in ('edital', 'consolidado')) or (
                        old == 'outro' and classified in ('retificacao', 'prorrogacao')):
                    changes.append({'source': observation['source'], 'run_id': observation['run_id'],
                        'title': title, 'url': url, 'recorded_kind': old, 'current_kind': classified,
                        'selected_as_principal': selected.get('url') == url and selected.get('title') == title})
    report = {'observed_at': datetime.now(timezone.utc).isoformat(), 'read_only': True,
        'observations_inspected': inspected, 'observation_scan_complete': complete,
        'scope': 'Stored document metadata only; classification changes require source-specific verification and reacquisition.',
        'changes': changes}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    print(json.dumps({'observations': inspected, 'complete': complete, 'changed_labels': len(changes),
        'selected_principals': sum(c['selected_as_principal'] for c in changes),
        'sources': dict(Counter(c['source'] for c in changes))}))


if __name__ == '__main__':
    main()
