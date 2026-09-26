"""Cargo transcription for IBAM Caruaru/PE edital 01/2026.

The preserved 24-page opening edital points to Anexo I for the cargo table;
the table is a separate PDF on the IBAM page.  This adapter is therefore
strict about the preserved source tuple *and* requires the normal processor
to reproduce the Anexo I rows in ``pages`` before returning a supported
field.  A reference to Anexo I in the opening edital is never treated as a
substitute for the table itself.

The six rows below are transcribed from Anexo I.  ``vagas_imediatas`` is the
table's TOTAL DE VAGAS; the quota columns are retained separately.  The
edital has no general cadastro-reserva column for these rows, and the PcD
numbers are immediate quota seats, so they must not become a general CR.
"""

from __future__ import annotations

import re

from app.tenderproof.contracts import ExtractedField, FieldState


EXPECTED_SOURCE = "ibam_open"
EXPECTED_EXTERNAL_ID = "364"
EXPECTED_ARTIFACT_SHA256 = (
    "4c2d85e7c9f1db1eb49b4f4f853117cd0ab73128da0a9d7aabcb339753f9e496"
)
ANEXO_I_URL = "https://www.ibam-concursos.org.br/documento/anx1pmc0126.pdf"
EXPECTED_ANNEX_ARTIFACT_SHA256 = "fe050e7f31d9bc5972e5ed0fdbfa01dbd402e51c3408d98f99d90b3745fb7244"

HOURS = "40 horas semanais"
FEE = "97.00"
EXAM_DATE = "2026-11-29"

_AUDITOR_REQUIREMENTS = (
    "Graduação de Nível Superior em qualquer área, em grau de bacharelado "
    "ou de licenciatura plena, por instituição de ensino superior, oficial "
    "ou reconhecida, com diploma registrado na forma da lei."
)
_ANALYST_REQUIREMENTS = {
    "002": (
        "Diploma de Bacharel ou Tecnólogo em Ciência da Computação, Engenharia "
        "da Computação, Sistemas de Informação, Análise e Desenvolvimento de "
        "Sistemas, Banco de Dados e correlatos na área de tecnologia da informação, "
        "emitido por instituição de ensino superior reconhecida pelo MEC."
    ),
    "003": (
        "Diploma de Bacharel em Engenharia Civil, emitido por instituição de ensino "
        "reconhecida pelo MEC, com registro no CREA-PE."
    ),
    "004": (
        "Diploma de Bacharel em Contabilidade, emitido por instituição de ensino "
        "reconhecida pelo MEC, com registro no CRC-PE."
    ),
    "005": (
        "Diploma de Bacharel em Direito, emitido por instituição de ensino "
        "reconhecida pelo MEC."
    ),
    "006": (
        "Diploma de conclusão de Curso Superior de Graduação em Nível de "
        "Bacharelado, Licenciatura ou Tecnologia, emitido por instituição de ensino "
        "oficialmente reconhecida pelo Ministério da Educação (MEC)."
    ),
}

# (code, name, total, AC, PcD, PPP, exam start, salary, salary note)
_ROWS = (
    (
        "001", "Auditor Fiscal Municipal", 10, 7, 1, 2, "09:10", "6000.00",
        "Vencimento-base de R$ 6.000,00 acrescido das gratificações reguladas nas Seções II e III do Capítulo III da LC nº 087/2021, alterada pela LC 154/2025, e no art. 15 da LC 154/2025.",
    ),
    (
        "002", "Analista Fiscal Municipal – Tecnologia da Informação", 2, 1, 1, 0, "09:10", "2500.00",
        "Vencimento-base de R$ 2.500,00 acrescido de Gratificação de Produtividade Fazendária (GPF), variável, de até R$ 3.750,00.",
    ),
    (
        "003", "Analista Fiscal Municipal – Engenharia Civil", 2, 1, 1, 0, "09:10", "2500.00",
        "Vencimento-base de R$ 2.500,00 acrescido de Gratificação de Produtividade Fazendária (GPF), variável, de até R$ 3.750,00.",
    ),
    (
        "004", "Analista Fiscal Municipal – Contabilidade", 2, 1, 1, 0, "09:10", "2500.00",
        "Vencimento-base de R$ 2.500,00 acrescido de Gratificação de Produtividade Fazendária (GPF), variável, de até R$ 3.750,00.",
    ),
    (
        "005", "Analista Fiscal Municipal – Direito", 2, 1, 1, 0, "09:10", "2500.00",
        "Vencimento-base de R$ 2.500,00 acrescido de Gratificação de Produtividade Fazendária (GPF), variável, de até R$ 3.750,00.",
    ),
    (
        "006", "Analista Fiscal Municipal – Área Geral de Ensino Superior", 2, 1, 1, 0, "16:10", "2500.00",
        "Vencimento-base de R$ 2.500,00 acrescido de Gratificação de Produtividade Fazendária (GPF), variável, de até R$ 3.750,00.",
    ),
)


def _flat(value: str) -> str:
    return " ".join(value.split())


def _compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def _row_snippet(page_text: str, code: str, next_code: str | None) -> str | None:
    match = re.search(rf"(?m)^\s*{re.escape(code)}\s+", page_text)
    if match is None:
        # Some normalised PDF layouts put the code after a line break or
        # directly before the cargo name.  Keep the fallback conservative.
        match = re.search(rf"\b{re.escape(code)}\s+(?=[A-Za-zÀ-ÿ])", page_text)
    if match is None:
        return None
    end = len(page_text)
    if next_code:
        next_match = re.search(rf"(?m)^\s*{re.escape(next_code)}\s+", page_text[match.end():])
        if next_match:
            end = match.end() + next_match.start()
    return page_text[match.start():end].strip()


