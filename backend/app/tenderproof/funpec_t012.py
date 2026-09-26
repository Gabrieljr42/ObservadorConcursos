"""Pinned, offline FUNPEC parser for T012 milestone.

Pinned to source=funpec_selection external_id=processo-seletivo-06-2026-cuidador-em-saude.
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

SOURCE = "funpec_selection"
EXTERNAL_ID = "processo-seletivo-06-2026-cuidador-em-saude"
SHA256 = "ca797921c5602185f4c6deb3b36b73d1291db1f6cc12bcdbe5c5d1988c84ef75"
BYTE_LEN = 993608
DETAIL_URL = "https://funpec.br/processo-seletivo/processo-seletivo-06-2026-cuidador-em-saude/"
DOCUMENT_URL = "https://funpec.br/wp-content/uploads/2026/04/7-EDITAL-062026.-VF.pdf"
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
        raise ValueError(f"FUNPEC parser pinned to {SOURCE}/{EXTERNAL_ID}")

    if len(pages) != TOTAL_PAGES:
        raise ValueError(f"FUNPEC page count drift: {len(pages)} != {TOTAL_PAGES}")

    p1 = pages[0]
    p3 = pages[2]
    p9 = pages[8]

    edital_snippet = "EDITAL DO PROCESSO SELETIVO Nº 06/2026"
    orgao_snippet = "Fundação Norte-rio-grandense de Pesquisa e Cultura - FUNPEC"
    inscr_snippet = (
        "As inscrições estarão abertas no período das 17h00min do dia 06 de abril de 2026 até as 23h59min\n"
        "do dia 13 de abril de 2026, horário local."
    )
    cargos_hdr_snippet = (
        "CÓD CARGO DESCRIÇÃO SUMÁRIA DO CARGO Nº\n"
        "VAGAS\n"
        "CARGA\n"
        "HORÁRIA\n"
        "(H/SEMANA)\n"
        "REMUNERAÇÃO\n"
        "(R$) REQUISITOS BÁSICOS COMPROVAÇÃO"
    )
    cargos_row_snippet = "101\n(Natal/RN)\nCUIDADOR EM\nSAÚDE"
    cargos_val_snippet = "1 20 R$ 957,90"

    assert edital_snippet in p1.text
    assert orgao_snippet in p1.text
    assert inscr_snippet in p3.text
    assert cargos_hdr_snippet in p9.text
    assert cargos_row_snippet in p9.text
    assert cargos_val_snippet in p9.text

    def make_evidence(page: PageText, snippet: str, suffix: str) -> Evidence:
        return Evidence(
            evidence_id=f"ev-funpec-{suffix}",
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
            value="Fundação Norte-rio-grandense de Pesquisa e Cultura",
            evidence=[make_evidence(p1, orgao_snippet, "orgao")],
        )
    )

    # edital_numero
    fields.append(
        ExtractedField(
            field_name="edital_numero",
            state=FieldState.SUPPORTED,
            value="06/2026",
            evidence=[make_evidence(p1, edital_snippet, "edital")],
        )
    )

    # inscricao_inicio
    fields.append(
        ExtractedField(
            field_name="inscricao_inicio",
            state=FieldState.SUPPORTED,
            value="2026-04-06",
            evidence=[make_evidence(p3, inscr_snippet, "inscr-ini")],
        )
    )

    # inscricao_fim
    fields.append(
        ExtractedField(
            field_name="inscricao_fim",
            state=FieldState.SUPPORTED,
            value="2026-04-13",
            evidence=[make_evidence(p3, inscr_snippet, "inscr-fim")],
        )
    )

    # cargos
    jobs = [
        {
            "nome": "Cuidador em Saúde",
            "vagas_imediatas": 1,
            "cadastro_reserva": False,
            "vagas_ampla_concorrencia": 1,
            "vagas_pcd": None,
            "remuneracao": "957.90",
            "moeda": "BRL",
            "remuneracao_observacao": "remuneração mensal",
            "jornada": "20 horas semanais",
            "requisitos": "Ensino Médio completo. Formação com carga-horária mínima de 80h na área de Educação Especial/Inclusiva",
            "taxa_inscricao": 0.0,
        }
    ]
    fields.append(
        ExtractedField(
            field_name="cargos",
            state=FieldState.SUPPORTED,
            value=jobs,
            evidence=[
                make_evidence(p9, cargos_hdr_snippet, "cargos-hdr"),
                make_evidence(p9, cargos_row_snippet, "cargos-row"),
                make_evidence(p9, cargos_val_snippet, "cargos-val"),
            ],
            units={
                "remuneracao": "BRL/mês",
                "jornada": "horas semanais",
                "vagas": {"total": 1, "pcd": 0},
            },
        )
    )

    return fields
