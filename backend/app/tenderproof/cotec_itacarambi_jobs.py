"""Version-pinned cargo transcription for COTEC Itacarambi concurso 27.

The cargo table is a separate Anexo I artifact.  This module deliberately
accepts only the exact source/candidate/artifact tuple and never treats a
similarly named COTEC table as interchangeable.
"""

from __future__ import annotations

from app.tenderproof.contracts import ExtractedField, FieldState


EXPECTED_SOURCE = "cotec_open"
EXPECTED_EXTERNAL_ID = "32"
EXPECTED_ARTIFACT_SHA256 = (
    "739b4efa17c3ab3b85cdb50a70da7c3c34d38487612eefb849a59a8b8d7a00b4"
)
EXPECTED_URL = (
    "https://anexos-r2.selecao.net.br/uploads/846/concursos/32/anexos/"
    "26f6b740-d572-4213-b269-7d88674780b9.pdf"
)


def _table_snippet(page_text: str) -> str | None:
    start = page_text.find("CÓD.")
    end_marker = "CR – Cadastro de Reserva."
    end = page_text.find(end_marker, start)
    if start < 0 or end < 0:
        return None
    return page_text[start : end + len(end_marker)]


def extract_itacarambi_jobs(
    artifact,
    pages,
    evidence,
    *,
    source: str | None = None,
    external_id: str | None = None,
    schema_version: str = "v1",
) -> ExtractedField | None:
    """Return the reviewed table only for the preserved Itacarambi Anexo I."""

    if (source, external_id, artifact.sha256) != (
        EXPECTED_SOURCE,
        EXPECTED_EXTERNAL_ID,
        EXPECTED_ARTIFACT_SHA256,
    ):
        return None
    page = next((item for item in pages if item.page_number == 1), None)
    if page is None or page.error or page.truncated:
        return ExtractedField(
            field_name="cargos",
            state=FieldState.FAILED,
            reason="Anexo I COTEC ausente ou página incompleta.",
        )
    required = (
        "CÂMARA MUNICIPAL DE ITACARAMBI - MG",
        "EDITAL 01/2026",
        "ANEXO I - ESPECIFICAÇÃO DOS CARGOS",
        "01 Agente Administrativo",
        "02 Auxiliar de Serviços Gerais**",
        "03 Controlador Interno",
        "04 Motorista**",
        "05 Técnico Legislativo",
        "06 Telefonista/Recepcionista",
        "07 Vigia",
        "R$ 3.737,48",
        "R$ 3.203,55",
        "Escala de",
        "12h x 36h",
        "CR – Cadastro de Reserva.",
    )
    snippet = _table_snippet(page.text)
    if snippet is None or any(token not in page.text for token in required):
        return ExtractedField(
            field_name="cargos",
            state=FieldState.FAILED,
            reason="Tabela do Anexo I COTEC não foi reproduzida integralmente.",
        )

    def row(name, immediate, salary, fee, requirement, hours):
        result = {
            "nome": name,
            "vagas_imediatas": immediate,
            "cadastro_reserva": True,
            "remuneracao": salary,
            "moeda": "BRL",
            "jornada": hours,
            "requisitos": requirement,
            "taxa_inscricao": fee,
        }
        if schema_version == "v2":
            if immediate:
                result.update({
                    "cadastro_reserva": False,
                    "vagas_pcd_reserva": "CR",
                    "cadastro_reserva_observacao": (
                        "Reserva PcD 10%; quantidade não especificada na coluna PcD; "
                        "a coluna geral informa 1 vaga imediata."
                    ),
                })
            else:
                result.update({
                    "vagas_pcd_reserva": "CR",
                    "cadastro_reserva_observacao": (
                        "Cadastro de reserva geral e reserva PcD 10%; sem vaga imediata."
                    ),
                })
        elif schema_version != "v1":
            raise ValueError(f"versão de esquema COTEC desconhecida: {schema_version}")
        return result

    jobs = [
        row("Agente Administrativo", 1, "1621.00", "75.00",
            "Ensino Médio Completo e conhecimentos básicos de informática.",
            "30 horas semanais"),
        row("Auxiliar de Serviços Gerais", 0, "1621.00", "65.00",
            "Ensino Fundamental Completo", "30 horas semanais"),
        row("Controlador Interno", 1, "3737.48", "95.00",
            "Ensino Superior Completo em Administração, Ciências Contábeis, Economia ou Direito.",
            "30 horas semanais"),
        row("Motorista", 0, "1965.45", "75.00",
            "Ensino Médio Completo e CNH na categoria “D”.", "30 horas semanais"),
        row("Técnico Legislativo", 1, "3203.55", "75.00",
            "Ensino Médio Completo e conhecimentos básicos de informática.",
            "30 horas semanais"),
        row("Telefonista/Recepcionista", 1, "1621.00", "75.00",
            "Ensino Médio Completo e conhecimentos básicos de informática.",
            "30 horas semanais"),
        row("Vigia", 1, "1621.00", "65.00",
            "Ensino Fundamental Completo", "Escala de 12h x 36h"),
    ]
    item = evidence(artifact=artifact, page=page, snippet=snippet)
    return ExtractedField(
        field_name="cargos",
        state=FieldState.SUPPORTED,
        value=jobs,
        reason=(
            "Quadro literal do Anexo I. TOTAIS GERAIS e RESERVA PCD 10% "
            "aparecem como CR onde o edital não informa quantidade; os cargos "
            "marcados exclusivamente para cadastro de reserva têm 0 vagas imediatas."
        ),
        evidence=[item] * len(jobs),
    )


def extract_itacarambi_jobs_v2(artifact, pages, evidence, *, source=None, external_id=None):
    return extract_itacarambi_jobs(
        artifact,
        pages,
        evidence,
        source=source,
        external_id=external_id,
        schema_version="v2",
    )
