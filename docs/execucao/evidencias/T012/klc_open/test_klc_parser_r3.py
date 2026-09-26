import hashlib
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[5] / "backend"))
from app.tenderproof.processing import extract_pages_isolated
from app.tenderproof.publication import _reproduced_evidence
from app.tenderproof.contracts import Artifact, DiscoveredCandidate
from app.tenderproof.klc_t012 import document_identity_ids
from klc_parser_r3 import dispatch, parse

PDF = Path(__file__).parents[5] / "backend/.tenderproof/r99kill13/klc_open/artifacts/art-96637dad76-84c944ec1eb0eeadd52ddbc9b8b212ba9dce9072db1f0f51694f198e0f7111b4.pdf"


def test_klc_r3_pinned_parse_and_literal_evidence():
    content = PDF.read_bytes()
    assert hashlib.sha256(content).hexdigest() == "84c944ec1eb0eeadd52ddbc9b8b212ba9dce9072db1f0f51694f198e0f7111b4"
    pages, *_ = extract_pages_isolated(content, artifact_id="art-96637dad76", owner_id="1", capacity_wait_s=15, reuse_completed=True)
    fields = parse(source="klc_open", external_id="632", content=content, pages=pages,
                   total_pages=10, truncated=False, errors=[])
    assert fields[2].field_name == "edital_numero" and fields[2].value == "002/2026"
    assert fields[-1].value[0]["cadastro_reserva"] is True
    assert all("\ufffd" not in e.snippet for f in fields for e in f.evidence)
    assert all(e.artifact_id == "art-96637dad76" and e.document_sha256 == "84c944ec1eb0eeadd52ddbc9b8b212ba9dce9072db1f0f51694f198e0f7111b4" and e.source_url.endswith("4fe007a9a3f5afb03835272439f1812f.pdf") for f in fields for e in f.evidence)


def test_klc_identity_resolver_is_strict_and_not_generic_fallback():
    content = PDF.read_bytes()
    pages, *_ = extract_pages_isolated(content, artifact_id="art-96637dad76", owner_id="1", capacity_wait_s=15, reuse_completed=True)
    candidate = DiscoveredCandidate(candidate_id="klc_open-632", external_id="632", source="klc_open",
                                    title_observed="Processo Seletivo 002/2026 - Prefeitura Municipal de Teodoro Sampaio - SP",
                                    detail_url_observed="https://www.klcconcursos.com.br/concursos/632",
                                    observed_at=datetime(2026, 9, 13))
    assert document_identity_ids(candidate, pages) == {"632"}
    assert document_identity_ids(candidate.model_copy(update={"external_id": "631"}), pages) == set()
    bad_pages = [page.model_copy(update={"text": page.text.replace("Teodoro Sampaio", "Outro Município")}) for page in pages]
    assert document_identity_ids(candidate, bad_pages) == set()


def test_klc_r3_rejects_substitution():
    content = PDF.read_bytes()
    pages, *_ = extract_pages_isolated(content, artifact_id="art-96637dad76", owner_id="1", capacity_wait_s=15, reuse_completed=True)
    try:
        parse(source="klc_open", external_id="631", content=content, pages=pages)
    except ValueError as exc:
        assert "identity pin" in str(exc)
    else:
        raise AssertionError("identity substitution was not rejected")


def test_klc_r3_rejects_processing_drift():
    content = PDF.read_bytes()
    pages, *_ = extract_pages_isolated(content, artifact_id="art-96637dad76", owner_id="1", capacity_wait_s=15, reuse_completed=True)
    try:
        parse(source="klc_open", external_id="632", content=content, pages=pages[:-1], total_pages=10)
    except ValueError as exc:
        assert "missing or extra pages" in str(exc)
    else:
        raise AssertionError("page truncation was not rejected")


