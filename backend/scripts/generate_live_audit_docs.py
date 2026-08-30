from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

# Support both ``python scripts/...`` from backend and direct invocation from
# the repository root.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.audit_metrics import build_metric_summary, metric_coherence_issues, source_metrics

CRAWLER_STATUSES = ('success', 'empty_valid', 'blocked', 'failed', 'degraded')
VERIFICATION_STATUSES = ('VERIFIED', 'EMPTY_VERIFIED', 'BLOCKED', 'FAILED_EXTERNAL', 'PARTIAL', 'BROKEN', 'NOT_AUDITED')


def sanitize_str(val: Any) -> str:
    if val is None:
        return ''
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', str(val))
    text = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
    return re.sub(r'\s+', ' ', text).strip()


def sanitize_md_cell(val: Any) -> str:
    return sanitize_str(val).replace('|', '\\|')


def display_value(val: Any, default: str = 'UNKNOWN') -> str:
    return default if val is None or val == '' else sanitize_md_cell(val)


def _metric(source: dict[str, Any], field: str) -> Any:
    return source_metrics(source).get(field)


def _crawler_status(source: dict[str, Any]) -> str:
    return source.get('crawler_status') or source.get('status') or 'degraded'


def _verification_status(source: dict[str, Any]) -> str:
    return source.get('verification_status') or ('EMPTY_VERIFIED' if _crawler_status(source) == 'empty_valid' else 'NOT_AUDITED')


def _counts(sources: list[dict[str, Any]], field: str, statuses: tuple[str, ...]) -> dict[str, int]:
    return {status: sum(1 for source in sources if (source.get(field) or '') == status) for status in statuses}


def _summary_counts(data: dict[str, Any], sources: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, int]]:
    summary = data.get('summary', {})
    crawler = summary.get('crawler_status_counts')
    verification = summary.get('verification_status_counts')
    if not isinstance(crawler, dict):
        crawler = _counts(sources, 'crawler_status', CRAWLER_STATUSES)
        if sum(crawler.values()) == 0:
            crawler = _counts(sources, 'status', CRAWLER_STATUSES)
    if not isinstance(verification, dict):
        verification = {status: sum(1 for source in sources if _verification_status(source) == status) for status in VERIFICATION_STATUSES}
    return ({status: int(crawler.get(status, 0)) for status in CRAWLER_STATUSES},
            {status: int(verification.get(status, 0)) for status in VERIFICATION_STATUSES})


def load_audit_json() -> tuple[dict[str, Any], Path, Path]:
    for path in (Path('audit_live_99.json'), Path('backend/audit_live_99.json'), Path('../backend/audit_live_99.json')):
        if path.exists():
            with path.open('r', encoding='utf-8') as handle:
                data = json.load(handle)
            docs_dir = Path('docs') if Path('docs').exists() else Path('../docs')
            return data, path, docs_dir
    raise FileNotFoundError('audit_live_99.json not found in search paths')


