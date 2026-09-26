"""Pinned, fail-closed IDIB Reriutaba/362 cargo extractor."""
from __future__ import annotations

import re

from .contracts import ExtractedField, FieldState

EXPECTED_SOURCE = "idib_open"
EXPECTED_EXTERNAL_ID = "362"
EXPECTED_SHA256 = "fef17aa38c078810cbfedfa999782c3d02318bd9e5fa764502b5c4bb116ab28a"
EXPECTED_BYTE_LEN = 1048994
VERSION = "idib-reriutaba-362/1"


def extract_reriutaba_prova(artifact, pages, evidence):
    page = next((p for p in pages if p.page_number == 68), None)
    snippet = "15 Realização das Provas Objetivas 06/12/2026"
    if page is None or page.error or page.truncated or "\ufffd" in (page.text if page else ""):
        return None
    start = page.text.find(snippet)
    if start < 0:
        return None
    try:
        ev = evidence(artifact=artifact, page=page, snippet=snippet)
    except AssertionError:
        return None
    return ExtractedField(field_name="prova_data", state=FieldState.SUPPORTED,
                          value="2026-12-06", original_value="06/12/2026", evidence=[ev])


def _row(text: str) -> str | None:
    match = re.search(r"Guarda\s*\nCivil\s*\nMunicipal\s*\n40h\s*\n09\s*\n0?6\s*\n0?1\s*\n0?2\s*\n0\s*\n0\s*\n11\s*\nEnsino M.dio\s*\nCompleto\s*\nSal.rio-M.nimo\s*\+\s*\n30%\s*\n\(periculosidade\)\s*\+\s*\nAdicional Noturno", text, re.I)
    return match.group(0).strip() if match else None


def extract_reriutaba_jobs(artifact, pages, evidence, *, source: str, external_id: str):
    if (source, external_id, artifact.sha256, artifact.byte_len) != (
        EXPECTED_SOURCE, EXPECTED_EXTERNAL_ID, EXPECTED_SHA256, EXPECTED_BYTE_LEN,
    ):
        return None
    selected = [p for p in pages if p.page_number in (3, 72)]
    if len(selected) != 2 or any(p.error or p.truncated for p in selected):
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="IDIB Reriutaba: páginas 3 e 72 ausentes, com erro ou truncadas")
    if any("\ufffd" in p.text for p in selected):
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="IDIB Reriutaba: U+FFFD residual no texto preservado")
    snippets = [_row(p.text) for p in selected]
    if any(s is None for s in snippets):
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="IDIB Reriutaba: linha Guarda Civil Municipal divergente")
    try:
        evidences = [evidence(artifact=artifact, page=p, snippet=s) for p, s in zip(selected, snippets)]
    except AssertionError:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="IDIB Reriutaba: evidência não é verbatim")
    jobs = [{
        "nome": "Guarda Civil Municipal",
        "vagas_imediatas": 9,
        "cadastro_reserva": 11,
        "vagas_ampla_concorrencia": 6,
        "vagas_pcd": 1,
        "vagas_ppp": 2,
        "vagas_indigenas": 0,
        "vagas_quilombolas": 0,
        "remuneracao": "salário-mínimo + 30% (periculosidade) + adicional noturno",
        "moeda": "BRL",
        "remuneracao_observacao": "mensal_variavel; base do salário-mínimo não quantificada no edital",
        "jornada": "40h semanais",
        "requisitos": "Ensino Médio Completo; CNH ou Permissão para Dirigir categoria AB ou superior",
        "taxa_inscricao": "156.67",
    }]
    return ExtractedField(field_name="cargos", state=FieldState.SUPPORTED,
                          value=jobs, evidence=evidences,
                          units={"remuneracao": "BRL/mês + adicionais explicitados no edital",
                                 "jornada": "horas semanais", "taxa_inscricao": "BRL/inscricao"})
