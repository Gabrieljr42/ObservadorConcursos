"""Positive/negative offline contract tests for the R9 proposal extractor."""
from pathlib import Path
import pytest

from publiconsult_proposal_r8 import (EDITAL_NUMERO, ORGAO, PRINCIPAL_SHA256,
    PRINCIPAL_URL, SOURCE, TITLE, _pages, extract_proposal_fields)
import publiconsult_proposal_r8 as parser

ROOT = Path(__file__).resolve().parents[5]
PDF = ROOT / "backend/.tenderproof/r30bytes/publiconsult_open/artifacts/art-30169711bf-7e3bc67ae2d209679dabaa791d7d63fb12369dd53e1da85cda9831721bd9917f.pdf"


def test_r8_returns_only_reproduced_identity_fields():
    result = extract_proposal_fields(content=PDF.read_bytes(), source=SOURCE,
        external_id="681", url_requested=PRINCIPAL_URL, url_final=PRINCIPAL_URL)
    assert [(f["field_name"], f["value"]) for f in result["fields"]] == [
        ("titulo", TITLE), ("orgao", ORGAO), ("edital_numero", EDITAL_NUMERO)]
    assert all(f["state"] == "supported" and f["evidence"] for f in result["fields"])
    assert result["artifact"]["sha256"] == PRINCIPAL_SHA256
    assert result["omitted_fields"] == ["cargos", "remuneracao", "taxa", "prova_data", "documentos"]


@pytest.mark.parametrize("kwargs", [
    {"source": "other_open"}, {"external_id": "682"},
    {"url_requested": PRINCIPAL_URL + "?raw=1"},
])
def test_r8_rejects_identity_or_url_drift(kwargs):
    content = PDF.read_bytes()
    base = {"content": content, "source": SOURCE, "external_id": "681",
            "url_requested": PRINCIPAL_URL, "url_final": PRINCIPAL_URL}
    base.update(kwargs)
    with pytest.raises(ValueError):
        extract_proposal_fields(**base)


def test_r8_rejects_byte_and_document_marker_drift():
    content = PDF.read_bytes()
    with pytest.raises(ValueError):
        extract_proposal_fields(content=content[:-1], source=SOURCE, external_id="681",
            url_requested=PRINCIPAL_URL, url_final=PRINCIPAL_URL)
    altered = b"X" + content[1:]
    with pytest.raises(ValueError):
        extract_proposal_fields(content=altered, source=SOURCE, external_id="681",
            url_requested=PRINCIPAL_URL, url_final=PRINCIPAL_URL)


def _records():
    return [{"page_index": i, "page_number": i + 1, "error": None,
             "truncated": False, "processing_error": False} for i in range(25)]


@pytest.mark.parametrize("mutate", [
    lambda r: r.pop(),
    lambda r: (r.__setitem__(0, {**r[0], "page_number": 2}), r.__setitem__(1, {**r[1], "page_number": 1})),
    lambda r: r[4].__setitem__("page_index", 99),
    lambda r: r[3].__setitem__("error", "text extraction failed"),
    lambda r: r[7].__setitem__("truncated", True),
    lambda r: r[9].__setitem__("processing_error", True),
])
def test_r9_rejects_each_page_structure_dimension(mutate):
    records = _records()
    mutate(records)
    with pytest.raises(ValueError):
        extract_proposal_fields(content=PDF.read_bytes(), source=SOURCE, external_id="681",
            url_requested=PRINCIPAL_URL, url_final=PRINCIPAL_URL, page_records=records)


class _FakePage:
    def __init__(self, text):
        self.text = text
    def extract_text(self):
        return self.text


@pytest.mark.parametrize("texts", [
    ["ok"] * 24,
    [""] + ["ok"] * 24,
    ["bad\ufffd"] + ["ok"] * 24,
])
def test_r9_rejects_count_nonempty_and_replacement_text(monkeypatch, texts):
    class Reader:
        def __init__(self, _stream):
            self.pages = [_FakePage(text) for text in texts]
    monkeypatch.setattr(parser, "PdfReader", Reader)
    with pytest.raises(ValueError):
        _pages(b"fixture")


def test_r9_rejects_processing_error(monkeypatch):
    def fail(_stream):
        raise RuntimeError("fixture parser error")
    monkeypatch.setattr(parser, "PdfReader", fail)
    with pytest.raises(ValueError):
        _pages(b"fixture")
