"""Extract Cebraspe Ponta Porã's profiles and vacancy matrix.

The edital has seven numbered prose profiles (pages 1–5) and a separate
matrix (page 6).  This adapter links both by cargo number and never derives a
global salary or vacancy value.
"""

from __future__ import annotations

import re

from app.tenderproof.contracts import ExtractedField, FieldState

MONEY = r"(?:\d{1,3}(?:\.\d{3})+|\d+),\d{2}"
EXPECTED_SOURCE = "cebraspe_open"
EXPECTED_EXTERNAL_ID = "CAMARA_MUNICIPAL_PONTAPORA_MS_26"
EXPECTED_ARTIFACT_SHA256 = "d09cd7a25a66696b4f30b718ee5a0acc3867b6f1892ec1f5c33c3efca6b2dd49"

CANONICAL_NAMES = {
    "1": "ANALISTA DE LICITAÇÃO E CONTRATOS",
    "2": "ANALISTA DE SISTEMAS",
    "3": "CONSULTOR LEGISLATIVO",
    "4": "CONTADOR",
    "5": "CONTROLADOR INTERNO",
    "6": "TÉCNICO EM INFORMÁTICA",
    "7": "ASSISTENTE ADMINISTRATIVO",
}
FEE_BY_ID = {"1": "200.00", "2": "200.00", "3": "200.00", "4": "200.00", "5": "200.00", "6": "140.00", "7": "120.00"}


def _flat(text: str) -> str:
    return " ".join(text.split())


def _money(value: str) -> str:
    return f"{float(value.replace('.', '').replace(',', '.')):.2f}"


def _page_for(spans, start: int, end: int):
    for a, b, page in spans:
        if max(a, start) < min(b, end):
            return page
    return spans[0][2]


def _page_snippet(page, anchor: str, limit: int = 5000) -> str:
    """Return a verbatim snippet from one physical page.

    Profile records can cross a page boundary in the flattened text.  An
    evidence snippet must still be contained in the page selected for it, so
    use the page text itself instead of a cross-page slice.
    """
    text = page.text
    position = text.casefold().find(anchor.casefold()) if anchor else 0
    if position < 0:
        position = 0
    return text[position:position + limit]


def extract_ponta_pora_jobs(
    artifact, pages, evidence, *, source: str | None = None, external_id: str | None = None,
) -> ExtractedField | None:
    if (source, external_id, artifact.sha256) != (
        EXPECTED_SOURCE, EXPECTED_EXTERNAL_ID, EXPECTED_ARTIFACT_SHA256,
    ):
        return None
    if not pages or any(page.error or page.truncated for page in pages):
        return ExtractedField(field_name="cargos", state=FieldState.FAILED, value=None,
                              reason="páginas do edital Cebraspe incompletas", evidence=[])
    text = ""
    spans = []
    for page in pages:
        start = len(text)
        text += page.text + "\n"
        spans.append((start, len(text), page))

    profile_re = re.compile(
        r"CARGO\s+(?P<id>\d+)\s*:\s*(?P<name>[^\n]+?)\s+"
        r"REQUISITO(?:S)?\s*:\s*(?P<requirements>.*?)\s+"
        r"DESCRI[ÇC][ÃA]O\s+SUM[ÁA]RIA\s+DA\s*S\s+ATIVIDADES:\s*.*?\s+"
        r"REMUNERA[ÇC][ÃA]O:\s*R\$\s*(?P<salary>" + MONEY + r")\.\s*"
        r"JORNADA\s+DE\s+TRABALHO:\s*(?P<hours>\d+\s+horas\s+semanais)\.",
        re.I | re.S,
    )
    profiles = list(profile_re.finditer(text))
    if len(profiles) != 7:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED, value=None,
                              reason=f"perfis Cebraspe incompletos: esperados 7, encontrados {len(profiles)}",
                              evidence=[])

    matrix_start = re.search(r"4\s+DAS\s+VAGAS\b", text, re.I)
    matrix_end = re.search(r"5\s+DAS\s+RESERVAS\s+DE\s+VAGAS\b", text, re.I)
    if not matrix_start or not matrix_end or matrix_start.end() >= matrix_end.start():
        return ExtractedField(field_name="cargos", state=FieldState.FAILED, value=None,
                              reason="matriz de vagas Cebraspe não delimitada", evidence=[])
    fee_page = next((page for page in pages if re.search(r"6\.1\s+TAXAS", page.text, re.I)), None)
    if fee_page is None:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED, value=None,
                              reason="taxas Cebraspe não localizadas", evidence=[])
    fee_match = re.search(r"6\.1\s+TAXAS:.*?(?=6\.2\s+Será admitida)", fee_page.text, re.I | re.S)
    if fee_match is None:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED, value=None,
                              reason="trecho de taxas Cebraspe não delimitado", evidence=[])
    fee_snippet = fee_match.group(0)
    matrix = text[matrix_start.end():matrix_end.start()]
    row_re = re.compile(
        r"Cargo\s+(?P<id>\d+)\s*:\s*(?P<name>.+?)\s+"
        r"(?P<ac>\d+|\*)\s+(?P<pcd>\d+|\*)\s+(?P<pp>\d+|\*)\s+"
        r"(?P<pi>\d+|\*)\s+(?P<pq>\d+|\*)\s+(?P<total>\d+)",
        re.I,
    )
    matrix_rows = {match["id"]: match for match in row_re.finditer(matrix)}
    if set(matrix_rows) != {str(index) for index in range(1, 8)}:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED, value=None,
                              reason="matriz de vagas Cebraspe parcialmente interpretada", evidence=[])

    jobs = []
    evidences = []
    for profile in profiles:
        ident = profile["id"]
        row = matrix_rows[ident]
        name = CANONICAL_NAMES[ident]
        profile_name = " ".join(profile["name"].split())
        row_name = " ".join(row["name"].split())
        if profile_name.casefold() != row_name.casefold():
            return ExtractedField(field_name="cargos", state=FieldState.FAILED, value=None,
                                  reason=f"nome divergente entre perfil e matriz no cargo {ident}", evidence=[])
        numbers = [row[key] for key in ("ac", "pcd", "pp", "pi", "pq")]
        immediate = int(row["total"])
        if sum(int(value) for value in numbers if value != "*") != immediate:
            return ExtractedField(field_name="cargos", state=FieldState.FAILED, value=None,
                                  reason=f"total de vagas inconsistente no cargo {ident}", evidence=[])
        profile_page = _page_for(spans, profile.start(), profile.end())
        matrix_offset = matrix_start.end() + row.start()
        matrix_page = _page_for(spans, matrix_offset, matrix_start.end() + row.end())
        evidences.append(evidence(
            artifact=artifact,
            page=profile_page,
            snippet=_page_snippet(profile_page, f"CARGO {ident}:"),
        ))
        evidences.append(evidence(
            artifact=artifact,
            page=matrix_page,
            snippet=_page_snippet(matrix_page, f"Cargo {ident}:"),
        ))
        evidences.append(evidence(artifact=artifact, page=fee_page, snippet=fee_snippet))
        jobs.append({
            "nome": name,
            "vagas_imediatas": immediate,
            "cadastro_reserva": "*" in numbers,
            "remuneracao": _money(profile["salary"]),
            "moeda": "BRL",
            "jornada": " ".join(profile["hours"].split()),
            "requisitos": " ".join(profile["requirements"].split()),
            "taxa_inscricao": FEE_BY_ID[ident],
        })
    return ExtractedField(field_name="cargos", state=FieldState.SUPPORTED, value=jobs, evidence=evidences)
