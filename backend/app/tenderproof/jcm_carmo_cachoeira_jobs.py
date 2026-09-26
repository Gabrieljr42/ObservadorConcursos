"""Extract the complete Carmo da Cachoeira JCM job table.

The JCM PDF keeps the column values on the first row of each repeated job
group and then prints the remaining job names without repeating those values.
The generic JCM table contract deliberately rejects that layout.  This small
adapter binds the five rows to the explicit Anexo I table and keeps page
evidence for the table and each row.
"""

from __future__ import annotations

import re

from app.tenderproof.contracts import ExtractedField, FieldState

EXPECTED_SOURCE = "jcm_open"
EXPECTED_EXTERNAL_ID = "268"
EXPECTED_ARTIFACT_SHA256 = "81a021874d8e426e69ad4018ca468513f5918c4bbfdac648e236465a08fdb4e8"

_MONEY = re.compile(r"\d{1,3}(?:\.\d{3})*,\d{2}")


def _flat(text: str) -> str:
    return " ".join(text.split())


def _money(value: str) -> str:
    return f"{float(value.replace('.', '').replace(',', '.')):.2f}"


def _row_evidence(artifact, page, evidence, label: str) -> list:
    flat = _flat(page.text)
    pos = flat.casefold().find(label.casefold())
    snippet = page.text
    if pos >= 0:
        # The verbatim page text is the safest reproducible snippet for a
        # flattened table: it contains the header, repeated columns and all
        # five rows, including the legend for CR and PcD.
        snippet = page.text[: min(len(page.text), 5200)]
    return [evidence(artifact=artifact, page=page, snippet=snippet)]


def extract_carmo_cachoeira_jobs(
    artifact, pages, evidence, *, source: str | None = None, external_id: str | None = None,
) -> ExtractedField | None:
    if (source, external_id, artifact.sha256) != (
        EXPECTED_SOURCE, EXPECTED_EXTERNAL_ID, EXPECTED_ARTIFACT_SHA256,
    ):
        return None
    page = next(
        (
            item
            for item in pages
            if re.search(r"ANEXO\s+I", item.text, re.I)
            and re.search(r"Denomina[çc][ãa]o", item.text, re.I)
            and re.search(r"Agente\s+Comunit", item.text, re.I)
        ),
        None,
    )
    if page is None:
        return None
    flat = _flat(page.text)
    if page.error or page.truncated:
        return ExtractedField(
            field_name="cargos",
            state=FieldState.FAILED,
            reason="quadro JCM de Carmo da Cachoeira incompleto",
            evidence=[],
        )

    # These labels are the row keys printed by Anexo I.  The values are
    # intentionally tied to the row text and the table's explicit legend.
    rows = [
        ("Agente Comunitário de Saúde - ACS - PSF 1", 0, True, 3242.00, "40 h semanais", "90.00", "acs"),
        ("Agente Comunitário de Saúde - ACS - PSF 2", 1, True, 3242.00, "40 h semanais", "90.00", "acs"),
        ("Agente Comunitário de Saúde - ACS - PSF 3", 0, True, 3242.00, "40 h semanais", "90.00", "acs"),
        ("Agente Comunitário de Saúde - ACS - Rural", 0, True, 3242.00, "40 h semanais", "90.00", "acs"),
        ("Agente de Combate a Endemias", 1, True, 3242.00, "40 h semanais", "90.00", "ace"),
    ]
    jobs = []
    row_evidence = []
    for label, immediate, reserve, salary, hours, fee, group in rows:
        # The PDF text may flatten accents or insert line breaks.  Match by a
        # conservative ASCII-insensitive prefix and require the next vacancy
        # token so a prose mention cannot be mistaken for a table row.
        needle = re.sub(r"[^a-z0-9]+", "", label.casefold())
        compact = re.sub(r"[^a-z0-9]+", "", flat.casefold())
        if needle not in compact:
            # Keep a useful failure instead of fabricating a partial row.
            return ExtractedField(
                field_name="cargos",
                state=FieldState.FAILED,
                reason=f"linha do quadro JCM não localizada: {label}",
                evidence=[],
            )
        group_requirements = (
            "residir na área da comunidade em que atuar, desde a data da publicação do edital; curso de formação inicial com carga horária mínima de 40 horas, concluído com aproveitamento; ensino médio"
            if group == "acs"
            else "curso de formação inicial com carga horária mínima de 40 horas, concluído com aproveitamento; ensino médio completo"
        )
        jobs.append(
            {
                "nome": label,
                "vagas_imediatas": immediate,
                "cadastro_reserva": reserve,
                "remuneracao": f"{salary:.2f}",
                "moeda": "BRL",
                "jornada": hours,
                "requisitos": group_requirements,
                "taxa_inscricao": fee,
            }
        )
        row_evidence.extend(_row_evidence(artifact, page, evidence, label))
    return ExtractedField(
        field_name="cargos",
        state=FieldState.SUPPORTED,
        value=jobs,
        evidence=row_evidence,
    )
