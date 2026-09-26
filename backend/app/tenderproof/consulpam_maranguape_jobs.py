"""Version-pinned Consulpam Maranguape cargo transcription.

The source table is split across pages 25--29 and repeats the same ACS
salary/requirements for 42 named areas.  This adapter is intentionally
limited to the preserved SHA/source/external-id tuple below; it must not be
used for another Consulpam edital with similar labels.
"""

from __future__ import annotations

import re

from app.tenderproof.contracts import ExtractedField, FieldState

EXPECTED_SOURCE = "consulpam_open"
EXPECTED_EXTERNAL_ID = "777"
EXPECTED_ARTIFACT_SHA256 = "c6731e75b83cb25671c4b3630a5c2cce86eb2e16a21ed28ee64d56019917837d"

SALARY = "3083.89"
HOURS = "40 horas semanais"
FEE = "135.00"
ACE_REQUIREMENTS = "Ensino Médio Completo."
ACS_REQUIREMENTS = (
    "Ensino Médio Completo, e residir na área de atuação em data anterior à publicação deste edital."
)

ACS_AREAS = (
    "Área Seca I", "Área Seca II", "Área Verde I", "Área Verde II", "Novo MPE II", "Coité",
    "Outra Banda I", "Outra Banda II", "Novo MPE I", "Novo MPE III", "Parque São João",
    "Parque Santa Fé", "Centro I", "Centro II", "Guabiraba I", "Guabiraba II",
    "Stênio Gomes", "Parque Iracema", "Santos Dumont", "Novo Parque Iracema", "Gereraú",
    "Urucará", "Tabatinga I", "Tabatinga II", "Ladeira Grande/Vila Nova", "Umarizeiras",
    "Lages", "Papara I", "Papara II (Papoco)", "Cachoeira", "Jubaia",
    "Forquilha/Cajueiro", "Tanques", "Lagoa do Juvenal", "Serra do Lagêdo", "Rato",
    "São João do Amanari", "Itapebussu I", "Itapebussu II", "Amanari I", "Amanari II",
    "Penedo",
)


def _page_for_code(pages, code: int):
    marker = f"{code:03d}"
    return next((page for page in pages if re.search(rf"(?m)^\s*{marker}\s*$", page.text)), None)


def _row_snippet(page, code: int, limit: int = 650) -> str | None:
    match = re.search(rf"(?m)^\s*{code:03d}\s*$", page.text)
    if match is None:
        return None
    return page.text[match.start():match.start() + limit]


def _compact(value: str) -> str:
    # The normal PDF processor preserves a line-break hyphen in Umarizeiras
    # ("UMARIZEI-\nRAS"); compare the pinned area label without separators.
    return re.sub(r"[^\w]+", "", value.casefold(), flags=re.UNICODE)


def extract_maranguape_jobs(
    artifact, pages, evidence, *, source: str | None = None, external_id: str | None = None,
) -> ExtractedField | None:
    if (source, external_id, artifact.sha256) != (
        EXPECTED_SOURCE, EXPECTED_EXTERNAL_ID, EXPECTED_ARTIFACT_SHA256,
    ):
        return None
    if not pages or any(page.error or page.truncated for page in pages):
        return ExtractedField(field_name="cargos", state=FieldState.FAILED, value=None,
                              reason="tabelas Consulpam Maranguape incompletas", evidence=[])

    jobs = []
    evidences = []
    ace_page = _page_for_code(pages, 1)
    if ace_page is None:
        return None
    ace_snippet = _row_snippet(ace_page, 1)
    if ace_snippet is None:
        return None
    jobs.append({
        "nome": "Agente de Combate às Endemias",
        "vagas_imediatas": 28,
        "cadastro_reserva": True,
        "vagas_cadastro_reserva": 280,
        "remuneracao": SALARY,
        "moeda": "BRL",
        "jornada": HOURS,
        "requisitos": ACE_REQUIREMENTS,
        "taxa_inscricao": FEE,
    })
    evidences.append(evidence(artifact=artifact, page=ace_page, snippet=ace_snippet))

    for code, area in enumerate(ACS_AREAS, start=2):
        page = _page_for_code(pages, code)
        if page is None:
            return ExtractedField(field_name="cargos", state=FieldState.FAILED, value=None,
                                  reason=f"linha Consulpam não localizada: {code:03d}", evidence=[])
        snippet = _row_snippet(page, code)
        if snippet is None or _compact(area) not in _compact(snippet):
            return ExtractedField(field_name="cargos", state=FieldState.FAILED, value=None,
                                  reason=f"área Consulpam não corroborada: {area}", evidence=[])
        jobs.append({
            "nome": f"Agente Comunitário de Saúde (ACS) — {area}",
            "area": area,
            "vagas_imediatas": 0,
            "cadastro_reserva": True,
            "vagas_cadastro_reserva": 20,
            "remuneracao": SALARY,
            "moeda": "BRL",
            "jornada": HOURS,
            "requisitos": ACS_REQUIREMENTS,
            "taxa_inscricao": FEE,
        })
        evidences.append(evidence(artifact=artifact, page=page, snippet=snippet))

    fee_page = next((page for page in pages if re.search(r"taxa de inscri[çc][ãa]o", page.text, re.I)), None)
    if fee_page is None:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED, value=None,
                              reason="taxa Consulpam não localizada", evidence=[])
    fee_match = re.search(r"taxa de inscri[çc][ãa]o.{0,240}", fee_page.text, re.I | re.S)
    if fee_match is None:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED, value=None,
                              reason="trecho de taxa Consulpam não delimitado", evidence=[])
    fee_evidence = evidence(artifact=artifact, page=fee_page, snippet=fee_match.group(0))
    evidences.extend([fee_evidence] * len(jobs))
    return ExtractedField(field_name="cargos", state=FieldState.SUPPORTED, value=jobs, evidence=evidences)
