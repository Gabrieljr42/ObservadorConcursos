"""Strong, source-specific preflight for FAFIPA contest 4208.

The FAFIPA PDF does not print the portal numeric id ``4208`` in its body, so
the publication identity fallback is deliberately the exact organization plus
the main edital number.  Any drift in bytes, pages, organization or edital
number fails closed.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from app.tenderproof.processing import extract_pages_isolated
from app.tenderproof.contracts import Evidence, ExtractedField, FieldState, EvidenceValidation
from app.tenderproof.contracts import Artifact, DiscoveredCandidate, Evidence, ExtractedField, FieldState, PageText

SOURCE = "fafipa_open"
EXTERNAL_ID = "4208"
SHA256 = "26c059dcd502f08d6476d68b41ceed056d2b5be803d17cbdedce9734a241276f"
BYTE_LEN = 3630911
PAGE_COUNT = 38
ORGANO = "Município de Mirador - PR"
EDITAL_NUMERO = "001/2026"
DETAIL_URL = "https://concursos.fundacaofafipa.org.br/informacoes/4208/"
DOCUMENT_URL = "https://anexos-r2.selecao.net.br/uploads/281/concursos/4208/anexos/7c626742-c657-4e0c-b36c-7d59336ee942.pdf"


def strong_preflight(content: bytes) -> dict[str, Any]:
    digest = hashlib.sha256(content).hexdigest()
    if digest != SHA256 or len(content) != BYTE_LEN:
        raise ValueError("FAFIPA T012 R4 artifact drift")
    pages, _, _, _, errors = extract_pages_isolated(
        content, artifact_id="fafipa-4208-edital", owner_id="t012-r4",
        max_pages=75, max_bytes=20 * 1024 * 1024, capacity_wait_s=15,
        reuse_completed=False,
    )
    if errors or len(pages) != PAGE_COUNT:
        raise ValueError(f"FAFIPA T012 R4 extraction failed: pages={len(pages)} errors={errors}")
    text = "\n".join(page.text for page in pages)
    validate_extracted_text(text)
    normalized = text.casefold()
    if "mirador" not in normalized or not re.search(r"01\.001/2026", text):
        raise ValueError("FAFIPA T012 R4 organization/edital identity missing")
    # ObservedNetAdapter has no numeric identity resolver for this portal;
    # explicit portal-id set is therefore empty and fallback binding is used.
    return {
        "source": SOURCE, "external_id": EXTERNAL_ID, "sha256": digest,
        "byte_len": len(content), "pages": len(pages),
        "document_identity_ids": [], "identity_binding": "organization+main_edital",
        "orgao": ORGANO, "edital_numero": EDITAL_NUMERO,
        "extraction_errors": errors,
    }


def validate_extracted_text(text: str) -> None:
    """Reject lossy PDF decoding before identity or field recognition."""
    if "\ufffd" in text:
        raise ValueError("FAFIPA T012 R4 PDF text contains U+FFFD replacement marker")


def extract_fields(*, artifact: Artifact, pages: list[PageText], candidate: DiscoveredCandidate,
                   content: bytes) -> list[ExtractedField]:
    """Emit the reviewed FAFIPA values with exact fresh-PDF evidence."""
    if (candidate.source, candidate.external_id) != (SOURCE, EXTERNAL_ID):
        raise ValueError("FAFIPA source/external pin mismatch")
    if artifact.sha256 != SHA256 or artifact.byte_len != BYTE_LEN:
        raise ValueError("FAFIPA artifact pin mismatch")
    if artifact.url_requested != DOCUMENT_URL or artifact.url_final != DOCUMENT_URL:
        raise ValueError("FAFIPA document URL pin mismatch")
    if candidate.detail_url_observed != DETAIL_URL:
        raise ValueError("FAFIPA detail URL pin mismatch")
    strong_preflight(content)
    by_page = {p.page_number: p for p in pages}
    def ev(field: str, page_number: int, snippet: str) -> Evidence:
        page = by_page.get(page_number)
        if page is None or page.error or page.truncated or not snippet or snippet not in page.text or "\ufffd" in snippet:
            raise ValueError(f"FAFIPA evidence drift: {field}")
        return Evidence(evidence_id=f"fafipa-4208-{field}", artifact_id=artifact.artifact_id,
                        document_sha256=artifact.sha256, source_url=artifact.url_final,
                        page_number=page_number, snippet=snippet,
                         method="fafipa-source-parser", method_version="fafipa-4208-r13")
    def line_with(page_number: int, token: str) -> str:
        page = by_page.get(page_number)
        if page is None:
            raise ValueError(f"FAFIPA page missing: {page_number}")
        line = next((line.strip() for line in page.text.splitlines() if token.casefold() in line.casefold()), None)
        if not line:
            raise ValueError(f"FAFIPA literal missing: {token}")
        return line
    fields = [
        ("titulo", "Concurso Público do Município de Mirador - PR", 1, "001/2026"),
        ("orgao", ORGANO, 1, "Mirador"),
        ("edital_numero", EDITAL_NUMERO, 1, "01.001/2026"),
        ("inscricao_inicio", "2026-09-02", 36, "02/09/2026"),
        ("inscricao_fim", "2026-10-07", 36, "07/10/2026"),
        ("prova_data", "2026-11-01", 36, "01/11/2026"),
    ]
    result = [ExtractedField(field_name=name, state=FieldState.SUPPORTED, value=value,
                             original_value=value, evidence=[ev(name, page, line_with(page, token))])
              for name, value, page, token in fields]
    cargos = [{"nome": "Auxiliar Administrativo", "vagas": 4},
              {"nome": "Auxiliar de Clínica Dentária", "vagas": "cadastro_reserva"},
              {"nome": "Farmacêutico", "vagas": 1}, {"nome": "Fisioterapeuta", "vagas": 1},
              {"nome": "Médico Clínico Geral", "vagas": 1}, {"nome": "Motorista", "vagas": 7},
              {"nome": "Operador de Máquinas Rodoviárias", "vagas": 1},
              {"nome": "Professor (20h)", "vagas": 4}, {"nome": "Professor (40h)", "vagas": 5},
              {"nome": "Professor de Educação Física", "vagas": 2},
              {"nome": "Técnico em Eletrotécnica", "vagas": 1},
              {"nome": "Técnico em Enfermagem", "vagas": "cadastro_reserva"},
              {"nome": "Técnico em Higiene Dental", "vagas": "cadastro_reserva"},
              {"nome": "Vigia", "vagas": "cadastro_reserva"}]
    # Bind every reviewed row to the exact cargo-specific literal used by R9.
    # The normal revalidator compares snippet/page/url/SHA, so an aggregate
    # table-header evidence would make the whole cargos field ineligible.
    cargo_evidence_specs = [
        (2, "Auxiliar administrativo Ensino médio completo. 40h 03 - 01 R$ 1.883,84 MATUTINO"),
        (2, "Auxiliar de Clínica Dentária"),
        (2, "Farmacêutico"),
        (2, "Fisioterapeuta"),
        (3, "Médico Clínico Geral"),
        (2, "Motorista"),
        (2, "Operador de Máquinas\nRodoviárias"),
        (3, "Professor\nCurso de nível superior de Licenciatura\nPlena em Pedagogia ou Curso Normal\nSuperior (Magistério Superior), ou Curso\nsuperior de licenciatura plena\nacompanhado de magistério, formação\nmínima em nível médio na modalidade\nnormal.\n20h 03 - 01"),
        (3, "Professor\nCurso de nível superior de Licenciatura\nPlena em Pedagogia ou Curso Normal\nSuperior (Magistério Superior), ou Curso\nsuperior de licenciatura plena\nacompanhado de magistério, formação\nmínima em nível médio na modalidade\nnormal.\n40h 03 01 01"),
        (3, "Professor de Educação Física"),
        (2, "Técnico em Eletrotécnica"),
        (2, "Técnico em Enfermagem"),
        (2, "Técnico em Higiene Dental"),
        (2, "Vigia Ensino fundamental completo. 36h CR - - R$ 1.636,20 VESPERTINO"),
    ]
    if len(cargo_evidence_specs) != len(cargos):
        raise ValueError("FAFIPA cargo evidence cardinality drift")
    cargo_evidence = [ev(f"cargos[{index}]", page, snippet)
                      for index, (page, snippet) in enumerate(cargo_evidence_specs)]
    result.append(ExtractedField(field_name="cargos", state=FieldState.SUPPORTED, value=cargos,
                                 evidence=cargo_evidence))
    return result


def strong_binding_contract(candidate: Any, contest: Any, pages: list[Any]) -> dict[str, Any]:
    """Apply the same identity fallback contract used by publication.

    FAFIPA has no numeric ID resolver in its ObservedNetAdapter, therefore the
    exact organization and main edital number are required together.
    """
    from app.tenderproof.source_adapters import get_source_adapter
    from app.tenderproof.validation import document_identity_ids
    adapter = get_source_adapter(SOURCE)
    explicit_ids = document_identity_ids(adapter, candidate, pages)
    text = "\n".join(page.text for page in pages).casefold()
    orgao = str(getattr(contest, "orgao", ""))
    edital = str(getattr(contest, "edital_numero", ""))
    fallback = (not explicit_ids and orgao.casefold() == ORGANO.casefold()
                and edital == EDITAL_NUMERO and "mirador" in text
                and EDITAL_NUMERO in text)
    if not fallback:
        raise ValueError("FAFIPA T012 strong organization+edital binding failed")
    return {"document_identity_ids": sorted(explicit_ids), "binding": "organization+main_edital"}


def strong_preflight_file(path: str | Path) -> dict[str, Any]:
    return strong_preflight(Path(path).read_bytes())
