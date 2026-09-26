"""Pinned, fail-closed cargo table extractor for Consulplan/Unaí 2026."""
from __future__ import annotations

import re

from .contracts import ExtractedField, FieldState

EXPECTED_SOURCES = {"consulplan_open", "institutoconsulplan_open"}
EXPECTED_EXTERNAL_ID = "unai2026"
EXPECTED_SHA256 = "9bdb0e77fde501c33363ce636744b8be8107c64a996c1bde6b4aa2faa96dac32"
EXPECTED_BYTE_LEN = 565628
VERSION = "consulplan-unai-2026/5"
PROVA_VERSION = "consulplan-unai-2026/2"

_START = "Analista de Atividades da Secretaria -"
_NAMES = (
    "Analista de Atividades da Secretaria - Analista de Sistemas",
    "Analista de Atividades da Secretaria - Consultor Jurídico",
    "Analista de Atividades da Secretaria - Contador",
)

_BAD = "\ufffd"
_RECOVERY = {
    f"Analista de Atividades da Secretaria - Consultor Jur{_BAD}dico": _NAMES[1],
    f"Analista de Atividades da Secretaria - Cont{_BAD}dor": _NAMES[2],
    f"Gradua{_BAD}{_BAD}o": "Graduação", f"Ci{_BAD}ncias": "Ciências", f"Cont{_BAD}beis": "Contábeis",
    f"Jur{_BAD}dico": "Jurídico", f"{_BAD}rea": "área", f"Informa{_BAD}{_BAD}o": "Informação",
    f"Comunica{_BAD}{_BAD}o": "Comunicação", f"Minist{_BAD}rio": "Ministério", f"Educa{_BAD}{_BAD}o": "Educação",
    f"B{_BAD}sico": "Básico", f"B{_BAD}SICO": "BÁSICO", f"Aux{_BAD}lio": "Auxílio",
    f"alimenta{_BAD}{_BAD}o": "alimentação", f"Benef{_BAD}cio": "Benefício", f"remunera{_BAD}{_BAD}o": "remuneração",
    f"C{_BAD}MARA": "CÂMARA", f"Una{_BAD}": "Unaí", f"UNA{_BAD}": "UNAÍ", f"P{_BAD}BLICO": "PÚBLICO",
}


def _recover_table(text: str) -> str:
    for broken, fixed in _RECOVERY.items():
        text = text.replace(broken, fixed)
    return text


def _row(text: str, name: str, next_name: str | None) -> str | None:
    pattern = re.escape(name).replace(r"\ ", r"\s+")
    match = re.search(pattern, text)
    if match is None:
        return None
    start = match.start()
    next_match = re.search(re.escape(next_name).replace(r"\ ", r"\s+"), text[match.end():]) if next_name else re.search(r"Benefício", text[match.end():])
    end = match.end() + next_match.start() if next_match else -1
    if end < 0:
        return None
    return text[start:end].strip()


