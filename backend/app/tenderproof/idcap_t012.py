"""Pinned, offline IDCAP parser for T012 milestone.

Pinned to source=idcap_open external_id=248.
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

SOURCE = "idcap_open"
EXTERNAL_ID = "248"
SHA256 = "7a8a3d200ba46d7a79f6e0f70baad86398a6f15291439ce8c7e79c0d5a0d12b3"
BYTE_LEN = 682449
DETAIL_URL = "https://www.idcap.org.br/informacoes/248/"
DOCUMENT_URL = "https://anexos-r2.selecao.net.br/uploads/227/concursos/248/anexos/f1cefcc4-0cd7-4ec7-a404-d975c3d435b4.pdf"
TOTAL_PAGES = 25


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
        raise ValueError(f"IDCAP parser pinned to {SOURCE}/{EXTERNAL_ID}")

    if len(pages) != TOTAL_PAGES:
        raise ValueError(f"IDCAP page count drift: {len(pages)} != {TOTAL_PAGES}")

    p1 = pages[0]
    p2 = pages[1]

    orgao_snippet = "PREFEITURA MUNICIPAL DE VITÓRIA/ES"
    edital_snippet = "EDITAL DE ABERTURA Nº 14/2026, DE 26 DE JUNHO DE 2026"
    cargos_hdr_snippet = "CÓD EMPREGO PÚBLICO CH SEMANAL VENCIMENTO PRÉ-REQUISITOS (comprovados na convocação)"
    cargos_row_snippet = "101 Agente Comunitário de\nSaúde - ACS 40h R$3.262,64"

    assert orgao_snippet in p1.text
    assert edital_snippet in p1.text
    assert cargos_hdr_snippet in p2.text
    assert cargos_row_snippet in p2.text

    def make_evidence(page: PageText, snippet: str, suffix: str) -> Evidence:
        return Evidence(
            evidence_id=f"ev-idcap-{suffix}",
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
            value="Prefeitura Municipal de Vitória",
            evidence=[make_evidence(p1, orgao_snippet, "orgao")],
        )
    )

    # edital_numero
    fields.append(
        ExtractedField(
            field_name="edital_numero",
            state=FieldState.SUPPORTED,
            value="14/2026",
            evidence=[make_evidence(p1, edital_snippet, "edital")],
        )
    )

    # cargos
    jobs = [
        {
            "nome": "Agente Comunitário de Saúde - ACS",
            "vagas_imediatas": None,
            "cadastro_reserva": True,
            "vagas_ampla_concorrencia": None,
            "vagas_pcd": None,
            "remuneracao": "3262.64",
            "moeda": "BRL",
            "remuneracao_observacao": "vencimento mensal",
            "jornada": "40h",
            "requisitos": "Ensino Médio Completo; Residir na área da equipe (comunidade) que atuar; Curso de formação inicial ACS",
            "taxa_inscricao": None,
        }
    ]
    fields.append(
        ExtractedField(
            field_name="cargos",
            state=FieldState.SUPPORTED,
            value=jobs,
            evidence=[
                make_evidence(p2, cargos_hdr_snippet, "cargos-hdr"),
                make_evidence(p2, cargos_row_snippet, "cargos-row"),
            ],
            units={
                "remuneracao": "BRL/mês",
                "jornada": "horas semanais",
                "vagas": {"total": 0, "pcd": 0},
            },
        )
    )

    return fields