def test_klc_r3_integral_replacement_guard():
    content = PDF.read_bytes()
    pages, *_ = extract_pages_isolated(content, artifact_id="art-96637dad76", owner_id="1", capacity_wait_s=15, reuse_completed=True)
    pages[0] = pages[0].model_copy(update={"text": pages[0].text.replace("Município", "Mun\ufffdcipio")})
    try:
        parse(source="klc_open", external_id="632", content=content, pages=pages)
    except ValueError as exc:
        assert "U+FFFD" in str(exc)
    else:
        raise AssertionError("integral U+FFFD guard was not enforced")


def test_klc_r3_rejects_document_url_drift_by_default():
    content = PDF.read_bytes()
    pages, *_ = extract_pages_isolated(content, artifact_id="art-96637dad76", owner_id="1", capacity_wait_s=15, reuse_completed=True)
    try:
        parse(source="klc_open", external_id="632", content=content, pages=pages, document_url="https://www.klcconcursos.com.br/editais/other.pdf")
    except ValueError as exc:
        assert "URL drift" in str(exc)
    else:
        raise AssertionError("document URL drift was not rejected")


def test_klc_r3_rejects_size_plus_or_minus_one():
    content = PDF.read_bytes()
    pages, *_ = extract_pages_isolated(content, artifact_id="art-96637dad76", owner_id="1", capacity_wait_s=15, reuse_completed=True)
    for altered in (content[:-1], content + b"x"):
        try:
            parse(source="klc_open", external_id="632", content=altered, pages=pages)
        except ValueError as exc:
            assert "byte length" in str(exc)
        else:
            raise AssertionError("byte-length drift was not rejected")


def test_klc_r7_has_no_strict_text_bypass():
    import inspect
    assert "strict_text" not in inspect.signature(parse).parameters


def test_klc_r8_dispatch_rejects_artifact_metadata_and_url_drifts():
    content = PDF.read_bytes()
    pages, *_ = extract_pages_isolated(content, artifact_id="art-96637dad76", owner_id="1", capacity_wait_s=15, reuse_completed=True)
    from app.tenderproof.contracts import Artifact, DiscoveredCandidate
    from datetime import datetime
    candidate = DiscoveredCandidate(candidate_id="klc_open-632", external_id="632", title_observed="KLC", detail_url_observed="https://www.klcconcursos.com.br?pag=mco&id=632", source="klc_open", observed_at=datetime.now())
    def artifact(**kw):
        base = dict(artifact_id="art-96637dad76", sha256="84c944ec1eb0eeadd52ddbc9b8b212ba9dce9072db1f0f51694f198e0f7111b4", byte_len=348300, url_requested="https://www.klcconcursos.com.br/editais/4fe007a9a3f5afb03835272439f1812f.pdf", url_final="https://www.klcconcursos.com.br/editais/4fe007a9a3f5afb03835272439f1812f.pdf", downloaded_at=datetime.now())
        base.update(kw); return Artifact(**base)
    for bad in (dict(byte_len=348301), dict(sha256="0"*64), dict(url_requested="https://www.klcconcursos.com.br/editais/other.pdf"), dict(url_final="https://www.klcconcursos.com.br/editais/other.pdf")):
        try:
            dispatch(candidate, artifact(**bad), pages, content=content, total_pages=10, errors=[])
        except ValueError as exc:
            assert "pin" in str(exc)
        else:
            raise AssertionError("artifact drift bypassed dispatch")


