from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any


VERSIONED_FIELDS: tuple[str, ...] = (
    'titulo',
    'orgao',
    'modalidade',
    'cargo',
    'area',
    'cidade',
    'uf',
    'status',
    'vagas',
    'salario_min',
    'salario_max',
    'escolaridade',
    'taxa',
    'prova_data',
    'edital_numero',
    'edital_data',
    'inscricao_inicio',
    'inscricao_fim',
    'link_edital',
    'link_inscricao',
    'edital_pdf_text_hash',
    'edital_pdf_pages',
    'content_hash',
)

NUMERIC_MONEY_FIELDS = {'salario_min', 'salario_max', 'taxa'}
INTEGER_FIELDS = {'vagas', 'edital_pdf_pages'}
DATE_FIELDS = {'prova_data', 'edital_data', 'inscricao_inicio', 'inscricao_fim'}

LABELS: dict[str, str] = {
    'titulo': 'título',
    'orgao': 'órgão',
    'modalidade': 'modalidade',
    'cargo': 'cargo',
    'area': 'área',
    'cidade': 'cidade',
    'uf': 'UF',
    'status': 'status',
    'vagas': 'vagas',
    'salario_min': 'salário mínimo',
    'salario_max': 'salário máximo',
    'escolaridade': 'escolaridade',
    'taxa': 'taxa',
    'prova_data': 'data da prova',
    'edital_numero': 'número do edital',
    'edital_data': 'data do edital',
    'inscricao_inicio': 'início das inscrições',
    'inscricao_fim': 'fim das inscrições',
    'link_edital': 'link do edital',
    'link_inscricao': 'link de inscrição',
    'edital_pdf_text_hash': 'conteúdo do PDF do edital',
    'edital_pdf_pages': 'páginas do PDF do edital',
    'content_hash': 'hash do conteúdo bruto',
}


def jsonable(value: Any) -> Any:
    """Convert SQLAlchemy/Python values into JSON-safe values for JSONB fields."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v) for v in value]
    return value


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        # Accept both Brazilian and canonical formats.
        text = text.replace('R$', '').replace(' ', '')
        if ',' in text and '.' in text:
            text = text.replace('.', '').replace(',', '.')
        elif ',' in text:
            text = text.replace(',', '.')
    else:
        text = str(value)
    try:
        return Decimal(text).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        text = text.replace('.', '').replace(',', '')
    else:
        text = str(value)
    try:
        return int(Decimal(text))
    except (InvalidOperation, ValueError):
        return None


def normalize_for_compare(value: Any, *, field: str | None = None) -> str:
    """Normalize values before diffing.

    This avoids false positives such as Decimal('0.00') vs '0', or 1 vs '1'.
    Those false positives would otherwise create useless concurso_versions and
    eventually noisy notifications.
    """
    if field in NUMERIC_MONEY_FIELDS:
        decimal_value = _decimal_or_none(value)
        return '' if decimal_value is None else f'{decimal_value:.2f}'

    if field in INTEGER_FIELDS:
        int_value = _int_or_none(value)
        return '' if int_value is None else str(int_value)

    value = jsonable(value)
    if value is None:
        return ''

    if field in DATE_FIELDS:
        if isinstance(value, (datetime, date)):
            if isinstance(value, datetime):
                # Normalize to naive UTC representation for comparison
                return value.strftime('%Y-%m-%dT%H:%M:%S')
            return value.strftime('%Y-%m-%d')
        if isinstance(value, str):
            return value.strip().replace('+00:00', '').replace('Z', '').split('.')[0]

    if isinstance(value, str):
        return ' '.join(value.strip().split())
    return str(value)


def diff_concurso(existing: Any, new_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return a JSON-safe field diff between current DB row and newly crawled data.

    The function compares only fields that matter to users/history. It deliberately
    ignores volatile fields like fetched_at and updated_at.
    """
    changed: dict[str, dict[str, Any]] = {}

    for field in VERSIONED_FIELDS:
        old_value = getattr(existing, field, None)
        new_value = new_data.get(field)
        if normalize_for_compare(old_value, field=field) != normalize_for_compare(new_value, field=field):
            changed[field] = {
                'label': LABELS.get(field, field),
                'old': jsonable(old_value),
                'new': jsonable(new_value),
            }

    return changed


