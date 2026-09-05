from __future__ import annotations

from app.audit_metrics import (
    audit_summary_matches_sources,
    build_metric_summary,
    metric_coherence_issues,
    source_metrics,
)


def _source(**overrides):
    source = {
        'verification_status': 'EMPTY_VERIFIED',
        'processed': 0,
        'empty_evidence': {'kind': 'evaluated_closed', 'value': 'all reviewed entries closed'},
        'visible_items_observed': 0,
        'visible_relevant_items': None,
        'visible_active_valid_items': None,
    }
    source.update(overrides)
    return source


def test_observed_items_with_zero_active_are_valid_empty():
    source = _source(
        visible_items_observed=30,
        visible_relevant_items=18,
        visible_active_valid_items=0,
    )
    assert metric_coherence_issues(source) == []


def test_empty_verified_with_active_items_is_inconsistent():
    issues = metric_coherence_issues(_source(visible_active_valid_items=8))
    assert {issue['code'] for issue in issues} == {'empty_verified_active_items'}


def test_verified_equal_active_count_has_no_coverage_issue():
    source = _source(
        verification_status='VERIFIED',
        processed=10,
        visible_active_valid_items=10,
    )
    assert metric_coherence_issues(source) == []


def test_verified_shortfall_without_explanation_is_a_mismatch():
    issues = metric_coherence_issues(_source(
        verification_status='VERIFIED',
        processed=8,
        visible_active_valid_items=10,
    ))
    assert {issue['code'] for issue in issues} == {'verified_coverage_mismatch'}


def test_verified_shortfall_with_explanation_is_allowed():
    source = _source(
        verification_status='VERIFIED',
        processed=8,
        visible_active_valid_items=10,
        coverage_explanation='Two cards are aliases of the same process.',
    )
    assert metric_coherence_issues(source) == []


def test_unknown_evidence_stays_null_instead_of_becoming_zero():
    metrics = source_metrics({
        'processed': 0,
        'visible_valid_items': None,
        'visible_items_observed': None,
        'visible_relevant_items': None,
        'visible_active_valid_items': None,
    })
    assert metrics == {
        'visible_items_observed': None,
        'visible_relevant_items': None,
        'visible_active_valid_items': None,
    }


def test_fomento_evidence_allows_empty_verified_with_zero_scope():
    source = _source(
        category='institutional_selection',
        visible_items_observed=106,
        visible_relevant_items=None,
        visible_active_valid_items=None,
        empty_evidence={
            'kind': 'institutional_non_personnel_fomento',
            'value': 'all calls are research fomento',
        },
    )
    metrics = source_metrics(source)
    source.update(metrics)
    assert metrics['visible_items_observed'] == 106
    assert metrics['visible_relevant_items'] == 0
    assert metrics['visible_active_valid_items'] == 0
    assert metric_coherence_issues(source) == []


def test_summary_matches_source_metrics():
    sources = [
        _source(
            verification_status='VERIFIED',
            visible_items_observed=30,
            visible_relevant_items=18,
            visible_active_valid_items=10,
            processed=10,
        ),
        _source(
            visible_items_observed=5,
            visible_relevant_items=5,
            visible_active_valid_items=0,
        ),
        _source(
            verification_status='NOT_AUDITED',
            visible_items_observed=None,
            visible_relevant_items=None,
            visible_active_valid_items=99,
            processed=99,
        ),
    ]
    summary = build_metric_summary(sources)
    assert summary['total_items_observed'] == 35
    assert summary['total_relevant_items_known'] == 23
    assert summary['total_active_valid_items_known'] == 109
    assert summary['total_processed'] == 109
    assert summary['coverage_rate_known_sources'] == 1.0
    # Only VERIFIED rows whose processed set is explicitly identical to the
    # independent active set are comparable for this ratio.
    assert summary['coverage_sources_known'] == 1
    assert audit_summary_matches_sources(summary, sources)


def test_docs_use_separated_metric_columns(tmp_path):
    from scripts.generate_live_audit_docs import generate_live_sources_audit_md

    data = {
        'generated_at': '2026-08-30T00:00:00Z',
        'summary': {
            'total_sources': 1,
            'total_processed': 10,
            'total_items_observed': 30,
            'total_relevant_items_known': 18,
            'total_active_valid_items_known': 10,
            'coverage_rate_known_sources': 1.0,
        },
        'sources': [{
            'index': 1,
            'name': 'Example',
            'source_type': 'example_open',
            'crawler_status': 'success',
            'verification_status': 'VERIFIED',
            'visible_items_observed': 30,
            'visible_relevant_items': 18,
            'visible_active_valid_items': 10,
            'processed': 10,
        }],
    }
    output = tmp_path / 'LIVE_SOURCES_AUDIT.md'
    generate_live_sources_audit_md(data, output)
    content = output.read_text(encoding='utf-8')
    assert '| # | Fonte | `source_type` | Observed | Relevant | Active valid | Processed | Verification |' in content
    assert 'Visible valid' not in content
    assert '`visible_valid_items` é mantido apenas como campo legado/deprecated.' in content
