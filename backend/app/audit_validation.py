"""Rules for comparing crawler output with independently observed live evidence.

The live audit must never infer a match from a populated crawler field.  This
module keeps that invariant in one place so the CLI, tests and future audit
consumers use the same conservative comparison semantics.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlsplit, urlunsplit

AUDIT_FIELDS = (
    'titulo', 'orgao', 'modalidade', 'cargo', 'area', 'cidade', 'uf',
    'status', 'vagas', 'salario_min', 'salario_max', 'escolaridade',
    'taxa', 'prova_data', 'edital_numero', 'edital_data',
    'inscricao_inicio', 'inscricao_fim', 'link_pagina', 'link_edital',
    'link_inscricao',
)

ALLOWED_FIELD_STATUSES = {'MATCH', 'MISMATCH', 'NULL_OK', 'UNKNOWN'}
MONEY_FIELDS = {'salario_min', 'salario_max', 'taxa'}
DATE_FIELDS = {'prova_data', 'edital_data', 'inscricao_inicio', 'inscricao_fim'}
URL_FIELDS = {'link_pagina', 'link_edital', 'link_inscricao'}
VALID_UFS = {
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS',
    'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC',
    'SP', 'SE', 'TO',
}
_BRAZILIAN_STATE_SUFFIXES = (
    'acre', 'alagoas', 'amapá', 'amapa', 'amazonas', 'bahia', 'ceará', 'ceara',
    'distrito federal', 'espírito santo', 'espirito santo', 'goiás', 'goias',
    'maranhão', 'maranhao', 'mato grosso', 'mato grosso do sul', 'minas gerais',
    'pará', 'para', 'paraíba', 'paraiba', 'paraná', 'parana', 'pernambuco',
    'piauí', 'piaui', 'rio de janeiro', 'rio grande do norte', 'rio grande do sul',
    'rondônia', 'rondonia', 'roraima', 'santa catarina', 'são paulo', 'sao paulo',
    'sergipe', 'tocantins',
)

_SEMANTIC_CITY_VALUES = {
    'inscreva', 'inscreva se', 'clique aqui', 'concurso publico',
    'processo seletivo', 'edital', 'saiba mais', 'detalhes', 'acessar',
    'online', 'leia', 'leia mais', 'ver edital', 'ver detalhes', 'confira',
}
_SEMANTIC_CITY_PREFIX = re.compile(
    r'^(?:inscreva(?:-se)?|clique(?:\s+aqui)?|acesse|saiba(?:\s+mais)?|'
    r'leia(?:\s+mais)?|confira|ver(?:\s+(?:edital|detalhes))?)\b',
    re.IGNORECASE,
)
_INVALID_EDITAL_LINK = re.compile(
    r'(?:privacy|privacidade|cookie|cookies|pol[ií]tica|policy|termos?|terms?|'
    r'aviso[-_/ ]legal|manual(?:[-_/ ]|$))',
    re.IGNORECASE,
)
_INVALID_SALARY_TEXT = re.compile(
    r'\b(?:taxa|aux[ií]lio|vale[- ]?alimenta[cç][aã]o|benef[ií]cio|'
    r'gratifica[cç][aã]o|reembolso)\b',
    re.IGNORECASE,
)


def has_value(value: object) -> bool:
    return value is not None and str(value).strip() != ''


def _fold_text(value: object) -> str:
    text = ' '.join(str(value).strip().split())
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(char for char in text if not unicodedata.combining(char))
    return text.casefold()


def _normalize_url(value: object) -> str:
    parsed = urlsplit(str(value).strip())
    scheme = parsed.scheme.casefold()
    netloc = parsed.netloc.casefold().removeprefix('www.')
    if netloc.endswith(':80') and scheme == 'http':
        netloc = netloc[:-3]
    if netloc.endswith(':443') and scheme == 'https':
        netloc = netloc[:-4]
    path = parsed.path.rstrip('/') or '/'
    # A fragment identifies a view on a page, not a different official URL.
    return urlunsplit((scheme, netloc, path, parsed.query, ''))


def _normalize_title(value: object) -> str:
    """Ignore harmless portal title suffixes such as ``- ALAGOAS``."""
    normalized = _fold_text(value)
    suffixes = '|'.join(re.escape(_fold_text(state)) for state in _BRAZILIAN_STATE_SUFFIXES)
    normalized = re.sub(rf'\s*[-–—,/ ]\s*(?:{suffixes}|[a-z]{{2}})$', '', normalized)
    return normalized.strip(' -–—,/')


def _normalize_date(value: object) -> str:
    if isinstance(value, datetime):
        # The audit compares calendar dates; portal presentation may add a
        # timezone or an optional time-of-day to the same official date.
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace('Z', '+00:00')).isoformat()
    except ValueError:
        pass
    match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', text)
    if match:
        year = int(match.group(3))
        if year < 100:
            year += 2000
        try:
            return date(year, int(match.group(2)), int(match.group(1))).isoformat()
        except ValueError:
            return text
    return _fold_text(text)


def _normalize_number(value: object) -> str:
    if isinstance(value, bool):
        return str(value).casefold()
    try:
        number = Decimal(str(value).replace(',', '.'))
        return format(number.normalize(), 'f')
    except (InvalidOperation, ValueError):
        return _fold_text(value)


def normalize_for_audit(field: str, value: object) -> str | None:
    """Normalize only presentation differences, never semantic differences."""
    if not has_value(value):
        return None
    if field in URL_FIELDS:
        return _normalize_url(value)
    if field in DATE_FIELDS:
        return _normalize_date(value)
    if field in MONEY_FIELDS:
        parsed = _coerce_decimal(value)
        if parsed is not None:
            return format(parsed.normalize(), 'f')
        return _normalize_number(value)
    if field == 'vagas':
        return _normalize_number(value)
    if field == 'titulo':
        return _normalize_title(value)
    return _fold_text(value)


def compare_field(field: str, expected: object, actual: object) -> str:
    """Compare two independently sourced values.

    ``expected`` must come from a live observation.  Callers should omit a
    field when the official site was not checked; omitted fields are UNKNOWN.
    """
    if expected is None:
        return 'NULL_OK' if not has_value(actual) else 'NULL_OK'
    if not has_value(expected):
        return 'UNKNOWN'
    if not has_value(actual):
        return 'MISMATCH'
    return 'MATCH' if normalize_for_audit(field, expected) == normalize_for_audit(field, actual) else 'MISMATCH'


def build_field_audit(
    expected: dict[str, object] | None,
    actual: dict[str, object] | None,
    *,
    known_null_fields: set[str] | list[str] | tuple[str, ...] = (),
) -> dict[str, str]:
    """Build a complete field matrix without ever treating ``actual`` as expected."""
    expected = expected if isinstance(expected, dict) else {}
    actual = actual if isinstance(actual, dict) else {}
    known_null = set(known_null_fields)
    result: dict[str, str] = {}
    for field in AUDIT_FIELDS:
        if field not in expected:
            result[field] = 'UNKNOWN'
        elif expected[field] is None:
            result[field] = 'NULL_OK' if field in known_null else 'UNKNOWN'
        else:
            result[field] = compare_field(field, expected[field], actual.get(field))
    return result


def count_statuses(field_audit: dict[str, str] | None) -> dict[str, int]:
    counts = {status: 0 for status in sorted(ALLOWED_FIELD_STATUSES)}
    for value in (field_audit or {}).values():
        if value in counts:
            counts[value] += 1
    return counts


def _coerce_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if not has_value(value):
        return None
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace('Z', '+00:00')).replace(tzinfo=None)
    except ValueError:
        pass
    match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', text)
    if not match:
        return None
    year = int(match.group(3))
    if year < 100:
        year += 2000
    try:
        return datetime(year, int(match.group(2)), int(match.group(1)))
    except ValueError:
        return None


def _coerce_decimal(value: object) -> Decimal | None:
    if isinstance(value, bool) or not has_value(value):
        return None
    if isinstance(value, Decimal):
        return value
    # Import lazily: app.connectors.__init__ imports BaseConnector, which uses
    # this module for the shared sanity gate.
    from app.connectors.common import parse_money

    parsed = parse_money(str(value))
    if parsed is not None:
        return parsed
    try:
        return Decimal(str(value).replace(',', '.'))
    except (InvalidOperation, ValueError):
        return None


def _city_is_semantic_noise(value: object) -> bool:
    folded = _fold_text(value).strip(' .-_/')
    return folded in _SEMANTIC_CITY_VALUES or bool(_SEMANTIC_CITY_PREFIX.match(folded))


def _add_diagnostic(
    diagnostics: list[dict[str, str]],
    *,
    severity: str,
    code: str,
    field: str,
    message: str,
) -> None:
    diagnostics.append({
        'severity': severity,
        'code': code,
        'field': field,
        'message': message,
    })


def validate_concurso_sanity(item: dict[str, Any] | None) -> dict[str, Any]:
    """Validate structural plausibility without inventing missing values.

    Errors identify values unsafe to persist as a concurso. Warnings retain the
    item but make suspicious extraction visible to crawl diagnostics. This is a
    deliberately conservative layer: it does not impose a maximum vacancy
    count or require optional fields that an official portal may omit.
    """
    item = item if isinstance(item, dict) else {}
    diagnostics: list[dict[str, str]] = []

    inscricao_inicio = _coerce_datetime(item.get('inscricao_inicio'))
    inscricao_fim = _coerce_datetime(item.get('inscricao_fim'))
    if has_value(item.get('inscricao_inicio')) and inscricao_inicio is None:
        _add_diagnostic(diagnostics, severity='warning', code='unparseable_date', field='inscricao_inicio', message='Data de início da inscrição não pôde ser normalizada')
    if has_value(item.get('inscricao_fim')) and inscricao_fim is None:
        _add_diagnostic(diagnostics, severity='warning', code='unparseable_date', field='inscricao_fim', message='Data de fim da inscrição não pôde ser normalizada')
    if inscricao_inicio and inscricao_fim and inscricao_inicio > inscricao_fim:
        _add_diagnostic(diagnostics, severity='error', code='inscricao_interval_inverted', field='inscricao_inicio/inscricao_fim', message='Início da inscrição é posterior ao fim')

    salario_min = _coerce_decimal(item.get('salario_min'))
    salario_max = _coerce_decimal(item.get('salario_max'))
    for field in ('salario_min', 'salario_max'):
        value = item.get(field)
        if isinstance(value, str) and _INVALID_SALARY_TEXT.search(value):
            _add_diagnostic(diagnostics, severity='error', code='salary_semantic_noise', field=field, message='Campo de salário contém taxa, auxílio, benefício ou gratificação')
    if salario_min is not None and salario_max is not None and salario_min > salario_max:
        _add_diagnostic(diagnostics, severity='error', code='salary_interval_inverted', field='salario_min/salario_max', message='Salário mínimo é superior ao salário máximo')

    uf = item.get('uf')
    if has_value(uf) and str(uf).strip().upper() not in VALID_UFS:
        _add_diagnostic(diagnostics, severity='error', code='invalid_uf', field='uf', message=f'UF fora do conjunto brasileiro válido: {uf!r}')

    cidade = item.get('cidade')
    if has_value(cidade) and _city_is_semantic_noise(cidade):
        _add_diagnostic(diagnostics, severity='error', code='semantic_city', field='cidade', message=f'Cidade parece ação/rótulo de interface: {cidade!r}')

    edital_url = item.get('link_edital')
    if has_value(edital_url) and _INVALID_EDITAL_LINK.search(str(edital_url)):
        _add_diagnostic(diagnostics, severity='error', code='invalid_edital_link', field='link_edital', message='Link de edital aponta para política, cookies, termos ou manual genérico')

    title = item.get('titulo')
    if has_value(title) and _city_is_semantic_noise(title):
        _add_diagnostic(diagnostics, severity='error', code='generic_title', field='titulo', message=f'Título parece rótulo de interface: {title!r}')

    raw_data = item.get('raw_data') if isinstance(item.get('raw_data'), dict) else {}
    publications = raw_data.get('publications') if isinstance(raw_data.get('publications'), list) else []
    # See _coerce_decimal: keep the module importable while the connectors
    # package is initializing.
    from app.publications import is_valid_publication_title

    for publication in publications:
        if not isinstance(publication, dict):
            continue
        pub_title = publication.get('title')
        if not has_value(pub_title) or not is_valid_publication_title(str(pub_title)):
            _add_diagnostic(diagnostics, severity='error', code='invalid_publication_title', field='raw_data.publications', message=f'Publicação não é um título oficial válido: {pub_title!r}')

    vagas = _coerce_decimal(item.get('vagas'))
    if vagas is not None and vagas == vagas.to_integral_value():
        vacancies = int(vagas)
        current_year = datetime.now().year
        if current_year - 1 <= vacancies <= current_year + 1:
            _add_diagnostic(diagnostics, severity='warning', code='vagas_looks_like_year', field='vagas', message=f'Número de vagas coincide com um ano: {vacancies}')
        edital_numero = str(item.get('edital_numero') or '')
        number_match = re.search(r'(?<!\d)(\d{1,5})(?:/\d{4})?', edital_numero)
        if number_match and vacancies >= 10 and vacancies == int(number_match.group(1)):
            _add_diagnostic(diagnostics, severity='warning', code='vagas_looks_like_edital_number', field='vagas', message=f'Número de vagas coincide com o número do edital: {vacancies}')
        sample_lines = raw_data.get('lines_sample') or []
        sample_text = ' '.join(str(line) for line in sample_lines if line is not None)
        if vacancies >= 1000 and re.search(rf'\b{vacancies}\b', sample_text) and re.search(r'\b(?:cep|telefone|tel\.?|fone)\b', sample_text, re.IGNORECASE):
            _add_diagnostic(diagnostics, severity='warning', code='vagas_looks_like_contact', field='vagas', message=f'Número de vagas coincide com um possível CEP/telefone')

    edital_data = _coerce_datetime(item.get('edital_data'))
    prova_data = _coerce_datetime(item.get('prova_data'))
    if has_value(item.get('prova_data')) and prova_data is None:
        _add_diagnostic(diagnostics, severity='warning', code='unparseable_date', field='prova_data', message='Data da prova não pôde ser normalizada')
    if prova_data and edital_data and prova_data < edital_data:
        _add_diagnostic(diagnostics, severity='warning', code='proof_before_notice', field='prova_data', message='Data da prova é anterior à data do edital')
    if prova_data and inscricao_inicio and prova_data < inscricao_inicio:
        _add_diagnostic(diagnostics, severity='warning', code='proof_before_registration', field='prova_data', message='Data da prova é anterior ao início das inscrições')

    errors = [diagnostic['code'] for diagnostic in diagnostics if diagnostic['severity'] == 'error']
    warnings = [diagnostic['code'] for diagnostic in diagnostics if diagnostic['severity'] == 'warning']
    return {
        'valid': not errors,
        'errors': errors,
        'warnings': warnings,
        'diagnostics': diagnostics,
    }
