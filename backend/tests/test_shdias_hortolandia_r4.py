from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from app.tenderproof.shdias_hortolandia import (
    EXPECTED_BYTES,
    EXPECTED_PAGES,
    EXPECTED_SHA256,
    EXTERNAL_ID,
    PROCESS_ID,
    SOURCE,
    derive,
    parse,
    preflight,
)


PDF = (Path(__file__).resolve().parents[2] / "docs/execucao/evidencias/T012/shdias_open/artifacts/01_Edital_Completo_2026_07_23_08_20_13.pdf")


@pytest.fixture()
def content() -> bytes:
    return PDF.read_bytes()


def test_pinned_identity_and_r3_fields_are_extracted_from_pdf(content):
    out = parse(content)
    assert hashlib.sha256(content).hexdigest().upper() == EXPECTED_SHA256
    assert len(content) == EXPECTED_BYTES
    assert out["identity"]["source"] == SOURCE
    assert out["identity"]["external_id"] == EXTERNAL_ID
    assert out["identity"]["process_id"] == PROCESS_ID
    assert out["identity"]["orgao"] == "Município de Hortolândia"
    assert out["identity"]["edital_numero"] == "001/2026"
    assert out["taxa_inscricao"] == "63.25"
    assert out["taxa"] == "63.25"
    assert out["evidence"]["taxa"]["snippet"] == "ENSINO MÉDIO COMPLETO VALOR DA INSCRIÇÃO: R$ 63,25"
    assert out["evidence"]["taxa"]["json_path"] == "taxa"
    assert out["prova_data"] == "2026-09-27"
    assert [c["vagas"] for c in out["cargos"]] == [12, 28]
    assert out["vagas_total"] == 40
    assert all("\ufffd" not in e["snippet"] for e in out["evidence"].values())


def test_preflight_reports_pinned_page_and_artifact_identity(content):
    result = preflight(content)
    assert result["sha256"] == EXPECTED_SHA256
    assert result["byte_len"] == EXPECTED_BYTES
    assert result["pages"] == EXPECTED_PAGES
    assert result["source"] == SOURCE
    assert result["external_id"] == EXTERNAL_ID
    assert result["process_id"] == PROCESS_ID
    assert result["network"] is False


@pytest.mark.parametrize(
    "kwargs",
    [
        {"source": "other_open"},
        {"external_id": "other"},
        {"process_id": "00309"},
    ],
)
def test_identity_drift_is_fail_closed(content, kwargs):
    with pytest.raises(ValueError, match="identity drift"):
        parse(content, **kwargs)


def test_sha_truncation_and_byte_drift_are_fail_closed(content):
    with pytest.raises(ValueError, match="artifact drift"):
        parse(content[:-1])
    altered = bytearray(content)
    altered[-1] ^= 1
    with pytest.raises(ValueError, match="artifact drift"):
        preflight(bytes(altered))


def test_marker_or_extraction_drift_is_fail_closed(monkeypatch, content):
    import app.tenderproof.shdias_hortolandia as parser
    from types import SimpleNamespace

    original = parser._pages
    monkeypatch.setattr(parser, "_pages", lambda value: ["plain text"] * EXPECTED_PAGES)
    with pytest.raises(ValueError, match="required literal"):
        parser.parse(content)
    monkeypatch.setattr(parser, "_pages", original)
    fake_pages = [SimpleNamespace(extract_text=lambda: "\ufffd")] * EXPECTED_PAGES
    monkeypatch.setattr(parser, "PdfReader", lambda value: SimpleNamespace(pages=fake_pages))
    with pytest.raises(ValueError, match=r"U\+FFFD"):
        parser.preflight(content)


def test_revalidate_is_semantically_stable(content):
    first = derive(content)
    second = derive(content)
    assert first == second
    assert first["identity"]["edital_numero"] == "001/2026"
