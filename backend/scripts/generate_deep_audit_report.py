from __future__ import annotations

"""Generate the evidence-preserving BEFORE -> AFTER report for the 99-source audit."""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.audit_validation import count_statuses  # noqa: E402


CRAWLER_STATUSES = ('success', 'empty_valid', 'blocked', 'failed', 'degraded')
VERIFICATION_STATUSES = (
    'VERIFIED', 'EMPTY_VERIFIED', 'BLOCKED', 'FAILED_EXTERNAL',
    'PARTIAL', 'BROKEN', 'NOT_AUDITED',
)
CLASSIFICATIONS = {
    'A': 'FUNCIONA E TEM EVIDÊNCIA',
    'B': 'FUNCIONA MAS FALTA EVIDÊNCIA INDEPENDENTE',
    'C': 'DISCOVERY INCOMPLETO',
    'D': 'PARSER INCOMPLETO',
    'E': 'QUALITY GATE REJEITANDO ITEM VÁLIDO',
    'F': 'PUBLICAÇÕES INCORRETAS',
    'G': 'VAZIO LEGÍTIMO',
    'H': 'VAZIO NÃO CONFIRMADO',
    'I': 'WAF / CLOUDFLARE / ANTI-BOT',
    'J': 'SITE FORA DO AR',
    'K': 'API EXTERNA COM ERRO',
    'L': 'JAVASCRIPT / SPA',
    'M': 'SSL / TLS / ENCODING',
    'N': 'ESTRUTURA DO SITE ALTERADA',
    'O': 'CONTEÚDO FORA DO ESCOPO',
    'P': 'AUDITOR SEM EVIDÊNCIA SUFICIENTE',
    'Q': 'OUTRO',
}
NOT_AUDITED_BUCKETS = {
    'A': 'crawler provavelmente correto, mas evidência insuficiente',
    'B': 'crawler precisa de trabalho futuro',
    'C': 'site incompatível com auditor independente',
    'D': 'conteúdo inexistente atualmente',
    'E': 'portal instável',
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open('r', encoding='utf-8') as handle:
        value = json.load(handle)
    if not isinstance(value, dict) or not isinstance(value.get('sources'), list):
        raise ValueError(f'Payload inválido: {path}')
    return value


def text(value: Any, default: str = 'UNKNOWN') -> str:
    if value is None or value == '':
        return default
    result = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', str(value))
    result = re.sub(r'\s+', ' ', result).strip()
    return result or default


def cell(value: Any, default: str = 'UNKNOWN') -> str:
    return text(value, default).replace('|', '\\|')


def number(value: Any) -> str:
    return text(value)


def source_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(source.get('source_type')): source for source in payload.get('sources', [])}


def rejection_counts(source: dict[str, Any]) -> dict[str, int]:
    diagnostics = source.get('crawler_diagnostics') or {}
    counts = diagnostics.get('rejection_counts') if isinstance(diagnostics, dict) else None
    return {str(key): int(value) for key, value in (counts or {}).items() if isinstance(value, int)}


def mismatch_fields(source: dict[str, Any]) -> list[str]:
    audit = source.get('field_audit') or {}
    return [field for field, status in audit.items() if status == 'MISMATCH']


def publication_reason(source: dict[str, Any]) -> str | None:
    publication = source.get('publication_audit') or {}
    if publication.get('status') == 'MISMATCH':
        missing = len(publication.get('missing_titles') or []) + len(publication.get('missing_links') or [])
        invalid = len(publication.get('invalid_actual_titles') or [])
        return f'publication_audit=MISMATCH (missing={missing}, invalid={invalid})'
    return None