def generate_live_sources_audit_md(data: dict[str, Any], out_file: Path) -> None:
    summary = data.get('summary', {})
    sources = data.get('sources', [])
    crawler, verification = _summary_counts(data, sources)
    generated_at = sanitize_str(data.get('generated_at'))
    total_items = summary.get('total_processed', summary.get('total_items', 0))
    calculated_metrics = build_metric_summary(sources)
    observed_total = summary.get('total_items_observed', calculated_metrics['total_items_observed'])
    relevant_total = summary.get('total_relevant_items_known', calculated_metrics['total_relevant_items_known'])
    active_total = summary.get('total_active_valid_items_known', calculated_metrics['total_active_valid_items_known'])
    coverage_rate = summary.get('coverage_rate_known_sources', calculated_metrics['coverage_rate_known_sources'])
    lines = [
        '# Auditoria LIVE das 99 fontes do MASTER_SOURCES',
        '',
        f'> Gerado em: {generated_at}  ',
        f'> Fontes: {summary.get("total_sources", len(sources))}  ',
        f'> Duração: {summary.get("duration_seconds", 0)}s',
        '',
        '## Resumo separado',
        '',
        '### CRAWLER STATUS',
        '',
        '| Status | Quantidade |',
        '|---|---:|',
    ]
    for status in CRAWLER_STATUSES:
        lines.append(f'| `{status}` | {crawler[status]} |')
    lines.extend([
        '',
        '### VERIFICATION STATUS',
        '',
        '| Status | Quantidade |',
        '|---|---:|',
    ])
    for status in VERIFICATION_STATUSES:
        lines.append(f'| `{status}` | {verification[status]} |')
    lines.extend([
        '',
        f'- Candidatos encontrados: {summary.get("total_candidates", "UNKNOWN")}',
        f'- Processados: {total_items}',
        f'- Itens observados independentemente: {display_value(observed_total)}',
        f'- Itens relevantes conhecidos: {display_value(relevant_total)}',
        f'- Itens ativos válidos conhecidos: {display_value(active_total)}',
        f'- Cobertura nas fontes com ativo conhecido: {display_value(coverage_rate)}',
        '',
        '## Política de evidência',
        '',
        'A auditoria compara `expected` observado no site/PDF oficial com `actual` retornado pelo crawler. Campo presente apenas em `actual` é `UNKNOWN`; nunca é `MATCH`.',
        '`visible_items_observed`, `visible_relevant_items` e `visible_active_valid_items` são evidências independentes. `processed` nunca preenche um campo desconhecido.',
        '`visible_valid_items` é mantido apenas como campo legado/deprecated.',
        '',
        '## Matriz das fontes',
        '',
        '| # | Fonte | `source_type` | Observed | Relevant | Active valid | Processed | Verification |',
        '|---:|---|---|---:|---:|---:|---:|---|',
    ])
    for source in sources:
        lines.append(
            f'| {int(source.get("index", 0)):02d} | {sanitize_md_cell(source.get("name"))} | '
            f'`{sanitize_md_cell(source.get("source_type"))}` | '
            f'{display_value(_metric(source, "visible_items_observed"))} | '
            f'{display_value(_metric(source, "visible_relevant_items"))} | '
            f'{display_value(_metric(source, "visible_active_valid_items"))} | '
            f'{source.get("processed", 0)} | `{_verification_status(source)}` |'
        )

    lines.extend(['', '## Amostras e comparações', ''])
    for source in sources:
        if _crawler_status(source) != 'success':
            continue
        sample = source.get('sample') or {}
        lines.extend([
            f'### {int(source.get("index", 0)):02d}. {sanitize_str(source.get("name"))} (`{sanitize_str(source.get("source_type"))}`)',
            f'- Crawler: `{_crawler_status(source)}`; verificação: `{_verification_status(source)}`',
            f'- Observed: {display_value(_metric(source, "visible_items_observed"))}; relevant: {display_value(_metric(source, "visible_relevant_items"))}; active valid: {display_value(_metric(source, "visible_active_valid_items"))}; processed: {source.get("processed", 0)}',
            f'- Método: {sanitize_str(sample.get("observation_method")) or "não informado"}',
            f'- URLs de evidência: {", ".join(sanitize_str(url) for url in sample.get("evidence_urls", source.get("evidence_urls", [])))}',
            '',
            '```json',
            json.dumps({
                'expected': sample.get('expected'),
                'actual': sample.get('actual'),
                'field_audit': sample.get('field_audit', source.get('field_audit')),
                'publication_audit': sample.get('publication_audit', source.get('publication_audit')),
            }, indent=2, ensure_ascii=False),
            '```',
            '',
        ])

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def generate_live_audit_issues_md(data: dict[str, Any], out_file: Path) -> None:
    sources = data.get('sources', [])
    crawler, verification = _summary_counts(data, sources)
    calculated_metrics = build_metric_summary(sources)
    summary = data.get('summary') or {}
    lines = [
        '# Questões da auditoria LIVE',
        '',
        f'> Gerado em: {sanitize_str(data.get("generated_at"))}',
        '',
        'Este documento é derivado exclusivamente de `audit_live_99.json`; não contém contagens ou alegações manuais.',
        '',
        '## Contagens',
        '',
        '### Crawler',
        '',
    ]
    lines.extend(f'- `{status}`: {crawler[status]}' for status in CRAWLER_STATUSES)
    lines.extend(['', '### Verificação', ''])
    lines.extend(f'- `{status}`: {verification[status]}' for status in VERIFICATION_STATUSES)
    lines.extend([
        '',
        '### Métricas independentes',
        '',
        f'- `total_items_observed`: {display_value(summary.get("total_items_observed", calculated_metrics["total_items_observed"]))}',
        f'- `total_relevant_items_known`: {display_value(summary.get("total_relevant_items_known", calculated_metrics["total_relevant_items_known"]))}',
        f'- `total_active_valid_items_known`: {display_value(summary.get("total_active_valid_items_known", calculated_metrics["total_active_valid_items_known"]))}',
        f'- `coverage_rate_known_sources`: {display_value(summary.get("coverage_rate_known_sources", calculated_metrics["coverage_rate_known_sources"]))}',
    ])
    lines.extend(['', '## Fontes que exigem atenção', ''])
    attention = [
        source for source in sources
        if _crawler_status(source) in {'degraded', 'failed'}
        or _verification_status(source) in {'PARTIAL', 'BROKEN', 'NOT_AUDITED', 'FAILED_EXTERNAL'}
        or metric_coherence_issues(source)
    ]
    if not attention:
        lines.append('Nenhuma fonte classificada como problema no JSON.')
    for source in attention:
        lines.extend([
            f'### {int(source.get("index", 0)):02d}. {sanitize_str(source.get("name"))} (`{sanitize_str(source.get("source_type"))}`)',
            f'- Crawler: `{_crawler_status(source)}`; verificação: `{_verification_status(source)}`',
            f'- Observed: {display_value(_metric(source, "visible_items_observed"))}; relevant: {display_value(_metric(source, "visible_relevant_items"))}; active valid: {display_value(_metric(source, "visible_active_valid_items"))}; processed: {source.get("processed", 0)}',
            f'- Erro: {sanitize_str(source.get("error_type"))} {sanitize_str(source.get("error_message"))}'.strip(),
        ])
        for issue in metric_coherence_issues(source):
            lines.append(f'- Inconsistência de métricas: `{sanitize_str(issue.get("code"))}` — {sanitize_str(issue.get("message"))}')
        for note in source.get('audit_notes', []):
            lines.append(f'- Nota: {sanitize_str(note)}')
        publication = source.get('publication_audit') or {}
        if publication.get('invalid_actual_titles'):
            lines.append(f'- Publicações inválidas: {sanitize_str(publication.get("invalid_actual_titles"))}')
        if source.get('empty_evidence'):
            lines.append(f'- Evidência de vazio: {sanitize_str(source.get("empty_evidence"))}')
        lines.append('')

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> None:
    data, json_path, docs_dir = load_audit_json()
    sources = data.get('sources', [])
    print(f'Loaded audit data from {json_path}')
    print(f'Total sources in JSON: {len(sources)}')
    generate_live_sources_audit_md(data, docs_dir / 'LIVE_SOURCES_AUDIT.md')
    generate_live_audit_issues_md(data, docs_dir / 'LIVE_AUDIT_ISSUES.md')
    print('Documentation generation complete.')


if __name__ == '__main__':
    main()
