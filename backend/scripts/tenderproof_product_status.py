"""Track the full product requirements separately from historical sample acceptance.

Refreshes implementation facts only. Evidence and decisions recorded in the
product ledger survive regeneration; registry membership never grants acceptance.
"""
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from app.tenderproof.source_adapters import SOURCE_ADAPTERS

SOURCE_REQUIREMENTS = (
    'official_addresses_and_content_scope', 'discovery_and_pagination',
    'active_and_followed_contests_coverage', 'details_and_all_document_types',
    'contest_identity_and_document_evidence', 'complete_fields_with_provenance',
    'amendments_and_history', 'repeated_current_live_collection',
    'catalogue_publication_and_sync', 'visual_app_verification',
    'recurring_operation_and_recovery',
)
PRODUCT_REQUIREMENTS = (
    'field_absence_ambiguity_extraction_failure_distinguished',
    'document_review_approve_apply_ui', 'login_search_filters_details',
    'favorites_alerts_updates_offline', 'internal_notifications',
    'push_infrastructure_and_device_delivery', 'solari_browser_acquire_result_close',
    'solari_processing_where_needed', 'solari_attempts_usage_spend_reconciliation',
    'legacy_writer_disabled', 'schedules_limits_retries_error_visibility',
    'backup_before_migration', 'restore_in_separate_environment',
    'restart_preserves_data_documents_progress', 'deduplication_and_history',
    'simple_operation_instructions',
)


def pending():
    return {'state': 'unverified', 'evidence': [], 'next_action': None}


def main():
    target = ROOT / 'docs/tenderproof-product-status.json'
    previous = json.loads(target.read_text(encoding='utf-8')) if target.exists() else {}
    prior = {row['source']: row for row in previous.get('sources', [])}
    inventory = json.loads((ROOT / 'docs/tenderproof-sources-99.json').read_text(encoding='utf-8'))
    historical = json.loads((ROOT / 'docs/tenderproof-rollout-matrix.json').read_text(encoding='utf-8'))
    old = {row['source']: row for row in historical['sources']}
    rows = []
    for source in inventory['sources']:
        key = source['source_type']
        adapter = SOURCE_ADAPTERS.get(key)
        row = prior.get(key, {
            'source': key, 'number': source['number'], 'name': source['name'],
            'result': 'incomplete', 'incompatibility_evidence': [],
            'requirements': {}, 'findings': [],
        })
        row['configured_listing_urls'] = list(adapter.listing_urls) if adapter else source['listing_urls']
        row['current_adapter'] = type(adapter).__name__ if adapter else None
        row['implementation_state'] = getattr(adapter, 'implementation_state', 'implemented') if adapter else 'pending'
        row['historical_sample_acceptance'] = {
            'state': old[key]['homologation_state'],
            'scope': old[key]['homologation_scope'],
            'reference': 'docs/tenderproof-rollout-matrix.json',
            'counts_as_full_integration': False,
        }
        for requirement in SOURCE_REQUIREMENTS:
            row['requirements'].setdefault(requirement, pending())
        rows.append(row)
    if len(rows) != 99 or len({row['source'] for row in rows}) != 99:
        raise ValueError('The product must retain all 99 unique sources')
    product = previous.get('product_requirements', {})
    for requirement in PRODUCT_REQUIREMENTS:
        product.setdefault(requirement, pending())
    report = {
        'schema_version': 1, 'updated_at': datetime.now(timezone.utc).isoformat(),
        'goal': 'Complete all 99 sources and the source-to-user product pipeline',
        'completion_rule': 'Every applicable requirement needs current scoped evidence. Incompatible sources need evidence and remain separate from integrated sources. Historical samples and HTTP success do not grant completion.',
        'counts': {'inventory': len(rows), 'registered_adapters': sum(row['current_adapter'] is not None for row in rows),
                   'results': dict(Counter(row['result'] for row in rows))},
        'product_requirements': product, 'sources': rows,
    }
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report['counts']))


if __name__ == '__main__':
    main()
