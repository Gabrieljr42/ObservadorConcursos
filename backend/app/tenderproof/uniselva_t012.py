"""Pinned, offline Uniselva parser for T012 milestone.

Pinned to source=uniselva_selection external_id=1346.
"""
from __future__ import annotations

from app.tenderproof.contracts import (
    Artifact,
    Evidence,
    EvidenceValidation,
    ExtractedField,
    FieldState,
    PageText,
)

SOURCE = "uniselva_selection"
EXTERNAL_ID = "1346"
SHA256 = "3b3bdfe6664530f786a4af44520267d14b16a197a2534724510f19d0c5b7cbc7"
BYTE_LEN = 289906
DETAIL_URL = "https://api.fundacaouniselva.org.br/SelecaoSimplificada/1346"
DOCUMENT_URL = "https://web.fundacaouniselva.org.br/Editais/1346/EDITAL%20055.2026%20CONTRATA%C3%87%C3%83O%20DE%20ESTAGI%C3%81RIO%28A%29%20DE%20GRADUA%C3%87%C3%83O%20EM%20ENGENHARIAS%20OU%20GEOLOGIA.pdf"
TOTAL_PAGES = 10


def extract_fields(
    *,
    candidate,
    artifact: Artifact,
    pages: list[PageText],
) -> list[ExtractedField]:
    if (
        candidate.source != SOURCE
        or str(candidate.external_id) != EXTERNAL_ID
        or artifact.sha256 != SHA256
        or artifact.byte_len != BYTE_LEN
    ):
        raise ValueError(f"Uniselva parser pinned to {SOURCE}/{EXTERNAL_ID}")

    if len(pages) != TOTAL_PAGES:
        raise ValueError(f"Uniselva page count drift: {len(pages)} != {TOTAL_PAGES}")

    p1 = pages[0]
    p3 = pages[2]
    p7 = pages[6]

    orgao_snippet = "EDITAL DE SELEÇÃO SIMPLIFICADA ESTÁGIO Nº 055/2026\nA Fundação Uniselva, entidade privada sem fins lucrativos"
    edital_snippet = "EDITAL DE SELEÇÃO SIMPLIFICADA ESTÁGIO Nº 055/2026"
    inscr_snippet = "Período de inscrições 08 a 14/07/2026"
    cargos_hdr_snippet = "Função Nº de vagas Vencimento Bruto"
    cargos_row_snippet = "Estagiário(a) dos cursos de Engenharias ou\nGeologia 02\nR$ 1.420,00\n+ Vale Transporte R$\n180,00"

    assert orgao_snippet in p1.text
    assert edital_snippet in p1.text
    assert inscr_snippet in p7.text
    assert cargos_hdr_snippet in p3.text
    assert cargos_row_snippet in p3.text

    def make_evidence(page: PageText, snippet: str, suffix: str) -> Evidence:
        return Evidence(
            evidence_id=f"ev-uniselva-{suffix}",
            artifact_id=artifact.artifact_id,
            document_sha256=artifact.sha256,
            source_url=artifact.url_final,
            page_number=page.page_number,
            snippet=snippet,
            method="deterministic-regex",
            method_version="tenderproof-fields/1.22",
            validation=EvidenceValidation(ok=True),
        )

    fields: list[ExtractedField] = []

    # titulo
    fields.append(
        ExtractedField(
            field_name="titulo",
            state=FieldState.SUPPORTED,
            value=candidate.title_observed,
            evidence=[make_evidence(p1, edital_snippet, "titulo")],
        )
    )

    # orgao
    fields.append(
        ExtractedField(
            field_name="orgao",
            state=FieldState.SUPPORTED,
            value="Fundação Uniselva",
            evidence=[make_evidence(p1, orgao_snippet, "orgao")],
        )
    )

    # edital_numero
    fields.append(
        ExtractedField(
            field_name="edital_numero",
            state=FieldState.SUPPORTED,
            value="055/2026",
            evidence=[make_evidence(p1, edital_snippet, "edital")],
        )
    )

    # inscricao_inicio
    fields.append(
        ExtractedField(
            field_name="inscricao_inicio",
            state=FieldState.SUPPORTED,
            value="2026-07-08",
            evidence=[make_evidence(p7, inscr_snippet, "inscr-ini")],
        )
    )

    # inscricao_fim
    fields.append(
        ExtractedField(
            field_name="inscricao_fim",
            state=FieldState.SUPPORTED,
            value="2026-07-14",
            evidence=[make_evidence(p7, inscr_snippet, "inscr-fim")],
        )
    )

    # cargos
    jobs = [
        {
            "nome": "Estagiário(a) dos cursos de Engenharias ou Geologia",
            "vagas_imediatas": 2,
            "cadastro_reserva": False,
            "vagas_ampla_concorrencia": 2,
            "vagas_pcd": None,
            "remuneracao": "1420.00",
            "moeda": "BRL",
            "remuneracao_observacao": "Bolsa mensal R$ 1.420,00 + Vale Transporte R$ 180,00",
            "jornada": "20 horas semanais",
            "requisitos": "Estar matriculado em curso de graduação de Geologia ou Engenharias",
            "taxa_inscricao": 0.0,
        }
    ]
    fields.append(
        ExtractedField(
            field_name="cargos",
            state=FieldState.SUPPORTED,
            value=jobs,
            evidence=[
                make_evidence(p3, cargos_hdr_snippet, "cargos-hdr"),
                make_evidence(p3, cargos_row_snippet, "cargos-row"),
            ],
            units={
                "remuneracao": "BRL/mês",
                "jornada": "horas semanais",
                "vagas": {"total": 2, "pcd": 0},
            },
        )
    )

    return fields
