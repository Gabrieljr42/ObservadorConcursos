from datetime import datetime, timezone

import pytest

from app.tenderproof.cebraspe_ponta_pora_jobs import (
    EXPECTED_ARTIFACT_SHA256 as CEBRASPE_SHA,
    EXPECTED_EXTERNAL_ID as CEBRASPE_ID,
    EXPECTED_SOURCE as CEBRASPE_SOURCE,
    extract_ponta_pora_jobs,
)
from app.tenderproof.contracts import Artifact, DiscoveredCandidate, PageText
from app.tenderproof.fepese_caxambu_jobs import (
    EXPECTED_ARTIFACT_SHA256 as FEPese_SHA,
    EXPECTED_EXTERNAL_ID as FEPese_ID,
    EXPECTED_SOURCE as FEPese_SOURCE,
    extract_caxambu_jobs,
)
from app.tenderproof.fields import extract_fields
from app.tenderproof.jcm_carmo_cachoeira_jobs import (
    EXPECTED_ARTIFACT_SHA256 as JCM_SHA,
    EXPECTED_EXTERNAL_ID as JCM_ID,
    EXPECTED_SOURCE as JCM_SOURCE,
    extract_carmo_cachoeira_jobs,
)


def _artifact(sha: str) -> Artifact:
    return Artifact(
        artifact_id="test-artifact",
        sha256=sha,
        byte_len=1,
        url_requested="https://example.test/edital.pdf",
        url_final="https://example.test/edital.pdf",
        downloaded_at=datetime.now(timezone.utc),
    )


@pytest.mark.parametrize(
    ("extractor", "source", "external_id", "sha"),
    [
        (extract_carmo_cachoeira_jobs, JCM_SOURCE, JCM_ID, JCM_SHA),
        (extract_ponta_pora_jobs, CEBRASPE_SOURCE, CEBRASPE_ID, CEBRASPE_SHA),
        (extract_caxambu_jobs, FEPese_SOURCE, FEPese_ID, FEPese_SHA),
    ],
)
def test_delivery_extractors_reject_same_named_table_with_other_bytes(
    extractor, source, external_id, sha
):
    pages = [PageText(artifact_id="test-artifact", page_number=1, text="Cargo nominal", char_count=14)]
    assert extractor(
        _artifact("0" * 64), pages, lambda **kwargs: None,
        source=source, external_id=external_id,
    ) is None
    assert extractor(
        _artifact(sha), pages, lambda **kwargs: None,
        source="other_source", external_id=external_id,
    ) is None


def test_fields_dispatch_marks_known_identity_with_wrong_sha_unsupported():
    candidate = DiscoveredCandidate(
        candidate_id="jcm_open-268",
        external_id=JCM_ID,
        source=JCM_SOURCE,
        detail_url_observed="https://example.test/268",
        observed_at=datetime.now(timezone.utc),
    )
    pages = [PageText(artifact_id="test-artifact", page_number=1, text="EDITAL 01/2026", char_count=13)]
    cargos = next(
        field for field in extract_fields(
            candidate=candidate,
            artifact=_artifact("0" * 64),
            pages=pages,
        ) if field.field_name == "cargos"
    )
    assert cargos.state.value == "failed"
    assert "SHA" in cargos.reason