def classify(source: dict[str, Any]) -> tuple[str, str]:
    crawler = source.get('crawler_status') or source.get('status')
    verification = source.get('verification_status')
    error_blob = f'{source.get("error_type") or ""} {source.get("error_message") or ""}'.casefold()
    diagnostics = source.get('crawler_diagnostics') or {}
    rejection = rejection_counts(source)
    empty = source.get('empty_evidence') or {}

    if verification == 'BLOCKED' or crawler == 'blocked':
        if source.get('http_status') in {401, 403, 429} or any(token in error_blob for token in ('cloudflare', 'waf', 'captcha', 'challenge', '403', '429', 'forbidden', 'anti-bot')):
            return 'I', 'bloqueio HTTP/anti-bot registrado no estado externo'
        return 'Q', 'crawler registrado como bloqueado, mas o payload não identifica o mecanismo'
    if verification == 'FAILED_EXTERNAL' or crawler == 'failed':
        if any(token in error_blob for token in ('api', 'json', 'endpoint')):
            return 'K', 'falha externa associada a endpoint/API'
        if any(token in error_blob for token in ('ssl', 'tls', 'certificate', 'encoding', 'unicode')):
            return 'M', 'falha externa associada a SSL/TLS/encoding'
        return 'J', 'falha externa de transporte/site registrada'

    if verification == 'EMPTY_VERIFIED':
        if isinstance(empty, dict) and empty.get('kind') == 'institutional_non_personnel_fomento':
            return 'O', 'portal observado com conteúdo de fomento fora do escopo de pessoal'
        return 'G', 'vazio confirmado por marcador, aba/API ou métrica oficial explícita'
    if crawler == 'empty_valid' or verification == 'H':
        return 'H', 'crawler declarou vazio, mas não há evidência independente suficiente'

    pub_reason = publication_reason(source)
    if pub_reason:
        return 'F', pub_reason
    if verification == 'VERIFIED':
        return 'A', 'identidade e pelo menos dois campos de domínio conferidos independentemente'

    mismatches = mismatch_fields(source)
    if verification == 'BROKEN':
        # A rejection count alone does not prove that the discarded item was
        # valid. Keep the primary classification on the independently proven
        # mismatch and retain the quality-gate trace in the reason/JSON.
        gate_note = f'; quality_gate={rejection["quality_gate"]}' if rejection.get('quality_gate') else ''
        return 'D', f'campo(s) independentemente divergente(s): {", ".join(mismatches) or "UNKNOWN"}{gate_note}'

    if source.get('observation_error'):
        if any(token in error_blob for token in ('timeout', 'connect', '503', '502', '500', 'unavailable')):
            return 'J', f'observação independente falhou: {text(source.get("observation_error"))}'
        if any(token in error_blob for token in ('javascript', 'spa', 'render')):
            return 'L', f'observação depende de JavaScript/SPA: {text(source.get("observation_error"))}'
        return 'N', f'observação não conseguiu interpretar a estrutura: {text(source.get("observation_error"))}'
    if crawler == 'degraded':
        if rejection.get('quality_gate'):
            return 'C', f'{rejection["quality_gate"]} candidato(s) descoberto(s), mas nenhum foi processado'
        if source.get('error_type') == 'UnconfirmedEmpty':
            return 'C', 'zero candidatos sem evidência de vazio; discovery/selector inconclusivo'
        return 'Q', text(source.get('error_type') or 'causa do estado degraded não confirmada')
    if verification == 'NOT_AUDITED':
        if source.get('sample') and not source.get('sample', {}).get('expected'):
            return 'B', 'crawler produziu amostra, mas o observador não obteve valor independente comparável'
        return 'P', text(source.get('verification_reason') or 'evidência independente insuficiente')
    return 'Q', 'estado não contemplado por regra específica'


def not_audited_bucket(source: dict[str, Any]) -> str:
    if source.get('crawler_status') == 'empty_valid':
        return 'D'
    error_blob = f'{source.get("error_type") or ""} {source.get("error_message") or ""} {source.get("observation_error") or ""}'.casefold()
    if source.get('crawler_status') in {'failed', 'blocked', 'degraded'} or any(
        token in error_blob for token in ('timeout', 'unavailable', 'connection', '503', '502', '403', '429')
    ):
        return 'E'
    if source.get('sample') and source.get('sample', {}).get('expected'):
        return 'A'
    if source.get('sample'):
        return 'B'
    return 'C'


def audit_counts(source: dict[str, Any]) -> dict[str, int]:
    counts = count_statuses(source.get('field_audit'))
    return {key: counts.get(key, 0) for key in ('MATCH', 'MISMATCH', 'UNKNOWN', 'NULL_OK')}


def independent_method(source: dict[str, Any]) -> str:
    sample = source.get('sample') or {}
    return text(sample.get('observation_method') or source.get('observation_method'))


