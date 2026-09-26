"""Offline fail-closed tests for the pinned EPL strong-binding parser."""
from pathlib import Path
from datetime import datetime
import sys

import pytest

ROOT = Path(__file__).parents[5]

import epl_parser_r3
from epl_parser_r3 import DOCUMENT_URL, DETAIL_URL, EPLParserError, _text, extract_identity, revalidate, validation_result
from app.models import Source
from app.tenderproof import publication as pub
from app.tenderproof.contracts import Artifact, DiscoveredCandidate, DocumentCandidate, ExtractedField, FieldState, PageText, TenderProofRun, ValidationResult, ValidationStatus

sys.path.insert(0, str(ROOT / "backend" / "tests"))
from test_tenderproof_publication import env  # noqa: E402,F401


ARTIFACT = ROOT / "backend" / ".tenderproof" / "r60rec" / "artifacts" / "art-8c5dbef058-b040f8c3ff74845185dfdfec2096b70da84a7ee10c54d228afe7b82ed205805f.pdf"
_PAGE_TEXTS = _text(ARTIFACT.read_bytes())


def _typed_pages(artifact_id="art-8c5dbef058"):
    return [PageText(artifact_id=artifact_id, page_number=i + 1, text=text)
            for i, text in enumerate(_PAGE_TEXTS)]


def _typed_artifact(**updates):
    values = dict(artifact_id="art-8c5dbef058", sha256="b040f8c3ff74845185dfdfec2096b70da84a7ee10c54d228afe7b82ed205805f",
                  byte_len=784614, url_requested=DOCUMENT_URL, url_final=DOCUMENT_URL,
                  downloaded_at="2026-09-08T14:13:22.563992Z")
    values.update(updates)
    return Artifact(**values)


def test_pinned_revalidate_returns_fresh_identity_fields():
    result = revalidate(ARTIFACT.read_bytes())
    assert [field.field_name for field in result] == ["orgao", "edital_numero"]
    assert result[0].value == "Fundação Hospitalar Santa Terezinha de Erechim (FHSTE)"
    assert result[1].value == "01/2023"
    pages = _text(ARTIFACT.read_bytes())
    assert all(item.page_number == 1 and item.snippet in pages[0] for field in result for item in field.evidence)
    assert all("\ufffd" not in page for page in pages)
    assert validation_result(ARTIFACT.read_bytes()).status.value == "valid"


@pytest.mark.parametrize("kwargs", [
    {"source": "other_open"},
    {"external_id": "999"},
    {"detail_url": DETAIL_URL + "?id=999"},
    {"document_url": DOCUMENT_URL.replace("00052", "00099")},
])
def test_pinned_binding_rejects_substitution(kwargs):
    with pytest.raises(EPLParserError):
        revalidate(ARTIFACT.read_bytes(), **kwargs)


def test_pinned_binding_rejects_mutated_bytes():
    content = bytearray(ARTIFACT.read_bytes())
    content[-1] ^= 1
    with pytest.raises(EPLParserError, match="bytes"):
        revalidate(bytes(content))


def test_text_extraction_rejects_replacement_and_bad_page_shape(monkeypatch):
    class Page:
        def __init__(self, value):
            self.value = value

        def extract_text(self):
            return self.value

    class Reader:
        def __init__(self, pages):
            self.pages = pages

    monkeypatch.setattr(epl_parser_r3, "PdfReader", lambda _: Reader([Page("x\ufffd")] * 43))
    with pytest.raises(EPLParserError, match=r"U\+FFFD"):
        _text(b"fixture")
    monkeypatch.setattr(epl_parser_r3, "PdfReader", lambda _: Reader([Page("x")] * 42))
    with pytest.raises(EPLParserError, match="page count"):
        _text(b"fixture")


@pytest.mark.parametrize("page_update", [
    {"page_number": 2},
    {"error": "processing_error"},
    {"truncated": True},
    {"text": ""},
    {"text": "\ufffd"},
])
def test_extract_identity_rejects_page_metadata_or_text_drift(page_update):
    pages = _typed_pages()
    pages[0] = pages[0].model_copy(update=page_update)
    result = extract_identity(_typed_artifact(), pages, source="epl_open", external_id="52")
    assert result[0].state is FieldState.FAILED


@pytest.mark.parametrize("updates", [
    {"url_requested": DOCUMENT_URL.replace("00052", "00099")},
    {"url_final": DOCUMENT_URL.replace("00052", "00099")},
])
def test_extract_identity_pins_both_artifact_urls(updates):
    result = extract_identity(_typed_artifact(**updates), _typed_pages(), source="epl_open", external_id="52")
    assert result[0].state is FieldState.FAILED


def test_shared_revalidate_consumes_source_dispatch_without_side_effects(env, monkeypatch):
    db, _, user, contest, _, store = env
    content = ARTIFACT.read_bytes()
    artifact = store.save_artifact_file(Artifact(
        artifact_id="epl-r3-preflight", sha256="b040f8c3ff74845185dfdfec2096b70da84a7ee10c54d228afe7b82ed205805f",
        byte_len=len(content), url_requested=DOCUMENT_URL, url_final=DOCUMENT_URL,
        downloaded_at="2026-09-08T14:13:22.563992Z"), content)
    candidate = DiscoveredCandidate(candidate_id="epl-52", external_id="52",
        title_observed="FUNDAÇÃO HOSPITALAR SANTA TEREZINHA DE ERECHIM",
        detail_url_observed=DETAIL_URL, observed_at=datetime(2026, 9, 8, 14, 13, 22), source="epl_open")
    run = TenderProofRun(run_id="epl-r3-preflight", owner_user_id=user.id, source="epl_open", mode="real",
        execution_status="completed", validation_status=ValidationStatus.VALID, candidates=[candidate],
        selected_candidate_id="epl-52", document=DocumentCandidate(doc_id="epl-r3-preflight", title="01 - Edital de Abertura",
            url_requested=DOCUMENT_URL, url_final=DOCUMENT_URL, kind="edital"), artifact=artifact,
        fields=[ExtractedField(field_name="titulo", state=FieldState.SUPPORTED,
            value="FUNDAÇÃO HOSPITALAR SANTA TEREZINHA DE ERECHIM")], validation=ValidationResult(status=ValidationStatus.VALID))
    source = db.get(Source, contest.source_id)
    source.source_type = "epl_open"
    contest.external_id = "52"
    contest.link_pagina = DETAIL_URL
    contest.link_edital = DOCUMENT_URL
    contest.orgao = "Fundação Hospitalar Santa Terezinha de Erechim (FHSTE)"
    contest.edital_numero = "01/2023"
    db.commit()
    called = []
    def dispatch(*, candidate, artifact, pages):
        if candidate.source == "epl_open":
            called.append(True)
            return extract_identity(artifact, pages, source=candidate.source, external_id=candidate.external_id)
        raise AssertionError("unexpected source in isolated dispatch")
    monkeypatch.setattr(pub, "extract_fields", dispatch)
    eligible, blocked = pub._revalidate(run, contest, source, store)
    assert called == [True]
    assert eligible == {}
    assert "titulo" in blocked
