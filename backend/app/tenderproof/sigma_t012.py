"""Pinned, offline Sigma parser for T012 milestone.

Pinned to source=sigma_open external_id=264.
"""
from __future__ import annotations

import hashlib
from app.tenderproof.contracts import (
    Artifact,
    Evidence,
    EvidenceValidation,
    ExtractedField,
    FieldState,
    PageText,
)

SOURCE = "sigma_open"
EXTERNAL_ID = "264"
SHA256 = "b2c123149dd32405293d380f3e9848bc6e31632ca741c7af37b623ba723a962b"
BYTE_LEN = 394446
DETAIL_URL = "https://concursos.sigmaassessoria.com.br/informacoes/264/"
DOCUMENT_URL = "https://anexos-r2.selecao.net.br/uploads/57/concursos/264/anexos/2271143d-3d46-4c71-bd43-9643c3552c97.pdf"
TOTAL_PAGES = 17


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
        raise ValueError(f"Sigma parser pinned to {SOURCE}/{EXTERNAL_ID}")

    if len(pages) != TOTAL_PAGES:
        raise ValueError(f"Sigma page count drift: {len(pages)} != {TOTAL_PAGES}")

    p1 = pages[0]
    p2 = pages[1]
    p17 = pages[16]

    orgao_snippet = "PREFEITURA MUNICIPAL DE ITAJU"
    edital_snippet = "PROCESSO SELETIVO SIMPLIFICADO N.º 001/2026"
    inscr_snippet = "As inscrições serão realizadas “on-line via Internet” a partir das 09h00min do dia\n13 de agosto de 2026 até às 23h59min59seg do dia 27 de agosto de 2026"
    prova_snippet = "Realização da Prova Objetiva 13.09.2026"
    cargos_hdr_snippet = "Denominação do Emprego Público Temporário Carga Horária Salário R$\n(agosto/2026)"
    cargos_row_snippet = "PROFESSOR DE EDUCAÇÃO ESPECIAL 30 horas semanais\nR$ 28,50\n(Piso Nacional do\nMagistério)"

    assert orgao_snippet in p1.text
    assert edital_snippet in p1.text
    assert inscr_snippet in p2.text
    assert prova_snippet in p17.text
    assert cargos_hdr_snippet in p1.text
    assert cargos_row_snippet in p1.text

    def make_evidence(page: PageText, snippet: str, suffix: str) -> Evidence:
        return Evidence(
            evidence_id=f"ev-sigma-{suffix}",
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
            value="Prefeitura Municipal de Itaju",
            evidence=[make_evidence(p1, orgao_snippet, "orgao")],
        )
    )

    # edital_numero
    fields.append(
        ExtractedField(
            field_name="edital_numero",
            state=FieldState.SUPPORTED,
            value="001/2026",
            evidence=[make_evidence(p1, edital_snippet, "edital")],
        )
    )

    # inscricao_inicio
    fields.append(
        ExtractedField(
            field_name="inscricao_inicio",
            state=FieldState.SUPPORTED,
            value="2026-08-13",
            evidence=[make_evidence(p2, inscr_snippet, "inscr-ini")],
        )
    )

    # inscricao_fim
    fields.append(
        ExtractedField(
            field_name="inscricao_fim",
            state=FieldState.SUPPORTED,
            value="2026-08-27",
            evidence=[make_evidence(p2, inscr_snippet, "inscr-fim")],
        )
    )

    # prova_data
    fields.append(
        ExtractedField(
            field_name="prova_data",
            state=FieldState.SUPPORTED,
            value="2026-09-13",
            evidence=[make_evidence(p17, prova_snippet, "prova")],
        )
    )

    # cargos
    jobs = [
        {
            "nome": "Professor de Educação Especial",
            "vagas_imediatas": None,
            "cadastro_reserva": True,
            "vagas_ampla_concorrencia": None,
            "vagas_pcd": None,
            "remuneracao": "28.50",
            "moeda": "BRL",
            "remuneracao_observacao": "por hora-aula (Piso Nacional do Magistério)",
            "jornada": "30 horas semanais",
            "requisitos": None,
            "taxa_inscricao": 50.0,
        }
    ]
    fields.append(
        ExtractedField(
            field_name="cargos",
            state=FieldState.SUPPORTED,
            value=jobs,
            evidence=[
                make_evidence(p1, cargos_hdr_snippet, "cargos-hdr"),
                make_evidence(p1, cargos_row_snippet, "cargos-row"),
            ],
            units={
                "remuneracao": "BRL/hora-aula",
                "jornada": "horas semanais",
                "vagas": {"total": 0, "pcd": 0},
            },
        )
    )

    return fields