def change_for(source: dict[str, Any], before: dict[str, Any] | None) -> tuple[str, str]:
    source_type = source.get('source_type')
    targeted = {
        'fcc_open': 'limite de candidatos ampliado, CFP/PLANEJAR excluído do escopo e rejeições detalhadas; parser de datas/taxa revisado',
        'cesgranrio_open': 'intervalos numéricos com ano compartilhado e taxas por faixa revisados; rejeições de intervalo mantidas rastreáveis',
    }
    if source_type in targeted:
        return 'correção direcionada aplicada', targeted[source_type]
    if not before:
        return 'fonte nova no payload final', 'sem estado BEFORE correspondente'
    before_state = f'{before.get("crawler_status", before.get("status"))}/{before.get("verification_status")}'
    after_state = f'{source.get("crawler_status")}/{source.get("verification_status")}'
    if before_state != after_state:
        return f'{before_state} → {after_state}', 'estado reavaliado após correções gerais de coerência/evidência'
    return 'sem transição de estado', 'nenhuma alteração específica de connector aplicada; estado foi revalidado'


def metric_value(source: dict[str, Any], key: str) -> str:
    return number(source.get(key))


def source_row(source: dict[str, Any], before: dict[str, Any] | None) -> list[str]:
    classification, reason = classify(source)
    counts = audit_counts(source)
    publication = source.get('publication_audit') or {}
    transition, change = change_for(source, before)
    return [
        cell(source.get('index')), cell(source.get('name')), cell(source.get('source_type')),
        cell(before.get('verification_status') if before else None), cell(source.get('verification_status')),
        cell(source.get('crawler_status')), number(before.get('candidates_found') if before else None),
        number(source.get('candidates_found', 0)), number(source.get('candidates_rejected', 0)),
        number(before.get('processed') if before else None), number(source.get('processed', 0)),
        metric_value(source, 'visible_items_observed'), metric_value(source, 'visible_relevant_items'),
        metric_value(source, 'visible_active_valid_items'), number(counts['MATCH']),
        number(counts['MISMATCH']), number(counts['UNKNOWN']), cell(publication.get('status')),
        number(publication.get('expected_count')), number(publication.get('actual_count')),
        cell(source.get('error_type')), cell(source.get('error_message')), f'{classification}. {CLASSIFICATIONS[classification]}',
        cell(reason), cell(source.get('verification_reason')), cell(transition), cell(change),
    ]


def md_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = [f'| {" | ".join(headers)} |', f'| {" | ".join("---" for _ in headers)} |']
    lines.extend(f'| {" | ".join(cell(value) for value in row)} |' for row in rows)
    return lines


def summary_rows(before: dict[str, Any], after: dict[str, Any]) -> list[list[str]]:
    before_counts = before.get('summary', {}).get('verification_status_counts') or {}
    after_counts = after.get('summary', {}).get('verification_status_counts') or {}
    return [[status, str(before_counts.get(status, 0)), str(after_counts.get(status, 0))] for status in VERIFICATION_STATUSES]


def crawler_summary_rows(before: dict[str, Any], after: dict[str, Any]) -> list[list[str]]:
    before_counts = before.get('summary', {}).get('crawler_status_counts') or {}
    after_counts = after.get('summary', {}).get('crawler_status_counts') or {}
    return [[status, str(before_counts.get(status, 0)), str(after_counts.get(status, 0))] for status in CRAWLER_STATUSES]


def rejection_rows(sources: list[dict[str, Any]]) -> list[list[str]]:
    counts: Counter[str] = Counter()
    urls: Counter[str] = Counter()
    for source in sources:
        for key, value in rejection_counts(source).items():
            counts[key] += value
        diagnostics = source.get('crawler_diagnostics') or {}
        for rejection in diagnostics.get('rejections', []) if isinstance(diagnostics, dict) else []:
            if isinstance(rejection, dict):
                urls[str(rejection.get('reason') or 'UNKNOWN')] += 1
    return [[key, str(counts[key]), str(urls.get(key, 0))] for key in sorted(counts)]


def fcc_rejection_rows(source: dict[str, Any]) -> list[list[str]]:
    diagnostics = source.get('crawler_diagnostics') or {}
    rows = []
    for rejection in diagnostics.get('rejections', []) if isinstance(diagnostics, dict) else []:
        if isinstance(rejection, dict):
            rows.append([
                rejection.get('url'), rejection.get('reason'),
                rejection.get('error_codes'), rejection.get('empty_evidence'),
            ])
    return rows


