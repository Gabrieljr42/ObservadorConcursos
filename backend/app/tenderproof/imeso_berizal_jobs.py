"""Pinned, fail-closed IMESO Berizal/139 cargo-table extractor."""
from __future__ import annotations

import re

from .contracts import ExtractedField, FieldState

EXPECTED_SOURCE = "imeso_open"
EXPECTED_EXTERNAL_ID = "139"
EXPECTED_SHA256 = "8e6fbc48ac7f54c492cc2beba78adc9216ba25fa781ba753d3e9e410fc7dd6dc"
EXPECTED_BYTE_LEN = 597314
VERSION = "imeso-berizal-139/1"

_NAMES = [
    "Agente Comunitário de Saúde - Micro Área 1 UBS Beriza",
    "Agente Comunitário de Saúde - Micro Área 2 UBS Berizal",
    "Agente Comunitário de Saúde - Micro Área 3 UBS Beriza",
    "Agente Comunitário de Saúde - Micro Área 4 UBS Berizal",
    "Agente Comunitário de Saúde - Micro Área 5 UBS Beriza",
    "Agente Comunitário de Saúde - Micro Área 6 UBS Berizal",
    "Agente Comunitário de Saúde - Micro Área 7 UBS Berizal",
    "Agente Comunitário de Saúde - Micro Área 8 UBS Berreiros",
    "Agente Comunitário de Saúde - Micro Área 9 UBS Barreiros",
    "Agente Comunitário de Saúde - Micro Área 10 UBS Barreiros",
    "Agente Comunitário de Saúde - Micro Área 11 UBS Barreiros",
]
_REQUIREMENT = "Residir na área da comunidade que irá atuar desde a data da publicação do Edital do Processo Seletivo / Ensino Médio Completo"


def extract_berizal_jobs(artifact, pages, evidence, *, source: str, external_id: str):
    if (source, external_id, artifact.sha256, artifact.byte_len) != (
        EXPECTED_SOURCE, EXPECTED_EXTERNAL_ID, EXPECTED_SHA256, EXPECTED_BYTE_LEN,
    ):
        return None
    page = next((p for p in pages if p.page_number == 22), None)
    if page is None or page.error or page.truncated:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="IME SO Berizal: página 22 ausente, com erro ou truncada")
    text = page.text
    if "ANEXO III" not in text or "BERIZAL" not in text or "VAGAS PARA" not in text:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="IMESO Berizal: cabeçalho da tabela divergente")
    starts = [m.start() for m in re.finditer(r"(?m)^\s*(?:0[1-9]|1[01])\s+AGENTE COMUNITÁRIO DE SAÚDE", text)]
    if len(starts) != 11:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="IMESO Berizal: não foram encontradas exatamente 11 linhas")
    snippets = []
    for index, name in enumerate(_NAMES):
        end = starts[index + 1] if index < 10 else text.find("Total geral de vagas", starts[index])
        snippet = text[starts[index]:end].strip()
        suffix = name.rsplit("UBS ", 1)[1]
        if (not re.search(rf"MICRO\s+.{{0,2}}REA\s+{index + 1}\b", snippet, re.I)
                or f"UBS {suffix}".upper() not in snippet.upper()
                or not all(token in snippet for token in ("Residir na", "comunidade", "Ensino", "Completo"))
                or "R$ 120,00" not in snippet or "1+CR" not in snippet
                or " 0 " not in snippet or "R$ 3.242,00" not in snippet or "40h" not in snippet):
            return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                                  reason=f"IMESO Berizal: linha {index + 1} divergiu")
        snippets.append(snippet)
    try:
        evidences = [evidence(artifact=artifact, page=page, snippet=snippet) for snippet in snippets]
    except AssertionError:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="IMESO Berizal: evidência não é verbatim")
    jobs = [{"nome": name, "vagas_imediatas": 1, "cadastro_reserva": True,
             "vagas_ampla_concorrencia": 1, "vagas_pcd": 0,
             "remuneracao": "3242.00", "moeda": "BRL", "remuneracao_observacao": "por mês",
             "jornada": "40h semanais", "requisitos": _REQUIREMENT,
             "taxa_inscricao": "120.00"} for name in _NAMES]
    return ExtractedField(field_name="cargos", state=FieldState.SUPPORTED,
                          value=jobs, evidence=evidences,
                          units={"remuneracao": "BRL/mês", "jornada": "horas semanais"})
