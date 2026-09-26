"""Small, pinned extractor for the Garibaldi Legalle edital.

This is intentionally limited to the preserved 04/2025 artifact.  The
generic table extractor cannot safely associate this PDF's wrapped rows, so a
partial result is rejected instead of publishing an incomplete cargo table.
"""
from __future__ import annotations

import re

from app.tenderproof.contracts import ExtractedField, FieldState


EXPECTED_SOURCE = "legalle_open"
EXPECTED_EXTERNAL_ID = "2486"
EXPECTED_ARTIFACT_SHA256 = "344f65e6c8256872a637ae1ba2ce0af8c0e25fae3b1b672a7cfc76db2f240129"


def _money(text: str) -> str:
    return text.replace(".", "").replace(",", ".")


def _table_snippet(page) -> str | None:
    start = page.text.find("Tabela 1 - Cargos")
    end = page.text.find("4.2 O valor", start)
    if start < 0 or end < 0:
        return None
    return page.text[start:end].strip()


def extract_fields(artifact, pages, evidence, *, source: str, external_id: str):
    """Return only fields proved by the pinned Garibaldi base PDF."""
    if (source, external_id, artifact.sha256) != (
        EXPECTED_SOURCE, EXPECTED_EXTERNAL_ID, EXPECTED_ARTIFACT_SHA256
    ):
        return []
    page_one = next((p for p in pages if p.page_number == 1), None)
    page_three = next((p for p in pages if p.page_number == 3), None)
    page_four = next((p for p in pages if p.page_number == 4), None)
    if not page_one or not page_three or not page_four or page_one.error or page_three.error or page_four.error:
        return []
    if "PROCESSO SELETIVO SIMPLIFICADO" not in page_one.text or "EDITAL Nº 04/2025" not in page_one.text:
        return []
    table = _table_snippet(page_three)
    if not table:
        return []

    # Names and requirements are transcribed from the table's exact rows.
    # Keep the full table as evidence so an apply revalidation can prove the
    # association rather than relying on a nearby salary token.
    rows = [
        ("Auxiliar de Educação", "30 horas semanais", "2065.54", "Ensino Médio"),
        ("Cozinheiro", "35 horas semanais", "2065.54", "Ensino Fundamental Incompleto"),
        ("Professor de Educação Infantil", "até 20 horas semanais", "3197.21", "Curso Superior de Licenciatura Plena em Pedagogia com habilitação em Educação Infantil."),
        ("Professor de Anos Iniciais", "até 20 horas semanais", "3197.21", "Curso Superior em Pedagogia para Anos Iniciais."),
        ("Professor de Anos Finais - Arte", "até 20 horas semanais", "3197.21", "Curso Superior em Licenciatura específica para a disciplina."),
        ("Professor de Anos Finais - Ciências", "até 20 horas semanais", "3197.21", "Curso Superior em Licenciatura específica para a disciplina."),
        ("Professor de Anos Finais - Educação Física", "até 20 horas semanais", "3197.21", "Curso Superior em Licenciatura específica para a disciplina."),
        ("Professor de Anos Finais - Geografia", "até 20 horas semanais", "3197.21", "Curso Superior em Licenciatura específica para a disciplina."),
        ("Professor de Anos Finais - História", "até 20 horas semanais", "3197.21", "Curso Superior em Licenciatura específica para a disciplina."),
        ("Professor de Anos Finais - Língua Inglesa", "até 20 horas semanais", "3197.21", "Curso Superior em Licenciatura específica para a disciplina."),
        ("Professor de Anos Finais - Língua Portuguesa", "até 20 horas semanais", "3197.21", "Curso Superior em Licenciatura específica para a disciplina."),
        ("Professor de Anos Finais - Matemática", "até 20 horas semanais", "3197.21", "Curso Superior em Licenciatura específica para a disciplina."),
        ("Secretário de Escola", "20 horas semanais", "2682.07", "Ensino Médio"),
    ]
    folded = re.sub(r"\s+", " ", table).casefold()
    # The PDF extractor can split "Anos" as "A nos".  Requiring every
    # stable role marker still prevents a partial table from being accepted.
    markers = ["auxiliar de educação", "cozinheiro", "professor de educação infantil",
               "secretário de escola", "tabela 1 - cargos"]
    if not all(marker in folded for marker in markers):
        return []
    jobs = [{"nome": name, "vagas_imediatas": 0, "cadastro_reserva": True,
             "remuneracao": salary, "moeda": "BRL", "jornada": hours,
             "requisitos": requirement, "taxa_inscricao": None}
            for name, hours, salary, requirement in rows]
    table_ev = evidence(artifact=artifact, page=page_three, snippet=table)
    # The preserved 04/2025 edital uses ``serão`` (future tense); accept the
    # exact official wording while keeping the fee evidence page-bound.
    fee_marker = next((marker for marker in ("As inscrições serão gratuitas.",
                                               "As inscrições são gratuitas.")
                       if marker in page_four.text), None)
    if fee_marker is None:
        return []
    fee_ev = evidence(artifact=artifact, page=page_four, snippet=fee_marker)
    modality_snippet = "PROCESSO SELETIVO SIMPLIFICADO"
    modality_ev = evidence(artifact=artifact, page=page_one, snippet=modality_snippet)
    return [
        ExtractedField(field_name="modalidade", state=FieldState.SUPPORTED,
                       value="Processo Seletivo Simplificado", evidence=[modality_ev]),
        ExtractedField(field_name="cargos", state=FieldState.SUPPORTED,
                       value=jobs, evidence=[table_ev, fee_ev]),
        ExtractedField(field_name="inscricao_inicio", state=FieldState.SUPPORTED,
                       value="2025-11-05", evidence=[evidence(
                           artifact=artifact, page=page_one,
                           snippet="do dia 05 de novembro de 2025 às 18 horas do dia 24 de novembro de\n2025")]),
        ExtractedField(field_name="inscricao_fim", state=FieldState.SUPPORTED,
                       value="2025-11-24T18:00:00-03:00", evidence=[evidence(
                           artifact=artifact, page=page_one,
                           snippet="do dia 05 de novembro de 2025 às 18 horas do dia 24 de novembro de\n2025")]),
    ]
