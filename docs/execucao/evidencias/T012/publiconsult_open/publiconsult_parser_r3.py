"""Evidence-scoped Publiconsult strong-binding parser (T012 R4)."""
from __future__ import annotations
import hashlib, io, re
from pathlib import Path
from app.tenderproof.contracts import Artifact, Evidence, EvidenceValidation, ExtractedField, FieldState, PageText, ValidationResult, ValidationStatus

SOURCE = "publiconsult_open"
EXTERNAL_ID = "681"
ARTIFACT_SHA256 = "7e3bc67ae2d209679dabaa791d7d63fb12369dd53e1da85cda9831721bd9917f"
ARTIFACT_BYTE_LEN = 720592
OFFICIAL_DOCUMENT_URL = "https://gsistbucket.s3.amazonaws.com/publiconsult/Anexos/681/PM%20VOTUPORANGA%20-%20PS%201-2026%20-%20Edital%20de%20Abertura%20de%20Inscri%C3%A7%C3%B5es.pdf"
EXPECTED_PAGES = 25

def _pages(content):
    from pypdf import PdfReader
    raw = PdfReader(io.BytesIO(content)).pages
    pages = []
    for i, page in enumerate(raw):
        text = page.extract_text() or ""
        pages.append(PageText(artifact_id="art-74ea1bc8f9", page_number=i + 1, text=text, char_count=len(text), extractor_version="publiconsult-parser-r4"))
    if len(pages) != EXPECTED_PAGES or any(not p.text.strip() for p in pages):
        raise ValueError("PDF incompleto/truncado")
    if any("\ufffd" in p.text for p in pages):
        raise ValueError("PDF ilegível: U+FFFD presente")
    return pages

def parse_pdf_bytes(content: bytes, *, source: str, external_id: str) -> dict:
    if source != SOURCE or str(external_id) != EXTERNAL_ID:
        raise ValueError("source/external_id fora do parser pinado")
    if len(content) != ARTIFACT_BYTE_LEN or hashlib.sha256(content).hexdigest() != ARTIFACT_SHA256:
        raise ValueError("tamanho/SHA divergente do PDF preservado")
    pages = _pages(content)
    text = "\n".join(p.text for p in pages)
    if not re.search(r"VOTUPORANGA", text, re.I) or not re.search(r"Processo Seletivo\s+N.{0,2}1/2026", text, re.I):
        raise ValueError("identidade textual ausente")
    return {"source": SOURCE, "external_id": EXTERNAL_ID, "orgao": "Prefeitura Municipal de Votuporanga/SP", "edital_numero": "1/2026", "identity_ids": [], "pages": pages}

def _ev(artifact, page, field, snippet):
    if snippet not in page.text:
        raise ValueError(f"evidência não reproduzível: {field}")
    return Evidence(evidence_id=f"ev-publiconsult-681-r4-{field}", artifact_id=artifact.artifact_id, document_sha256=artifact.sha256, source_url=artifact.url_final, page_number=page.page_number, snippet=snippet, method="publiconsult-source-parser", method_version="t012-publiconsult-r4", validation=EvidenceValidation(ok=True))

def fields_for_run(content: bytes, artifact: Artifact, *, source: str, external_id: str):
    if artifact.byte_len != ARTIFACT_BYTE_LEN or artifact.sha256 != ARTIFACT_SHA256 or artifact.url_requested != OFFICIAL_DOCUMENT_URL or artifact.url_final != OFFICIAL_DOCUMENT_URL:
        raise ValueError("Artifact não corresponde exatamente à URL/tamanho/SHA oficial pinados")
    parsed = parse_pdf_bytes(content, source=source, external_id=external_id)
    pages = parsed.pop("pages")
    first = pages[0]
    org_snip = next(line.strip() for line in first.text.splitlines() if "Prefeitura Municipal de VOTUPORANGA" in line)
    edital_snip = next(line.strip() for line in first.text.splitlines() if "Processo Seletivo" in line and "1/2026" in line)
    fields = [ExtractedField(field_name="orgao", state=FieldState.SUPPORTED, value=parsed["orgao"], evidence=[_ev(artifact, first, "orgao", org_snip)]), ExtractedField(field_name="edital_numero", state=FieldState.SUPPORTED, value=parsed["edital_numero"], evidence=[_ev(artifact, first, "edital_numero", edital_snip)])]
    validation = ValidationResult(status=ValidationStatus.VALID, checks=["source_pin", "external_pin", "sha256", "pages_complete", "no_u+fffd", "fresh_orgao", "fresh_edital_numero"])
    return fields, validation, {"source": parsed["source"], "external_id": parsed["external_id"], "identity_ids": parsed["identity_ids"]}

def prepare_for_revalidate(run, content: bytes, *, contest_orgao: str, contest_edital_numero: str):
    """Prepare real TenderProof fields/validation for the normal revalidate gate."""
    if run.source != SOURCE or not run.artifact:
        raise ValueError("run identity fora do pin Publiconsult")
    matches = [candidate for candidate in run.candidates if candidate.source == SOURCE and candidate.external_id == EXTERNAL_ID]
    if len(matches) != 1:
        raise ValueError("run deve conter exatamente um candidato Publiconsult/681")
    candidate = matches[0]
    if run.selected_candidate_id != candidate.candidate_id:
        raise ValueError("selected_candidate_id não aponta para Publiconsult/681")
    if hashlib.sha256(content).hexdigest() != ARTIFACT_SHA256 or len(content) != ARTIFACT_BYTE_LEN:
        raise ValueError("bytes do artefato divergem do tamanho/SHA pinados")
    if run.artifact.byte_len != ARTIFACT_BYTE_LEN or run.artifact.sha256 != ARTIFACT_SHA256 or run.artifact.url_requested != OFFICIAL_DOCUMENT_URL or run.artifact.url_final != OFFICIAL_DOCUMENT_URL:
        raise ValueError("artefato/URL não corresponde exatamente ao documento Publiconsult pinado")
    fields, validation, identity = fields_for_run(content, run.artifact, source=run.source, external_id=candidate.external_id)
    if fields[0].value != contest_orgao or fields[1].value != contest_edital_numero:
        raise ValueError("órgão/edital não vinculam ao alvo")
    return run.model_copy(update={"fields": fields, "validation": validation}), identity

if __name__ == "__main__":
    artifact = next(Path("backend/.tenderproof/r30bytes/publiconsult_open/artifacts").glob("*7e3bc67ae2d209679dabaa791d7d63fb12369dd53e1da85cda9831721bd9917f.pdf"))
    content = artifact.read_bytes()
    spec = Artifact(artifact_id="art-74ea1bc8f9", sha256=ARTIFACT_SHA256, byte_len=ARTIFACT_BYTE_LEN, url_requested=OFFICIAL_DOCUMENT_URL, url_final=OFFICIAL_DOCUMENT_URL, downloaded_at="2026-09-08T12:51:29.654529Z", content_type="application/pdf", storage_path=artifact.name)
    fields, validation, identity = fields_for_run(content, spec, source=SOURCE, external_id=EXTERNAL_ID)
    assert validation.status is ValidationStatus.VALID and identity["identity_ids"] == [] and len(fields) == 2
    print("PUBLICONSULT_R4_PARSER_PASS", identity)