def extract_unai_jobs(artifact, pages, evidence, *, source: str, external_id: str):
    if (source not in EXPECTED_SOURCES or external_id != EXPECTED_EXTERNAL_ID
            or artifact.sha256 != EXPECTED_SHA256 or artifact.byte_len != EXPECTED_BYTE_LEN):
        return None
    page = next((p for p in pages if p.page_number == 1), None)
    if page is None or page.error or page.truncated:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="Consulplan Unaí: página 1 ausente, truncada ou com texto inválido")
    text = _recover_table(page.text)
    if _BAD in text:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="Consulplan Unaí: U+FFFD residual na tabela preservada")
    page = page.model_copy(update={"text": text})
    if not re.search(r"Analista\s+de\s+Atividades\s+da\s+Secretaria\s+-", text) or not re.search(r"VENCIMENTO\s+BÁSICO\s+\(R\$\)", text):
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="Consulplan Unaí: quadro de cargos não reconhecido")
    page2 = next((p for p in pages if p.page_number == 2), None)
    if page2 is None or page2.error or page2.truncated:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="Consulplan Unaí: início da página 2 ausente; completude não comprovada")
    page2_text = _recover_table(page2.text)
    row_starts = re.findall(r"Analista\s+de\s+Atividades\s+da\s+Secretaria\s+-", text)
    if (len(row_starts) != 3 or "I - DAS VAGAS" not in text
            or "NOTAS EXPLICATIVAS" not in text or "1.1.1" not in text or "1.1.2" not in text):
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="Consulplan Unaí: título/cardinalidade/terminador do quadro divergente")
    if not re.search(r"\b1\.2\s+O Regime Jurídico Funcional", page2_text) or re.search(r"Analista\s+de\s+Atividades\s+da\s+Secretaria\s+-", page2_text):
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="Consulplan Unaí: página 2 sugere continuação de quadro")
    rows = []
    for index, name in enumerate(_NAMES):
        row = _row(text, name, _NAMES[index + 1] if index < len(_NAMES) - 1 else None)
        if not row:
            return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                                  reason=f"Consulplan Unaí: linha ausente ({name})")
        rows.append(row)
    required = ("30 horas", "R$ 9.193,89", "Auxílio alimentação", "R$ 1.200,00",
                "vide subitem 1.1.2")
    flat_rows = [" ".join(row.split()) for row in rows]
    if any(any(token not in row for token in required) for row in flat_rows):
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="Consulplan Unaí: remuneração/jornada/benefício divergente")
    if ("Graduação em curso superior da área geral de Computação" not in flat_rows[0]
            or "Graduação em curso superior de Direito" not in flat_rows[1]
            or "Graduação em curso superior de Ciências Contábeis" not in flat_rows[2]
            or "registro na Ordem dos Advogados do Brasil" not in flat_rows[1]
            or "registro no Conselho Regional de Contabilidade" not in flat_rows[2]):
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="Consulplan Unaí: requisito de alguma linha divergente")
    try:
        evidences = [evidence(artifact=artifact, page=page, snippet=row) for row in rows]
        for ev in evidences:
            ev.method_version = VERSION
        fee_page = next((p for p in pages if p.page_number == 3), None)
        fee_snippet_match = fee_page and re.search(
            r"O valor da taxa de inscrição será de R\$ 80,00 \(oitenta reais\) para todos os cargos\.",
            fee_page.text,
        )
        if fee_page is None or fee_page.error or fee_page.truncated or fee_snippet_match is None:
            raise AssertionError("trecho uniforme de taxa p3 ausente ou divergente")
        fee_snippet = fee_snippet_match.group(0)
        for index in range(3):
            fee_ev = evidence(artifact=artifact, page=fee_page, snippet=fee_snippet,
                               json_path=f"cargos[{index}].taxa_inscricao")
            fee_ev.method_version = VERSION
            evidences.append(fee_ev)
    except AssertionError:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="Consulplan Unaí: evidência não é verbatim")
    benefits = ["auxílio alimentação R$ 1.200,00", "outros benefícios conforme subitem 1.1.2"]
    jobs = [
        {"nome": _NAMES[0], "vagas_imediatas": 1, "cadastro_reserva": True,
         "vagas_ampla_concorrencia": 1, "vagas_pcd": 0, "remuneracao": "9193.89",
         "moeda": "BRL", "remuneracao_observacao": "vencimento básico por mês",
         "jornada": "30 horas semanais", "requisitos": "Graduação em curso superior da área geral de Computação e Tecnologia da Informação e Comunicação", "beneficios": benefits, "taxa_inscricao": "80.00"},
        {"nome": _NAMES[1], "vagas_imediatas": 0, "cadastro_reserva": True,
         "vagas_ampla_concorrencia": 0, "vagas_pcd": 0, "remuneracao": "9193.89",
         "moeda": "BRL", "remuneracao_observacao": "vencimento básico por mês",
         "jornada": "30 horas semanais", "requisitos": "Graduação em curso superior de Direito e registro na Ordem dos Advogados do Brasil", "beneficios": benefits, "taxa_inscricao": "80.00"},
        {"nome": _NAMES[2], "vagas_imediatas": 1, "cadastro_reserva": True,
         "vagas_ampla_concorrencia": 1, "vagas_pcd": 0, "remuneracao": "9193.89",
         "moeda": "BRL", "remuneracao_observacao": "vencimento básico por mês",
         "jornada": "30 horas semanais", "requisitos": "Graduação em curso superior de Ciências Contábeis e registro no Conselho Regional de Contabilidade", "beneficios": benefits, "taxa_inscricao": "80.00"},
    ]
    return ExtractedField(field_name="cargos", state=FieldState.SUPPORTED, value=jobs,
                          evidence=evidences,
                          units={"remuneracao": "BRL/mês", "jornada": "horas semanais"})


def extract_unai_prova(artifact, pages, evidence, *, source: str, external_id: str):
    if (source not in EXPECTED_SOURCES or external_id != EXPECTED_EXTERNAL_ID
            or artifact.sha256 != EXPECTED_SHA256 or artifact.byte_len != EXPECTED_BYTE_LEN):
        return None
    page = next((p for p in pages if p.page_number == 31), None)
    if page is None or page.error or page.truncated:
        return ExtractedField(field_name="prova_data", state=FieldState.FAILED,
                              reason="Consulplan Unaí: página 31 ausente, truncada ou com erro")
    match = re.search(r"Realização da Prova Objetiva e Discursiva\s+10/1/2027", page.text)
    if match is None:
        return ExtractedField(field_name="prova_data", state=FieldState.FAILED,
                              reason="Consulplan Unaí: linha de prova divergente")
    snippet = match.group(0)
    try:
        ev = evidence(artifact=artifact, page=page, snippet=snippet)
    except AssertionError:
        return ExtractedField(field_name="prova_data", state=FieldState.FAILED,
                              reason="Consulplan Unaí: evidência de prova não é verbatim")
    return ExtractedField(field_name="prova_data", state=FieldState.SUPPORTED,
                          value="2027-01-10", original_value="10/1/2027", evidence=[ev],
                          units={"date": "ISO-8601", "timezone": "America/Sao_Paulo"})
