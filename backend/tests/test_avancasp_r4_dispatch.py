"""Offline dispatch gate for both preserved AvançaSP R2 PDF revisions."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.tenderproof.avancasp_t012 import ARTIFACT_PINS, DETAIL_URL, SOURCE, EXTERNAL_ID
from app.tenderproof import avancasp_t012 as parser
from app.tenderproof.contracts import Artifact, DiscoveredCandidate, PageText
from app.tenderproof.fields import extract_fields
from app.tenderproof.pdf_text import extract_pages


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs/execucao/evidencias/T012/avancasp_open"
PDFS = {
    "c60fcc60f0037c4f28907460cf8a60ec6832b115b28988e81d77ebbb66441637":
        EVIDENCE / "avancasp-open-272-bbc8f6fc-a0a1-49ef-aa1d-7d5d2403f7ce.pdf",
    "49b2137790ee4915ef3ef058e15d94bde937e8bd766840681a278b59d5eb5cfd":
        EVIDENCE / "avancasp-open-272-6d52089a-0ad3-4a18-bef5-306c27315785.pdf",
}


def _case(sha: str):
    path = PDFS[sha]
    raw = path.read_bytes()
    pin = ARTIFACT_PINS[sha]
    artifact = Artifact(
        artifact_id=f"avancasp-open-{sha[:8]}", sha256=sha, byte_len=len(raw),
        url_requested=pin["url"], url_final=pin["url"], content_type="application/pdf",
        downloaded_at=datetime.now(timezone.utc), storage_path=str(path),
    )
    pages, *_ = extract_pages(raw, artifact_id=artifact.artifact_id)
    candidate = DiscoveredCandidate(
        candidate_id="avancasp_open-272", source=SOURCE, external_id=EXTERNAL_ID,
        title_observed="CONCURSO PÚBLICO 01/2026 - PREFEITURA MUNICIPAL DE CABREÚVA",
        detail_url_observed=DETAIL_URL, observed_at=datetime.now(timezone.utc),
    )
    return raw, artifact, candidate, pages


@pytest.mark.parametrize("sha", list(PDFS))
def test_each_r2_pdf_dispatches_with_its_own_pin(sha):
    raw, artifact, candidate, pages = _case(sha)
    assert hashlib.sha256(raw).hexdigest() == sha
    fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    by_name = {field.field_name: field for field in fields}
    assert by_name["cargos"].state.value == "supported"
    assert len(by_name["cargos"].value) == 14


@pytest.mark.parametrize("mutation", ["source", "external", "sha", "bytes", "url", "pages", "error", "truncated", "replacement"])
def test_r2_dispatch_rejects_each_identity_or_structure_drift(mutation):
    sha = next(iter(PDFS))
    raw, artifact, candidate, pages = _case(sha)
    if mutation == "source":
        candidate.source = "other_open"
    elif mutation == "external":
        candidate.external_id = "273"
    elif mutation == "sha":
        artifact.sha256 = "0" * 64
    elif mutation == "bytes":
        artifact.byte_len += 1
    elif mutation == "url":
        artifact.url_final = artifact.url_final.replace("/272/", "/273/")
    elif mutation == "pages":
        pages = pages[:-1]
    elif mutation == "error":
        pages[0].error = "synthetic extraction error"
    elif mutation == "truncated":
        pages[0].truncated = True
    else:
        pages[0].text += "\ufffd"
    if mutation == "source":
        with pytest.raises(ValueError):
            parser.extract_fields(candidate=candidate, artifact=artifact, pages=pages)
        return
    fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    assert fields and all(field.state.value != "supported" for field in fields)