def _find_row_page(pages, code: str):
    for page in pages:
        if page.error or page.truncated:
            continue
        if re.search(rf"\b{re.escape(code)}\s+(?=[A-Za-zÀ-ÿ])", page.text):
            return page
    return None


def _find_fee_page(pages):
    return next(
        (page for page in pages if not page.error and not page.truncated and "97,00" in page.text),
        None,
    )


def extract_caruaru_jobs(
    artifact,
    pages,
    evidence,
    *,
    source: str | None = None,
    external_id: str | None = None,
) -> ExtractedField | None:
    """Return the six Anexo I rows only when the pinned document has them.

    The caller should pass pages produced by ``extract_pages_isolated``.  The
    opening 24-page PDF alone intentionally yields FAILED because it only
    says that Anexo I exists; this makes a missing annex visible to the gate.
    """

    if (source, external_id, artifact.sha256) != (
        EXPECTED_SOURCE,
        EXPECTED_EXTERNAL_ID,
        EXPECTED_ANNEX_ARTIFACT_SHA256,
    ):
        return None
    if not pages or any(page.error or page.truncated for page in pages):
        return ExtractedField(
            field_name="cargos",
            state=FieldState.FAILED,
            value=None,
            reason="páginas IBAM Caruaru incompletas; Anexo I não pode ser conferido",
            evidence=[],
        )

    table_page = next(
        (
            page for page in pages
            if re.search(r"ANEXO\s+I", page.text, re.I)
            and re.search(r"CARGOS[,.]?\s+VAGAS", page.text, re.I)
            and re.search(r"TOTAL\s+DE\s+VAGAS", page.text, re.I)
        ),
        None,
    )
    fee_page = _find_fee_page(pages)
    if table_page is None:
        return ExtractedField(
            field_name="cargos",
            state=FieldState.FAILED,
            value=None,
            reason=(
                "Anexo I de Caruaru é documento separado e não está nas páginas "
                "do run preservado; não emitir cargos a partir da referência ao anexo"
            ),
            evidence=[],
        )
    jobs = []
    evidences = []
    for index, (code, name, total, ac, pcd, ppp, exam_start, salary, salary_note) in enumerate(_ROWS):
        page = _find_row_page(pages, code)
        next_code = _ROWS[index + 1][0] if index + 1 < len(_ROWS) else None
        snippet = _row_snippet(page.text, code, next_code) if page else None
        requirement_anchor = {
            "001": "Graduação",
            "002": "Tecnólogo",
            "003": "Engenharia Civil",
            "004": "Contabilidade",
            "005": "Direito",
            "006": "Graduação",
        }[code]
        row_text = _flat(snippet or "").casefold()
        row_compact = _compact(snippet or "")
        row_tokens = (name, "40h", "6.000,00" if code == "001" else "2.500,00", requirement_anchor)
        if page is None or not snippet or (
            _compact(name) not in row_compact
            or any(token.casefold() not in row_text for token in row_tokens[1:3])
            or _compact(requirement_anchor) not in row_compact
        ):
            return ExtractedField(
                field_name="cargos",
                state=FieldState.FAILED,
                value=None,
                reason=f"linha do Anexo I não corroborada para o cargo {code}",
                evidence=[],
            )
        requirement = _AUDITOR_REQUIREMENTS if code == "001" else _ANALYST_REQUIREMENTS[code]
        jobs.append({
            "codigo": code,
            "nome": name,
            "vagas_imediatas": total,
            "vagas_ampla_concorrencia": ac,
            "vagas_pcd": pcd,
            "vagas_ppp": ppp,
            "vagas_indigenas": 0,
            "vagas_quilombolas": 0,
            "vagas_trans": 0,
            "cadastro_reserva": None,
            "cadastro_reserva_observacao": (
                "O Anexo I quantifica vagas imediatas e quotas AC/PcD/PPP; cadastro "
                "de reserva não confirmado nesta conferência. A cota PcD é separada "
                "do CR geral."
            ),
            "remuneracao": salary,
            "moeda": "BRL",
            "remuneracao_observacao": salary_note,
            "jornada": HOURS,
            "requisitos": requirement,
            "taxa_inscricao": FEE,
            "prova_data": EXAM_DATE,
            "prova_inicio": exam_start,
            "prova_horario_observacao": "Horário de Brasília; duração de 4 horas.",
        })
        evidences.append(evidence(artifact=artifact, page=page, snippet=snippet))

    if fee_page is not None:
        fee_snippet_match = re.search(r"(?:taxa|valor)\s+[^.]{0,120}97,00[^.]*", fee_page.text, re.I | re.S)
        fee_snippet = fee_snippet_match.group(0) if fee_snippet_match else "R$ 97,00"
        evidences.append(evidence(artifact=artifact, page=fee_page, snippet=fee_snippet))
    return ExtractedField(
        field_name="cargos",
        state=FieldState.SUPPORTED,
        value=jobs,
        reason=(
            "Tabela literal do Anexo I; salário mantém apenas vencimento-base e "
            "gratificações permanecem em observação; quotas PcD/PPP não são CR geral."
        ),
        evidence=evidences,
    )