def classify_change(changed_fields: dict[str, dict[str, Any]], *, is_created: bool = False) -> str:
    if is_created:
        return 'created'
    if not changed_fields:
        return 'none'

    if 'publications_added' in changed_fields:
        return 'document_added'

    if 'status' in changed_fields:
        return 'status_changed'

    date_fields = {'inscricao_inicio', 'inscricao_fim', 'prova_data'}
    if date_fields.intersection(changed_fields):
        return 'dates_changed'

    edital_fields = {'link_edital', 'edital_pdf_text_hash', 'edital_pdf_pages', 'edital_numero', 'edital_data'}
    if edital_fields.intersection(changed_fields):
        return 'edital_changed'

    money_fields = {'salario_min', 'salario_max', 'taxa'}
    if money_fields.intersection(changed_fields):
        return 'values_changed'

    if 'vagas' in changed_fields:
        return 'vacancies_changed'

    return 'updated'


def build_change_summary(changed_fields: dict[str, dict[str, Any]], *, is_created: bool = False) -> str:
    if is_created:
        return 'Concurso cadastrado pela primeira vez.'
    if not changed_fields:
        return 'Nenhuma alteração relevante detectada.'

    messages: list[str] = []

    if 'publications_added' in changed_fields:
        item = changed_fields['publications_added']
        added = item.get('new') or []
        count = len(added) if isinstance(added, list) else 1
        if count == 1 and isinstance(added, list) and added:
            title = added[0].get('title') if isinstance(added[0], dict) else None
            messages.append(f"Nova publicação adicionada: {title or 'documento do concurso'}.")
        else:
            messages.append(f"{count} novas publicações adicionadas ao concurso.")

    if 'status' in changed_fields:
        item = changed_fields['status']
        messages.append(f"Status alterado de {item.get('old') or 'não informado'} para {item.get('new') or 'não informado'}.")

    if 'inscricao_fim' in changed_fields:
        item = changed_fields['inscricao_fim']
        messages.append(f"Fim das inscrições alterado de {item.get('old') or 'não informado'} para {item.get('new') or 'não informado'}.")

    if 'inscricao_inicio' in changed_fields:
        item = changed_fields['inscricao_inicio']
        messages.append(f"Início das inscrições alterado de {item.get('old') or 'não informado'} para {item.get('new') or 'não informado'}.")

    if 'prova_data' in changed_fields:
        item = changed_fields['prova_data']
        messages.append(f"Data da prova alterada de {item.get('old') or 'não informado'} para {item.get('new') or 'não informado'}.")

    if 'link_edital' in changed_fields:
        messages.append('Link do edital foi atualizado.')

    if 'edital_pdf_text_hash' in changed_fields:
        messages.append('Conteúdo do PDF do edital foi alterado.')

    if 'vagas' in changed_fields:
        item = changed_fields['vagas']
        messages.append(f"Quantidade de vagas alterada de {item.get('old') or 'não informado'} para {item.get('new') or 'não informado'}.")

    if 'salario_min' in changed_fields or 'salario_max' in changed_fields:
        messages.append('Faixa salarial foi atualizada.')

    if 'taxa' in changed_fields:
        messages.append('Taxa de inscrição foi atualizada.')

    if not messages:
        visible_fields = [changed_fields[k].get('label', k) for k in changed_fields if k != 'content_hash']
        if visible_fields:
            messages.append('Campos atualizados: ' + ', '.join(visible_fields[:8]) + '.')
        else:
            messages.append('Dados brutos do concurso foram atualizados.')

    return ' '.join(messages)
