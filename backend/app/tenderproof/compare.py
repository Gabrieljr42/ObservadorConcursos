"""TenderProof Fase 3 — comparação baseline × TenderProof (somente leitura).

A baseline é uma observação anterior (ex.: linha ``Concurso`` lida do banco
ou snapshot explícito). Nunca é a verdade usada para validar o TenderProof,
e diferenças entre momentos distintos não são atribuídas automaticamente a
erro do crawler — ``baseline_collected_at``/``baseline_origin`` são sempre
exibidos.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.tenderproof.contracts import (
    TARGET_FIELDS,
    Agreement,
    ComparisonField,
    ComparisonResult,
    ExtractedField,
    FieldState,
)


def _fold(value: Any) -> str:
    text = " ".join(str(value).strip().split())
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).casefold()


def _norm_date(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    text = str(value).strip()
    if not text:
        return None
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    match = re.search(r"(\d{2})/(\d{2})/(\d{4})", text)
    if match:
        return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
    return _fold(text) or None


def _norm_money(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    text = str(value).strip().replace("R$", "").strip()
    if not text:
        return None
    text = text.replace(".", "").replace(",", ".") if "," in text else text
    try:
        return format(Decimal(text).normalize(), "f")
    except (InvalidOperation, ValueError):
        folded = _fold(text)
        return folded or None


def _baseline_value_for(baseline: dict[str, Any], field_name: str) -> Any | None:
    if field_name == "remuneracao":
        # Baseline canônica guarda faixa global (salario_min/max); o
        # TenderProof guarda observações com escopo. A comparação é indicativa.
        lo = _norm_money(baseline.get("salario_min"))
        hi = _norm_money(baseline.get("salario_max"))
        vals = [v for v in (lo, hi) if v]
        return " / ".join(vals) if vals else None
    if field_name in ("inscricao_inicio", "inscricao_fim", "prova_data"):
        return _norm_date(baseline.get(field_name))
    value = baseline.get(field_name)
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    return value


def _tenderproof_value_for(field: ExtractedField | None) -> Any | None:
    if field is None or field.state != FieldState.SUPPORTED:
        return None
    value = field.value
    if field.field_name in ("inscricao_inicio", "inscricao_fim", "prova_data"):
        return _norm_date(value)
    if field.field_name == "remuneracao" and isinstance(value, dict):
        return " / ".join(value.get("valores_observados") or [])
    return value


def _agree(field_name: str, baseline_value: Any | None, tp_value: Any | None) -> tuple[Agreement, str]:
    if tp_value is None:
        return Agreement.NO_EVIDENCE, "TenderProof sem evidência para o campo"
    if baseline_value is None:
        return Agreement.NO_BASELINE, "baseline sem valor para o campo"
    if field_name == "cargos":
        # Compare every typed value, including null versus false for reserve
        # places. Text folding would erase meaningful requirement differences.
        if baseline_value == tp_value:
            return Agreement.AGREE, "quadros de cargos concordam em todos os valores registrados"
        return Agreement.DIVERGE, "quadros de cargos diferentes; conferir vagas, remuneração, jornada, requisitos e taxa por cargo"
    if field_name in ("inscricao_inicio", "inscricao_fim", "prova_data"):
        left, right = _norm_date(baseline_value), _norm_date(tp_value)
    elif field_name == "remuneracao":
        # Indicativa: AGREE quando há interseção entre observações com escopo
        # e a faixa da baseline; escopos diferentes não são erro automático.
        def _money_set(raw: Any) -> set[str]:
            out: set[str] = set()
            for token in str(raw).split("/"):
                normalized = _norm_money(token)
                if normalized:
                    out.add(normalized)
            return out

        if _money_set(baseline_value) & _money_set(tp_value):
            return Agreement.AGREE, "valor observado com escopo coincide com a faixa da baseline"
        return (
            Agreement.DIVERGE,
            "valores diferentes; baseline é faixa global e TenderProof é observação com escopo — conferir contexto",
        )
    elif field_name == "edital_numero":
        left, right = _fold(baseline_value), _fold(tp_value)
    else:
        left, right = _fold(baseline_value), _fold(tp_value)
    if left == right:
        return Agreement.AGREE, "valores concordam após normalização de apresentação"
    return Agreement.DIVERGE, f"baseline {baseline_value!r} ≠ TenderProof {tp_value!r}"


def compare(
    *,
    baseline: dict[str, Any] | None,
    baseline_collected_at: datetime | None,
    baseline_origin: str,
    fields: list[ExtractedField],
) -> ComparisonResult:
    baseline = baseline or {}
    by_name = {f.field_name: f for f in fields}
    out: list[ComparisonField] = []
    for name in TARGET_FIELDS:
        field = by_name.get(name)
        b_value = _baseline_value_for(baseline, name)
        t_value = _tenderproof_value_for(field)
        agreement, explanation = _agree(name, b_value, t_value)
        if field and field.state == FieldState.CONFLICT:
            explanation = "Há evidências conflitantes; nenhum valor foi escolhido automaticamente para comparar."
        elif field and field.state == FieldState.FAILED:
            explanation = field.reason or 'Extração pendente; não foi possível determinar um valor para comparação.'
        out.append(
            ComparisonField(
                field_name=name,
                baseline_value=b_value,
                tenderproof_value=t_value,
                tenderproof_state=field.state if field else FieldState.UNKNOWN,
                agreement=agreement,
                explanation=explanation,
            )
        )
    return ComparisonResult(
        status="compared",
        baseline_collected_at=baseline_collected_at,
        baseline_origin=baseline_origin,
        fields=out,
    )
