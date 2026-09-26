"""Pinned, offline FATEC identity and fields parser for T012 milestone.

Pinned to source=fatec_selection external_id=2026/5020028-01.
"""
from __future__ import annotations

import hashlib
import uuid
from app.tenderproof.contracts import (
    Artifact,
    Evidence,
    EvidenceValidation,
    ExtractedField,
    FieldState,
    PageText,
)

SOURCE = "fatec_selection"
EXTERNAL_ID = "2026/5020028-01"
SHA256 = "abdf909cd6ac5bb46a92be82520d63c557cbb5feb7ae2f6728abc70926f0c1bd"
BYTE_LEN = 209318
DETAIL_URL = "https://www.fatecsm.org.br/processos-seletivos/"
DOCUMENT_URL = "https://www.fatecsm.org.br/doc.licitacoes/edital_030326103131-fatec.pdf"
TOTAL_PAGES = 7


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
        raise ValueError(f"FATEC parser pinned to {SOURCE}/{EXTERNAL_ID}")

    if len(pages) != TOTAL_PAGES:
        raise ValueError(f"FATEC page count drift: {len(pages)} != {TOTAL_PAGES}")

    p1 = pages[0]
    p2 = pages[1]
    p3 = pages[2]

    orgao_snippet = "FUNDAÇÃO DE APOIO À TECNOLOGIA E CIÊNCIA"
    edital_snippet = "EDITAL DE PROCESSO SELETIVO PÚBLICO N° 2026/5020028-01"
    prova_snippet = "A prova escrita será realizada no dia 09 de abril de 2026 às 9 horas"
    cargos_header_snippet = "Cód. Vagas Cargo Requisito de qualificação CH (h)"
    cargos_row_snippet = "01 01\nASSISTENTE DE\nLABORATÓRIO\nEnsino Médio completo 40 h"
    remun_snippet = "01 40 R$ 3.699,03 + 20% de insalubridade"
    inscr_snippet = "Os currículos serão recebidos no período 2 de abril de 20 26 a 8 de abril de 20 26."

    assert orgao_snippet in p1.text
    assert edital_snippet in p1.text
    assert prova_snippet in p3.text
    assert cargos_header_snippet in p1.text
    assert cargos_row_snippet in p1.text
    assert remun_snippet in p1.text
    assert inscr_snippet in p2.text

    def make_evidence(page: PageText, snippet: str, suffix: str) -> Evidence:
        return Evidence(
            evidence_id=f"ev-fatec-{suffix}",
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
            value="Fundação de Apoio à Tecnologia e Ciência - FATEC",
            evidence=[make_evidence(p1, orgao_snippet, "orgao")],
        )
    )

    # edital_numero
    fields.append(
        ExtractedField(
            field_name="edital_numero",
            state=FieldState.SUPPORTED,
            value="2026/5020028-01",
            evidence=[make_evidence(p1, edital_snippet, "edital")],
        )
    )

    # inscricao_inicio
    fields.append(
        ExtractedField(
            field_name="inscricao_inicio",
            state=FieldState.SUPPORTED,
            value="2026-04-02",
            evidence=[make_evidence(p2, inscr_snippet, "inscr-ini")],
        )
    )

    # inscricao_fim
    fields.append(
        ExtractedField(
            field_name="inscricao_fim",
            state=FieldState.SUPPORTED,
            value="2026-04-08",
            evidence=[make_evidence(p2, inscr_snippet, "inscr-fim")],
        )
    )

    # prova_data
    fields.append(
        ExtractedField(
            field_name="prova_data",
            state=FieldState.SUPPORTED,
            value="2026-04-09",
            evidence=[make_evidence(p3, prova_snippet, "prova")],
        )
    )

    # remuneracao
    fields.append(
        ExtractedField(
            field_name="remuneracao",
            state=FieldState.SUPPORTED,
            value={
                "valores_observados": ["3699.03"],
                "escopo": "Cód. 01 40h R$ 3.699,03 + 20% de insalubridade",
                "nota": "Valores por cargo conforme contexto; não inferir mínimo/máximo global.",
            },
            evidence=[make_evidence(p1, remun_snippet, "remun")],
        )
    )

    # cargos
    jobs = [
        {
            "nome": "Assistente de Laboratório",
            "vagas_imediatas": 1,
            "cadastro_reserva": None,
            "vagas_ampla_concorrencia": 1,
            "vagas_pcd": None,
            "remuneracao": "3699.03",
            "moeda": "BRL",
            "remuneracao_observacao": "+ 20% de insalubridade",
            "jornada": "40 h",
            "requisitos": "Ensino Médio completo",
            "taxa_inscricao": None,
        }
    ]
    fields.append(
        ExtractedField(
            field_name="cargos",
            state=FieldState.SUPPORTED,
            value=jobs,
            evidence=[
                make_evidence(p1, cargos_header_snippet, "cargos-hdr"),
                make_evidence(p1, cargos_row_snippet, "cargos-row"),
            ],
            units={
                "remuneracao": "BRL/mês",
                "jornada": "horas semanais",
                "vagas": {"total": 1, "pcd": 0},
            },
        )
    )

    return fields
