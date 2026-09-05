"""Independent evidence metrics for the live audit.

The crawler's output and the independent portal observation are deliberately
kept separate here.  In particular, ``processed`` never fills an unknown
metric merely to make a coverage ratio look better.
"""

from __future__ import annotations

from typing import Any

METRIC_FIELDS = (
    'visible_items_observed',
    'visible_relevant_items',
    'visible_active_valid_items',
)
LEGACY_METRIC_FIELD = 'visible_valid_items'
NON_AUDITED = 'NOT_AUDITED'


def _count(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    return None


def _explicit_metric_values(source: dict[str, Any]) -> dict[str, int | None]:
    """Return explicitly supplied metrics without falling back to crawler data."""
    values: dict[str, int | None] = {}
    evidence = source.get('metric_evidence')
    if not isinstance(evidence, dict):
        evidence = {}
    for field in METRIC_FIELDS:
        if field in source:
            values[field] = _count(source.get(field))
        elif field in evidence:
            values[field] = _count(evidence.get(field))
    return values


def _legacy_observed(source: dict[str, Any]) -> int | None:
    """Migrate the old independent count only when the new field is absent."""
    if 'visible_items_observed' in source:
        return _count(source.get('visible_items_observed'))
    return _count(source.get(LEGACY_METRIC_FIELD))


def _empty_kind(source: dict[str, Any]) -> str:
    evidence = source.get('empty_evidence')
    if isinstance(evidence, dict):
        return str(evidence.get('kind') or '').casefold()
    return ''


def source_metrics(source: dict[str, Any]) -> dict[str, int | None]:
    """Resolve the three metrics using independent evidence only.

    Existing ``visible_valid_items`` is treated as a legacy independent
    observation count.  It is never treated as relevant or active by default;
    those fields remain ``None`` until explicit semantic evidence exists.
    """
    explicit = _explicit_metric_values(source)
    metrics = {field: explicit.get(field) for field in METRIC_FIELDS}
    if 'visible_items_observed' not in explicit:
        metrics['visible_items_observed'] = _legacy_observed(source)

    # The institutional connector already records this exact semantic fact in
    # independent empty evidence.  It is safe to carry it into the separated
    # metrics because it does not depend on the number of parsed items.
    if (
        source.get('category') == 'institutional_selection'
        and _empty_kind(source) == 'institutional_non_personnel_fomento'
    ):
        if metrics['visible_relevant_items'] is None:
            metrics['visible_relevant_items'] = 0
        if metrics['visible_active_valid_items'] is None:
            metrics['visible_active_valid_items'] = 0
    return metrics


def enrich_source(source: dict[str, Any]) -> dict[str, Any]:
    """Add separated metrics to one audit row while preserving compatibility."""
    metrics = source_metrics(source)
    source.update(metrics)
    if 'metric_evidence' not in source:
        legacy = _count(source.get(LEGACY_METRIC_FIELD))
        source['metric_evidence'] = {
            'method': 'legacy_independent_observation' if legacy is not None else 'unknown',
            'observed_basis': LEGACY_METRIC_FIELD if legacy is not None else None,
            'relevant_basis': 'explicit_only',
            'active_basis': 'explicit_only',
        }
    return source


def has_explicit_empty_evidence(value: Any) -> bool:
    """Whether an empty assertion has enough structure to be auditable."""
    if isinstance(value, dict):
        return bool(value.get('kind') and value.get('value'))
    return isinstance(value, str) and bool(value.strip())


def has_explicit_zero_active_evidence(evidence: Any, active: Any) -> bool:
    """Whether an independent observer explicitly established an empty tab."""
    if active != 0 or not isinstance(evidence, dict):
        return False
    return bool(evidence.get('active_basis') or evidence.get('basis'))


def coverage_explanation(source: dict[str, Any]) -> str | None:
    value = source.get('coverage_explanation')
    if not value and isinstance(source.get('metric_evidence'), dict):
        value = source['metric_evidence'].get('coverage_explanation')
    return str(value).strip() if value else None


def metric_coherence_issues(source: dict[str, Any]) -> list[dict[str, str]]:
    """Return semantic contradictions without silently changing verification."""
    issues: list[dict[str, str]] = []
    status = source.get('verification_status')
    active = _count(source.get('visible_active_valid_items'))
    processed = _count(source.get('processed')) or 0

    if status == 'EMPTY_VERIFIED':
        if active is not None and active > 0:
            issues.append({
                'code': 'empty_verified_active_items',
                'message': 'EMPTY_VERIFIED has visible_active_valid_items > 0',
            })
        elif active is None and not has_explicit_empty_evidence(source.get('empty_evidence')):
            issues.append({
                'code': 'empty_verified_without_sufficient_evidence',
                'message': 'EMPTY_VERIFIED has no known active count and no structured empty_evidence',
            })

    if status == 'VERIFIED' and active is not None and processed != active and not coverage_explanation(source):
        issues.append({
            'code': 'verified_coverage_mismatch',
            'message': f'VERIFIED processed={processed} differs from active={active} without coverage_explanation',
        })
    return issues


def _sum_known(sources: list[dict[str, Any]], field: str) -> int | None:
    values = [_count(source.get(field)) for source in sources]
    known = [value for value in values if value is not None]
    return sum(known) if known else None


def build_metric_summary(sources: list[dict[str, Any]]) -> dict[str, Any]:
    """Build comparable totals and coverage using only known independent counts."""
    total_active = _sum_known(sources, 'visible_active_valid_items')
    coverage_sources = [
        source for source in sources
        if _count(source.get('visible_active_valid_items')) is not None
        and source.get('verification_status') != NON_AUDITED
    ]
    # ``processed`` is a crawler funnel count, not necessarily the number of
    # currently active official entries.  Keep this ratio only for rows where
    # the two counts are explicitly the same active set.
    comparable_sources = [
        source for source in coverage_sources
        if source.get('verification_status') == 'VERIFIED'
        and _count(source.get('processed')) == _count(source.get('visible_active_valid_items'))
    ]
    comparable_active = sum(_count(source.get('visible_active_valid_items')) or 0 for source in comparable_sources)
    comparable_processed = sum(_count(source.get('processed')) or 0 for source in comparable_sources)
    coverage_rate = comparable_processed / comparable_active if comparable_active else None
    return {
        'total_items_observed': _sum_known(sources, 'visible_items_observed'),
        'total_relevant_items_known': _sum_known(sources, 'visible_relevant_items'),
        'total_active_valid_items_known': total_active,
        'total_processed': sum(_count(source.get('processed')) or 0 for source in sources),
        'coverage_rate_known_sources': round(coverage_rate, 4) if coverage_rate is not None else None,
        'coverage_sources_known': len(comparable_sources),
        'metric_inconsistencies': sum(len(metric_coherence_issues(source)) for source in sources),
    }


def audit_summary_matches_sources(summary: dict[str, Any], sources: list[dict[str, Any]]) -> bool:
    expected = build_metric_summary(sources)
    return all(summary.get(key) == value for key, value in expected.items())
