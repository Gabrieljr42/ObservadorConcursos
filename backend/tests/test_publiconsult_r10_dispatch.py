"""Shared dispatch/page_records gate for Publiconsult R9."""
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.tenderproof.contracts import Artifact, DiscoveredCandidate
from app.tenderproof.fields import extract_fields
from app.tenderproof.pdf_text import extract_pages
from app.tenderproof.publiconsult_t012 import ARTIFACT_BYTE_LEN, ARTIFACT_SHA256, OFFICIAL_DOCUMENT_URL, fields_for_run

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "backend/.tenderproof/r30bytes/publiconsult_open/artifacts/art-30169711bf-7e3bc67ae2d209679dabaa791d7d63fb12369dd53e1da85cda9831721bd9917f.pdf"


def _case():
    raw = PDF.read_bytes()
    artifact = Artifact(artifact_id="publiconsult-681-r10", sha256=ARTIFACT_SHA256,
                        byte_len=ARTIFACT_BYTE_LEN, url_requested=OFFICIAL_DOCUMENT_URL,
                        url_final=OFFICIAL_DOCUMENT_URL, content_type="application/pdf",
                        downloaded_at=datetime.now(timezone.utc), storage_path=str(PDF))
    pages, *_ = extract_pages(raw, artifact_id=artifact.artifact_id)
    candidate = DiscoveredCandidate(candidate_id="publiconsult_open-681", source="publiconsult_open",
                                    external_id="681", title_observed="Votuporanga",
                                    detail_url_observed="https://publiconsult.com.br/Concurso/Detail/681?origem=H",
                                    observed_at=datetime.now(timezone.utc))
    return artifact, candidate, pages


def test_r9_shared_dispatch_returns_only_principal_identity_fields():
    artifact, candidate, pages = _case()
    fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    assert [field.field_name for field in fields] == ["titulo", "orgao", "edital_numero"]
    assert all(field.state.value == "supported" for field in fields)
    assert all(field.evidence[0].document_sha256 == ARTIFACT_SHA256 for field in fields)


def test_exported_parser_round_trips_its_own_evidence_and_rejects_stale_line():
    from app.tenderproof.publication import _reproduced_evidence
    from app.tenderproof.contracts import Evidence
    artifact, candidate, pages = _case()
    parsed, validation, _ = fields_for_run(PDF.read_bytes(), artifact,
                                           source=candidate.source,
                                           external_id=candidate.external_id)
    assert validation.status.value == "valid"
    artifacts = {artifact.artifact_id: artifact}
    assert all(_reproduced_evidence(evidence, field, artifacts)
               for field in parsed for evidence in field.evidence)
    stale = parsed[0].evidence[0].model_copy(update={"snippet": "Processo Seletivo n� 1/2026"})
    assert not _reproduced_evidence(stale, parsed[0], artifacts)


@pytest.mark.parametrize("mutation", ["truncated", "error", "page_order", "url", "source", "external"])
def test_r9_shared_dispatch_fails_closed_on_page_or_identity_drift(mutation):
    artifact, candidate, pages = _case()
    if mutation == "truncated":
        pages[2].truncated = True
    elif mutation == "error":
        pages[2].error = "processing_error"
    elif mutation == "page_order":
        pages[0].page_number = 2
    elif mutation == "url":
        artifact.url_final += "?drift=1"
    elif mutation == "source":
        candidate.source = "other_open"
    else:
        candidate.external_id = "682"
    if mutation == "source":
        with pytest.raises(ValueError):
            fields_for_run(PDF.read_bytes(), artifact, source=candidate.source, external_id=candidate.external_id)
        return
    fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    assert fields and all(field.state.value != "supported" for field in fields)
