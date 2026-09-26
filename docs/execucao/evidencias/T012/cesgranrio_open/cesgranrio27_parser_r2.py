"""Byte-pinned identity parser for Cesgranrio event 27 (SEMA/MT).

This evidence-local module is intentionally not wired into shared ``fields.py``.
It is used only to prove the bounded revalidation path without weakening global
extraction rules.
"""
import re

from app.tenderproof.contracts import Evidence, EvidenceValidation, ExtractedField, FieldState


SOURCE = "cesgranrio_open"
EXTERNAL_ID = "27"
SHA256 = "e053d5c0f3f81b0fa93eb47912fe34398c7dd7d4a9be759ad43c96054d7ef39f"
BYTE_LEN = 1166736
ORG = "Secretaria de Estado de Meio Ambiente do Estado de Mato Grosso - SEMA/MT"
EDITAL = "01/2026"


def _ev(artifact, page, snippet, field_name):
    if snippet not in page.text:
        raise ValueError(f"evidence drift for {field_name}")
    return Evidence(
        evidence_id=f"ces27-r2-{field_name}",
        artifact_id=artifact.artifact_id,
        document_sha256=artifact.sha256,
        source_url=artifact.url_final,
        page_number=page.page_number,
        snippet=snippet,
        method="cesgranrio27-pinned-identity",
        method_version="T012-r2",
        validation=EvidenceValidation(ok=True),
    )


def extract_identity_fields(*, artifact, pages, source=SOURCE, external_id=EXTERNAL_ID):
    if source != SOURCE or external_id != EXTERNAL_ID:
        return None
    if artifact.sha256 != SHA256 or artifact.byte_len != BYTE_LEN:
        return None
    if not pages or not pages[0].text.strip():
        return None
    first = pages[0]
    if "SECRETARIA DE ESTADO DE MEIO AMBIENTE (SEMA/MT)" not in first.text:
        return None
    edital_match = re.search(r"EDITAL\s+N[º°]?\s*1\s*-\s*SEMA/MT", first.text, re.I)
    if not edital_match:
        return None
    org_snippet = "SECRETARIA DE ESTADO DE MEIO AMBIENTE (SEMA/MT)"
    edital_snippet = edital_match.group(0)
    return [
        ExtractedField(
            field_name="orgao", state=FieldState.SUPPORTED, value=ORG,
            evidence=[_ev(artifact, first, org_snippet, "orgao")],
        ),
        ExtractedField(
            field_name="edital_numero", state=FieldState.SUPPORTED, value=EDITAL,
            evidence=[_ev(artifact, first, edital_snippet, "edital_numero")],
        ),
    ]
