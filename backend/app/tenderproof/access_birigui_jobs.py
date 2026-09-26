"""Pinned, fail-closed cargo extractor for ACCESS Birigui external_id 183."""
from __future__ import annotations

import re

from .contracts import Artifact, Evidence, ExtractedField, FieldState, PageText

SOURCE = "access_open"
EXTERNAL_ID = "183"
SHA256 = "de7a554e58278416d88182054a257b4d1439a46ef0730b2cfb3f0996c3731087"
VERSION = "access-birigui-183/1"


def extract_birigui_jobs(artifact: Artifact, pages: list[PageText], evidence_factory, *, source: str, external_id: str) -> ExtractedField | None:
    if source != SOURCE or external_id != EXTERNAL_ID or artifact.sha256 != SHA256:
        return None
    page = next((p for p in pages if p.page_number == 2), None)
    if page is None:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="ACCESS Birigui: página 2 preservada ausente")
    if page.error or page.truncated:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="ACCESS Birigui: página preservada com erro/truncamento")
    text = page.text
    requirement = re.search(r"Licenciatura Plena em\s+Pedagogia ou Normal\s+Superior, ambas com\s+habilita.{0,4}o na Educa.{0,4}o\s+Infantil e nos anos iniciais do\s+Ensino Fundamental", text, re.I)
    workload = re.search(r"At.{0,3} 40 horas semanais", text, re.I)
    salary = re.search(r"R\$ 30,53 hora-\s*aula", text, re.I)
    counts = re.search(r"09 01 10", text)
    if not requirement or not workload or not salary or not counts or "Professor Auxiliar" not in text:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="ACCESS Birigui: estrutura textual do SHA esperado divergiu")
    snippets = [
        "Professor Auxiliar",
        requirement.group(0), workload.group(0), salary.group(0), counts.group(0),
    ]
    try:
        evidence = [evidence_factory(artifact=artifact, page=page, snippet=s) for s in snippets]
    except AssertionError:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="ACCESS Birigui: evidência não é verbatim no material preservado")
    return ExtractedField(
        field_name="cargos", state=FieldState.SUPPORTED,
        value=[{"nome": "Professor Auxiliar", "vagas_imediatas": 10,
                "cadastro_reserva": None, "vagas_ampla_concorrencia": 9,
                "vagas_pcd": 1, "remuneracao": "30.53", "moeda": "BRL",
                "remuneracao_observacao": "por hora-aula",
                "jornada": "até 40 horas semanais",
                "requisitos": "Licenciatura Plena em Pedagogia ou Normal Superior, ambas com habilitação na Educação Infantil e nos anos iniciais do Ensino Fundamental",
                "taxa_inscricao": None}],
        evidence=evidence,
        units={"remuneracao": "BRL/hora-aula", "jornada": "horas semanais"},
    )