def test_klc_r8_dispatch_rejects_page_truncated_flag():
    content = PDF.read_bytes()
    pages, *_ = extract_pages_isolated(content, artifact_id="art-96637dad76", owner_id="1", capacity_wait_s=15, reuse_completed=True)
    pages[0] = pages[0].model_copy(update={"truncated": True})
    from app.tenderproof.contracts import Artifact, DiscoveredCandidate
    from datetime import datetime
    a = Artifact(artifact_id="art-96637dad76", sha256="84c944ec1eb0eeadd52ddbc9b8b212ba9dce9072db1f0f51694f198e0f7111b4", byte_len=348300, url_requested="https://www.klcconcursos.com.br/editais/4fe007a9a3f5afb03835272439f1812f.pdf", url_final="https://www.klcconcursos.com.br/editais/4fe007a9a3f5afb03835272439f1812f.pdf", downloaded_at=datetime.now())
    c = DiscoveredCandidate(candidate_id="klc_open-632", external_id="632", title_observed="KLC", detail_url_observed="https://www.klcconcursos.com.br?pag=mco&id=632", source="klc_open", observed_at=datetime.now())
    try:
        dispatch(c, a, pages, content=content, total_pages=10, errors=[])
    except ValueError as exc:
        assert "truncated" in str(exc)
    else:
        raise AssertionError("PageText.truncated bypassed dispatch")


def test_klc_r3_dispatch_signature_and_page_error_guard():
    content = PDF.read_bytes()
    pages, *_ = extract_pages_isolated(content, artifact_id="art-96637dad76", owner_id="1", capacity_wait_s=15, reuse_completed=True)
    class ErrorPage:
        page_number = 1
        text = pages[0].text
        processing_error = "synthetic-error"
    bad = [ErrorPage(), *pages[1:]]
    try:
        parse(source="klc_open", external_id="632", content=content, pages=bad)
    except ValueError as exc:
        assert "page error" in str(exc)
    else:
        raise AssertionError("page error flag was not rejected")


def test_klc_r3_evidence_matches_revalidation_contract():
    content = PDF.read_bytes()
    pages, *_ = extract_pages_isolated(content, artifact_id="art-96637dad76", owner_id="1", capacity_wait_s=15, reuse_completed=True)
    fields = parse(source="klc_open", external_id="632", content=content, pages=pages)
    artifact = Artifact(artifact_id="art-96637dad76", sha256="84c944ec1eb0eeadd52ddbc9b8b212ba9dce9072db1f0f51694f198e0f7111b4", byte_len=len(content), url_requested="https://www.klcconcursos.com.br/editais/4fe007a9a3f5afb03835272439f1812f.pdf", url_final="https://www.klcconcursos.com.br/editais/4fe007a9a3f5afb03835272439f1812f.pdf", downloaded_at=datetime.fromisoformat("2026-09-08T14:54:34.654211+00:00"))
    cargo = next(f for f in fields if f.field_name == "cargos")
    assert all(_reproduced_evidence(e, cargo, {artifact.artifact_id: artifact}) for e in cargo.evidence)


def test_klc_r3_typed_dispatch_boundary():
    content = PDF.read_bytes()
    pages, total, processed, truncated, errors = extract_pages_isolated(content, artifact_id="art-96637dad76", owner_id="1", capacity_wait_s=15, reuse_completed=True)
    from app.tenderproof.contracts import Artifact, DiscoveredCandidate
    artifact = Artifact(artifact_id="art-96637dad76", sha256="84c944ec1eb0eeadd52ddbc9b8b212ba9dce9072db1f0f51694f198e0f7111b4", byte_len=len(content), url_requested="https://www.klcconcursos.com.br/editais/4fe007a9a3f5afb03835272439f1812f.pdf", url_final="https://www.klcconcursos.com.br/editais/4fe007a9a3f5afb03835272439f1812f.pdf", downloaded_at=datetime.fromisoformat("2026-09-08T14:54:34.654211+00:00"))
    candidate = DiscoveredCandidate(candidate_id="klc_open-632", external_id="632", title_observed="KLC", detail_url_observed="https://www.klcconcursos.com.br?pag=mco&id=632", source="klc_open", observed_at=datetime.now())
    fields = dispatch(candidate, artifact, pages, content=content, total_pages=total, truncated=truncated, errors=errors)
    assert all(field.state.value == "supported" for field in fields)
    assert all(type(field).__name__ == "ExtractedField" for field in fields)
