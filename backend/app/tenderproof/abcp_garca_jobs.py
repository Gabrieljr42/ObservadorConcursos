"""Pinned, fail-closed ABCP Garca/2868 cargo-table extractor."""
from __future__ import annotations

import re

from .contracts import ExtractedField, FieldState

EXPECTED_SOURCE = "abcp_open"
EXPECTED_EXTERNAL_ID = "2868"
EXPECTED_SHA256 = "00dc6e0d8e560b8b0a5aae557016d7e6a169b1ebc00aeb31d7ff95babf497b2a"
EXPECTED_BYTE_LEN = 791715
VERSION = "abcp-garca-2868/1"

_UTF8_RECOVERY = {
    "C�MARA": "CÂMARA", "GAR�A": "GARÇA", "T�CNICO": "TÉCNICO",
    "m�dio": "médio", "BENEF�CIOS": "BENEFÍCIOS", "Al�m": "Além",
    "sal�rio": "salário", "C�mara": "Câmara", "benef�cio": "benefício",
    "Aux�lio": "Auxílio", "alimenta��o": "alimentação",
}


def _recover_preserved_utf8(text: str) -> str:
    """Repair only known pdftotext replacement sequences from preserved text."""
    for broken, fixed in _UTF8_RECOVERY.items():
        text = text.replace(broken, fixed)
    if "�" in text:
        raise ValueError("ABCP Garca: U+FFFD residual no texto preservado")
    return text


def extract_garca_jobs(artifact, pages, evidence, *, source: str, external_id: str):
    if (source, external_id, artifact.sha256, artifact.byte_len) != (
        EXPECTED_SOURCE, EXPECTED_EXTERNAL_ID, EXPECTED_SHA256, EXPECTED_BYTE_LEN,
    ):
        return None
    page = next((p for p in pages if p.page_number == 1), None)
    if page is None or page.error or page.truncated:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="ABCP Garca: página 1 ausente, com erro ou truncada")
    try:
        page = page.model_copy(update={"text": _recover_preserved_utf8(page.text)})
    except ValueError:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="ABCP Garca: texto preservado contém codificação não recuperável")
    text = page.text
    # The preserved text extractor linearizes the table after item 2.4.
    marker = re.search(r"001\s+T.{0,3}CNICO\s+LEGISLATIVO", text, re.I)
    if marker is None:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="ABCP Garca: linha Técnico Legislativo ausente")
    end = text.find("Objetiva", marker.start())
    row = text[marker.start():end + len("Objetiva+\nDiscursiva")] if end >= 0 else ""
    required = ("LEGISLATIVO", "01", "CR", "35 horas", "3.378,77", "BENEF")
    if not row or any(token not in row for token in required):
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="ABCP Garca: linha de cargo divergente")
    benefit_match = re.search(r"2\.3\s+.*?R\$\s*680,00.*?Vale Transporte\.", text, re.I | re.S)
    if benefit_match is None:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="ABCP Garca: benefícios não encontrados no texto preservado")
    try:
        evidences = [
            evidence(artifact=artifact, page=page, snippet=row.strip()),
            evidence(artifact=artifact, page=page, snippet=benefit_match.group(0).strip()),
        ]
    except AssertionError:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="ABCP Garca: evidência não é verbatim")
    jobs = [{
        "nome": "Técnico Legislativo", "vagas_imediatas": 1,
        "cadastro_reserva": True, "vagas_ampla_concorrencia": 1,
        "vagas_pcd": 0, "remuneracao": "3378.77", "moeda": "BRL",
        "remuneracao_observacao": "por mês", "jornada": "35 horas semanais",
        "requisitos": "Ensino Médio completo",
        "beneficios": ["auxílio alimentação R$ 680,00", "vale-transporte"],
    }]
    return ExtractedField(field_name="cargos", state=FieldState.SUPPORTED,
                          value=jobs, evidence=evidences,
                          units={"remuneracao": "BRL/mês", "jornada": "horas semanais"})