def publication_rows(sources: list[dict[str, Any]]) -> tuple[list[list[str]], list[list[str]]]:
    counts: Counter[str] = Counter()
    details = []
    for source in sources:
        publication = source.get('publication_audit') or {}
        status = publication.get('status') or 'UNKNOWN'
        counts[status] += 1
        if status == 'MISMATCH' or publication.get('invalid_actual_titles'):
            details.append([
                source.get('source_type'), status, publication.get('expected_count'),
                publication.get('actual_count'), len(publication.get('missing_titles') or []),
                len(publication.get('missing_links') or []), publication.get('invalid_actual_titles'),
            ])
    return [[key, str(value)] for key, value in sorted(counts.items())], details


def blocked_rows(sources: list[dict[str, Any]]) -> list[list[str]]:
    rows = []
    for source in sources:
        if source.get('verification_status') != 'BLOCKED':
            continue
        rows.append([
            source.get('source_type'), source.get('url'), source.get('error_type'),
            source.get('error_message'), source.get('http_status'), source.get('browser_used'),
            'não identificado no payload final', 'não identificada no payload final',
            'investigar endpoint/API oficial e workaround legítimo em rodada futura; não comprovado nesta rodada',
        ])
    return rows


def generate(before: dict[str, Any], after: dict[str, Any], out_file: Path) -> None:
    before_by_type = source_map(before)
    sources = after.get('sources', [])
    classified = [(*classify(source), source) for source in sources]
    verification_counts = Counter(source.get('verification_status') for source in sources)
    classification_counts = Counter(row[0] for row in classified)
    bucket_counts = Counter(not_audited_bucket(source) for source in sources if source.get('verification_status') == 'NOT_AUDITED')
    publication_counts, publication_details = publication_rows(sources)
    fcc = next((source for source in sources if source.get('source_type') == 'fcc_open'), {})
    coverage_rate = after.get('summary', {}).get('coverage_rate_known_sources')
    coverage_sources = after.get('summary', {}).get('coverage_sources_known')

    lines: list[str] = [
        '# Relatório de resolução profunda da auditoria LIVE — 99 fontes',
        '',
        f'> Payload final: `audit_live_99.json`, gerado em {cell(after.get("generated_at"))}.',
        f'> Baseline BEFORE preservado em `audit_live_99_before_deep_resolution.json`, gerado em {cell(before.get("generated_at"))}.',
        '',
        '## Escopo, método e política de evidência',
        '',
        'Foram executados o crawler de cada entrada de `MASTER_SOURCES` e um observador independente sobre as páginas/listagens oficiais alcançáveis na mesma rodada. A comparação usa `expected` observado independentemente contra `actual` do crawler; um valor presente apenas no crawler permanece `UNKNOWN` e nunca é promovido a `MATCH`.',
        '',
        'Os campos de estado permanecem separados: `crawler_status` descreve a execução do crawler; `verification_status` descreve o que a evidência independente permitiu provar. `processed` é funil do crawler e não preenche `visible_items_observed`, `visible_relevant_items` ou `visible_active_valid_items`.',
        '',
        'A auditoria é uma fotografia temporal. Sites podem mudar depois do horário indicado; bloqueios, conteúdo vazio e dados de inscrição devem ser rechecados em nova execução.',
        '',
        '## BEFORE → AFTER',
        '',
        '### Verification status',
        '',
        *md_table(['Status', 'Antes', 'Depois'], summary_rows(before, after)),
        '',
        '### Crawler status',
        '',
        *md_table(['Status', 'Antes', 'Depois'], crawler_summary_rows(before, after)),
        '',
        '### Totais e métricas separadas',
        '',
        *md_table(
            ['Métrica', 'Antes', 'Depois'],
            [[key, before.get('summary', {}).get(key), after.get('summary', {}).get(key)] for key in (
                'total_candidates', 'total_processed', 'total_items_observed',
                'total_relevant_items_known', 'total_active_valid_items_known',
                'coverage_rate_known_sources', 'coverage_sources_known', 'metric_inconsistencies',
            )],
        ),
        '',
        f'A cobertura final é `{cell(coverage_rate)}` em {cell(coverage_sources)} fonte(s) comparável(is): somente linhas `VERIFIED` em que `processed` coincide explicitamente com o conjunto ativo independente entram no denominador. Isso evita interpretar o funil total do crawler como cobertura do universo ativo.',
        '',
        '## Classificação principal A–Q',
        '',
        *md_table(['Código', 'Classificação', 'Fontes'], [[key, CLASSIFICATIONS[key], classification_counts.get(key, 0)] for key in CLASSIFICATIONS]),
        '',
        'A classificação é uma camada explicativa e não substitui `verification_status`.',
        '',
        '## NOT_AUDITED restante — buckets A–E',
        '',
        *md_table(['Bucket', 'Definição', 'Quantidade', 'Fontes'], [
            [key, value, bucket_counts.get(key, 0), ', '.join(source.get('source_type', '') for source in sources if source.get('verification_status') == 'NOT_AUDITED' and not_audited_bucket(source) == key) or '-']
            for key, value in NOT_AUDITED_BUCKETS.items()
        ]),
        '',
        'Cada uma das fontes `NOT_AUDITED` abaixo também possui `verification_reason` no JSON final; o bucket é apenas uma agregação operacional.',
        '',
        '## Resultado por fonte (todas as 99)',
        '',
        *md_table(
            ['#', 'Fonte', 'source_type', 'Antes', 'Depois', 'Crawler', 'Cand. antes', 'Cand. depois', 'Rej.', 'Proc. antes', 'Proc. depois', 'Observed', 'Relevant', 'Active', 'MATCH', 'MISMATCH', 'UNKNOWN', 'Pub.', 'Pub. esp.', 'Pub. atual', 'error_type', 'error_message', 'Classificação', 'Razão principal', 'verification_reason', 'Transição', 'Alteração'],
            [source_row(source, before_by_type.get(source.get('source_type'))) for source in sources],
        ),
        '',
        '## Trilha de rejeições',
        '',
        *md_table(['Reason code', 'Quantidade registrada', 'Entradas rastreáveis'], rejection_rows(sources)),
        '',
        'Os reason codes acima vêm de `crawler_diagnostics.rejection_counts`; as URLs e os detalhes permanecem no JSON final. Para FCC, a trilha completa da rodada é:',
        '',
        *md_table(['URL', 'Reason', 'Error codes', 'Evidência adicional'], fcc_rejection_rows(fcc)),
        '',
        '## Auditoria de publicações',
        '',
        *md_table(['Status', 'Fontes'], publication_counts),
        '',
        *md_table(['source_type', 'Status', 'Esperadas', 'Atuais', 'Títulos ausentes', 'Links ausentes', 'Títulos inválidos'], publication_details or [['Nenhuma', 'UNKNOWN', 0, 0, 0, 0, '']]),
        '',
        'A observação independente rejeita itens de menu, privacy, cookies, login e navegação como publicações. `UNKNOWN` significa que a publicação não foi comparável, não que foi confirmada.',
        '',
        '## Relatório de BLOCKED',
        '',
        *md_table(['source_type', 'URL', 'Tipo de bloqueio', 'Mensagem registrada', 'HTTP', 'Browser', 'Endpoint alternativo', 'API pública', 'Recomendação'], blocked_rows(sources) or [['Nenhuma', '', '', '', '', '', '', '', '']]),
        '',
        'A tabela não infere causa além do que o payload registrou. Endpoints alternativos, APIs públicas e workarounds aparecem como “não identificados” quando não foram comprovados nesta rodada.',
        '',
        '## Limitações e leitura correta',
        '',
        '- `BROKEN` significa que a comparação independente encontrou pelo menos um `MISMATCH` de campo ou publicação; não significa indisponibilidade do portal.',
        '- `NOT_AUDITED` não é sucesso nem falha: indica que a evidência independente não atingiu os critérios de identidade, domínio e quantidade.',
        '- `EMPTY_VERIFIED` só foi mantido quando havia marcador explícito, aba/API observável ou métrica independente estruturada; um zero produzido apenas pelo crawler não foi aceito.',
        '- A codificação exibida em alguns portais legados pode ser limitada pelo próprio conteúdo HTTP; a auditoria registra o texto obtido e não inventa acentos ou valores ausentes.',
        '- Não houve promoção de valores crawler-only para evidência independente.',
    ]
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> None:
    before_path = BACKEND_ROOT / 'audit_live_99_before_deep_resolution.json'
    after_path = BACKEND_ROOT / 'audit_live_99.json'
    out_path = BACKEND_ROOT / 'docs' / 'LIVE_AUDIT_DEEP_RESOLUTION.md'
    before = load_json(before_path)
    after = load_json(after_path)
    if len(after.get('sources', [])) != 99:
        raise ValueError('O payload final não contém exatamente 99 fontes')
    generate(before, after, out_path)
    print(f'Generated {out_path}')


if __name__ == '__main__':
    main()
