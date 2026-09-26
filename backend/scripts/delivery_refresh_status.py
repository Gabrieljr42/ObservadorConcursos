"""Refresh current delivery facts while retaining the prior delivery and requirements."""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[2]
    receipts = root / 'backend/.tenderproof/product-completion'
    latest = lambda pattern: max(receipts.glob(pattern), key=lambda p: p.stat().st_mtime)
    api_path, snapshot_path = latest('delivery-api-current-*.json'), latest('delivery-current-*.json')
    api, snapshot = (json.loads(p.read_text(encoding='utf-8')) for p in (api_path, snapshot_path))
    path = root / 'docs/tenderproof-product-status.json'
    status = json.loads(path.read_text(encoding='utf-8'))
    matrix = list(csv.DictReader((root / 'docs/entrega-fontes-atual.csv').open(encoding='utf-8-sig'), delimiter=';'))
    assert len(matrix) == len(status['sources']) == 99
    previous = status.get('delivery', {})
    if previous.get('state') != 'in_progress_authorized_completion':
        status.setdefault('delivery_history', []).append({'recorded_at': status['updated_at'], 'delivery': previous})
    status.setdefault('legacy_requirements_snapshot_at', status['updated_at'])
    by_source = {row['fonte']: row for row in matrix}
    for source in status['sources']:
        row = by_source[source['source']]
        source['current_delivery'] = {key: row[key] for key in ('status_objetivo', 'escopo_verificavel', 'fato_objetivo', 'lacunas', 'evidencia_especifica', 'condicao_retomada')}
    status['delivery'] = {
        'state': 'in_progress_authorized_completion',
        'scope': 'Current document-verified pilot records; whole-source integration is not certified.',
        'catalogue_contests': api['contests'], 'catalogue_sources': api['sources'],
        'structured_jobs': api['structured_jobs'], 'new_contests_this_execution': api['contests'] - 10,
        'open_contest_ids_at_verification': api.get('open_contest_ids', []),
        'sources_with_historical_successful_detail_jobs': sum(s['historical_detail_jobs'].get('succeeded', 0) > 0 for s in snapshot['sources']),
        'fully_integrated_sources': 0, 'versions': api['counts']['versions'],
        'internal_notifications': api['counts']['notifications'],
        'pending_document_contest_ids': [c['id'] for c in api['catalogue'] if c['review']['pending']],
        'applied_amendment_contest_ids': [c['id'] for c in api['catalogue'] if c.get('amendments')],
        'known_amended_deadline_not_yet_applied_contest_ids': [],
        'application_url': 'http://localhost:13000/inicio',
        'ui_verified': api['ui_verified'],
        'ui_blocker': 'Another browser instance holds the OPFS handle. No storage was deleted; user was asked to close prior instances.',
        'source_matrix': 'docs/entrega-fontes-atual.csv', 'operation_report': 'docs/ENTREGA-ATUAL-OPERACAO.md',
        'evidence': [str(api_path.relative_to(root)), str(snapshot_path.relative_to(root))],
        'solari': snapshot['solari'],
    }
    status['updated_at'] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': str(path), 'contests': api['contests'], 'sources': api['sources'], 'ui_verified': api['ui_verified'], 'historical_requirements_preserved': True}))


if __name__ == '__main__':
    main()
