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
from urllib.parse import urlsplit, urlunsplit

from app.connectors.common import parse_money

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
    netloc = parsed.netloc.casefold()
    if netloc.endswith(':80') and scheme == 'http':
        netloc = netloc[:-3]
    if netloc.endswith(':443') and scheme == 'https':
        netloc = netloc[:-4]
    path = parsed.path.rstrip('/') or '/'
    # A fragment identifies a view on a page, not a different official URL.
    return urlunsplit((scheme, netloc, path, parsed.query, ''))


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
        parsed = parse_money(str(value))
        if parsed is not None:
            return format(parsed.normalize(), 'f')
        return _normalize_number(value)
    if field == 'vagas':
        return _normalize_number(value)
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
