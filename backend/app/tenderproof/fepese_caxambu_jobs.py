"""Extract the explicit FEPESE Caxambu do Sul cargo tables."""

from __future__ import annotations

import re

from app.tenderproof.contracts import ExtractedField, FieldState

EXPECTED_SOURCE = "fepese_open"
EXPECTED_EXTERNAL_ID = "2026pscaxambudosul"
EXPECTED_ARTIFACT_SHA256 = "a23c6ecd25f7a80d1bf6ed790673082f21bf45936ef64e1573856448be08dc11"

MONEY = re.compile(r"\d{1,3}(?:\.\d{3})*,\d{2}")


def _flat(text: str) -> str:
    return " ".join(text.split())


def _money(value: str) -> str:
    return f"{float(value.replace('.', '').replace(',', '.')):.2f}"


SUPERIOR = [
    "Advogado", "Analista Jurídico", "Assistente Social", "Enfermeiro", "Engenheiro Agrônomo",
    "Engenheiro Civil", "Farmacêutico", "Fisioterapeuta", "Médico ESF", "Nutricionista",
    "Odontólogo", "Psicólogo",
]
MEDIO = ["Agente Comunitário de Saúde", "Agente de Controle de Endemias", "Assistente Administrativo",
         "Técnico de Enfermagem", "Técnico em Informática", "Técnico em Saúde Bucal"]
FUNDAMENTAL = ["Motorista", "Operador de Máquinas"]


def _find_page(pages, heading: str):
    return next((page for page in pages if heading.casefold() in _flat(page.text).casefold()), None)


def _extract_rows(text, labels):
    flat = _flat(text)
    ordered = sorted(labels, key=len, reverse=True)
    label_pattern = re.compile("(?P<name>" + "|".join(re.escape(label) for label in ordered) +
                               r")(?:[¹²³*])?\s+", re.I)
    # A job name can recur inside its own requirement (e.g. "Advogado junto
    # à Ordem" or "Curso Técnico em Informática").  Those prose mentions
    # look like row starts after flattening the PDF, so first retain only the
    # first occurrence of each known label (the table row itself).
    occurrences = []
    seen = set()
    for match in label_pattern.finditer(flat):
        key = " ".join(match["name"].split()).casefold()
        if key in seen:
            continue
        seen.add(key)
        occurrences.append(match)
    terminal_pattern = re.compile(r"\bCR\s+(?P<hours>\d{1,2}h)\s+(?P<salary>\d{1,3}(?:\.\d{3})*,\d{2})\b", re.I)
    rows = []
    for occurrence in occurrences:
        terminal = terminal_pattern.search(flat, occurrence.end())
        if terminal is None:
            body = flat[occurrence.end():]
        else:
            body = flat[occurrence.end():terminal.end()]
        rows.append({"name": occurrence["name"], "body": body})
    return rows


def extract_caxambu_jobs(
    artifact, pages, evidence, *, source: str | None = None, external_id: str | None = None,
) -> ExtractedField | None:
    if (source, external_id, artifact.sha256) != (
        EXPECTED_SOURCE, EXPECTED_EXTERNAL_ID, EXPECTED_ARTIFACT_SHA256,
    ):
        return None
    page5 = _find_page(pages, "4 CARGOS, FORMAÇÃO EXIGIDA")
    page6 = next((page for page in pages if "Tabela 4.3" in page.text and "Motorista" in page.text), None)
    if page5 is None or page6 is None:
        return None
    if page5.error or page5.truncated or page6.error or page6.truncated:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED, value=None,
                              reason="tabelas FEPESE incompletas", evidence=[])
    jobs = []
    evidences = []
    for page, labels, fee, table_label in (
        (page5, SUPERIOR, "120.00", "Tabela 4.1"),
        (page5, MEDIO, "100.00", "Tabela 4.2"),
        (page6, FUNDAMENTAL, "80.00", "Tabela 4.3"),
    ):
        flat_page = _flat(page.text)
        start = flat_page.casefold().find(table_label.casefold())
        next_tables = [flat_page.casefold().find(f"Tabela 4.{n}", start + 1) for n in (1, 2, 3, 4) if flat_page.casefold().find(f"Tabela 4.{n}", start + 1) >= 0]
        stop = min(next_tables) if next_tables else len(flat_page)
        rows = _extract_rows(flat_page[start:stop], labels)
        if len(rows) != len(labels):
            return ExtractedField(field_name="cargos", state=FieldState.FAILED, value=None,
                                  reason=f"{table_label} FEPESE parcialmente interpretada", evidence=[])
        for index, match in enumerate(rows):
            # Keep the official label from the edital contract.  Some PDF
            # glyph maps expose accented characters as U+FFFD even though
            # the row is otherwise read correctly.
            name = labels[index]
            body = " ".join(match["body"].split())
            terminal = re.search(r"\bCR\s+(?P<hours>\d{1,2}h)\s+(?P<salary>\d{1,3}(?:\.\d{3})*,\d{2})\b", body)
            if not terminal:
                return ExtractedField(field_name="cargos", state=FieldState.FAILED, value=None,
                                      reason=f"linha sem vagas, jornada ou vencimento: {name}", evidence=[])
            requirements = body[:terminal.start()].strip(" ;.")
            row_text = page.text
            needle = name.split()[0]
            start = page.text.casefold().find(needle.casefold())
            snippet = page.text if start < 0 else page.text[max(0, start - 120): min(len(page.text), start + 700)]
            fee_page = next((p for p in pages if "6.4 O valor da taxa de inscrição" in p.text), None)
            if fee_page is None:
                return ExtractedField(field_name="cargos", state=FieldState.FAILED, value=None,
                                      reason="taxas FEPESE não encontradas", evidence=[])
            evidences.extend([
                evidence(artifact=artifact, page=page, snippet=snippet),
                evidence(artifact=artifact, page=fee_page, snippet=fee_page.text[:1800]),
            ])
            jobs.append({
                "nome": name,
                "vagas_imediatas": 0,
                "cadastro_reserva": True,
                "remuneracao": _money(terminal["salary"]),
                "moeda": "BRL",
                "jornada": terminal["hours"],
                "requisitos": requirements,
                "taxa_inscricao": fee,
            })
    return ExtractedField(field_name="cargos", state=FieldState.SUPPORTED, value=jobs, evidence=evidences)
