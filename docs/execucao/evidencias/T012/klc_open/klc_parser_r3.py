"""Source-specific offline KLC R3 parser; intentionally not shared-field code."""
from __future__ import annotations

from hashlib import sha256
from app.tenderproof.contracts import (Artifact, DiscoveredCandidate, Evidence,
                                       EvidenceValidation, ExtractedField, FieldState,
                                       PageText)

SOURCE = "klc_open"
EXTERNAL_ID = "632"
ARTIFACT_SHA256 = "84c944ec1eb0eeadd52ddbc9b8b212ba9dce9072db1f0f51694f198e0f7111b4"
ARTIFACT_BYTE_LEN = 348300


DOCUMENT_URL = "https://www.klcconcursos.com.br/editais/4fe007a9a3f5afb03835272439f1812f.pdf"


def parse(*, source: str, external_id: str, content: bytes, pages: list,
          artifact_id: str = "art-96637dad76", document_url: str = DOCUMENT_URL,
          total_pages: int | None = None, truncated: bool = False,
          errors: list | None = None) -> list[ExtractedField]:
    if source != SOURCE or str(external_id) != EXTERNAL_ID:
        raise ValueError("KLC R3 identity pin mismatch")
    digest = sha256(content).hexdigest()
    if len(content) != ARTIFACT_BYTE_LEN:
        raise ValueError("KLC R3 artifact byte length mismatch")
    if digest != ARTIFACT_SHA256:
        raise ValueError("KLC R3 artifact SHA mismatch")
    if document_url != DOCUMENT_URL:
        raise ValueError("KLC R3 document URL drift")
    if truncated or errors:
        raise ValueError("KLC R3 processing truncated or errored")
    if total_pages is not None and total_pages != 10:
        raise ValueError("KLC R3 unexpected total page count")
    if len(pages) != 10 or [getattr(p, "page_number", None) for p in pages] != list(range(1, 11)):
        raise ValueError("KLC R3 missing or extra pages")
    text = "\n".join(getattr(page, "text", "") for page in pages)
    if any(getattr(page, "truncated", False) for page in pages):
        raise ValueError("KLC R3 page truncated flag")
    page_errors = [getattr(page, "error", None) or getattr(page, "processing_error", None) for page in pages]
    if any(page_errors):
        raise ValueError("KLC R3 page error flag")
    if "\ufffd" in text:
        raise ValueError("KLC R3 U+FFFD in integral text")
    if "PROCESSO SELETIVO" not in text or "Teodoro Sampaio" not in text:
        raise ValueError("KLC R3 opening identity not reproduced")
    if "002/2026" not in text and "002-2026" not in text:
        raise ValueError("KLC R3 edital number not reproduced")
    def evidence(snippet: str, path: str) -> Evidence:
        page = next((p.page_number for p in pages if snippet in getattr(p, "text", "")), None)
        if page is None:
            raise ValueError(f"literal evidence missing: {snippet}")
        if "\ufffd" in snippet:
            raise ValueError("KLC R3 replacement character in evidence")
        return Evidence(evidence_id=f"klc632-{path.replace('[','-').replace(']','')}-{page}",
                        artifact_id=artifact_id, document_sha256=digest,
                        source_url=document_url, page_number=page, snippet=snippet,
                        json_path=path, method="klc-t012-r3-parser",
                        method_version="klc-open-632-r3",
                        validation=EvidenceValidation(ok=True))
    cargo = {
        "nome": "Monitor de Transporte e Atividade Escolares",
        "cadastro_reserva": True,
        "remuneracao": "1621.00",
        "jornada": "30 h/s",
        "requisitos": "Ensino Médio completo",
        "taxa_inscricao": "19.75",
        "beneficio": "ticket alimentação; valor atual R$ 715,00",
    }
    ev = [evidence("Monitor de Transporte", "cargos[0].nome"),
          evidence("1,621,00 +", "cargos[0].remuneracao"),
          evidence("30 h/s", "cargos[0].jornada"),
          evidence("Ensino Médio completo", "cargos[0].requisitos"),
          evidence("19,75", "cargos[0].taxa_inscricao"),
          evidence("ticket alimentação", "cargos[0].beneficio"),
          evidence("R$ 715,00", "cargos[0].beneficio")]
    return [
        ExtractedField(field_name="titulo", state=FieldState.SUPPORTED,
                       value="Processo Seletivo 002/2026 - Prefeitura Municipal de Teodoro Sampaio - SP",
                       evidence=[evidence("PROCESSO SELETIVO", "titulo")]),
        ExtractedField(field_name="orgao", state=FieldState.SUPPORTED,
                       value="Prefeitura Municipal de Teodoro Sampaio - SP",
                       evidence=[evidence("Teodoro Sampaio", "orgao")]),
        ExtractedField(field_name="edital_numero", state=FieldState.SUPPORTED,
                       value="002/2026", evidence=[evidence("002/2026", "edital_numero")]),
        ExtractedField(field_name="inscricao_inicio", state=FieldState.SUPPORTED,
                       value="2026-04-15", evidence=[evidence("15 de abril", "inscricao_inicio")]),
        ExtractedField(field_name="inscricao_fim", state=FieldState.SUPPORTED,
                       value="2026-04-26", evidence=[evidence("26 de abril de 2026", "inscricao_fim")]),
        ExtractedField(field_name="cargos", state=FieldState.SUPPORTED, value=[cargo],
                       evidence=ev),
    ]


def dispatch(candidate: DiscoveredCandidate, artifact: Artifact,
             pages: list[PageText], *, content: bytes,
             total_pages: int | None = None, truncated: bool = False,
             errors: list | None = None) -> list[ExtractedField]:
    """Typed adapter boundary consumed by an integration dispatcher."""
    if artifact.sha256 != ARTIFACT_SHA256 or artifact.byte_len != ARTIFACT_BYTE_LEN:
        raise ValueError("KLC R3 artifact metadata pin mismatch")
    if artifact.url_requested != DOCUMENT_URL or artifact.url_final != DOCUMENT_URL:
        raise ValueError("KLC R3 artifact URL pin mismatch")
    return parse(source=candidate.source, external_id=candidate.external_id,
                 content=content, pages=pages, artifact_id=artifact.artifact_id,
                 document_url=artifact.url_final, total_pages=total_pages,
                 truncated=truncated, errors=errors)
