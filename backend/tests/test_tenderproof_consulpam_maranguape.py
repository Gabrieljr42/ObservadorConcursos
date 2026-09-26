from datetime import datetime, timezone

from app.tenderproof.consulpam_maranguape_jobs import (
    ACS_AREAS,
    EXPECTED_ARTIFACT_SHA256,
    EXPECTED_EXTERNAL_ID,
    EXPECTED_SOURCE,
    extract_maranguape_jobs,
)
from app.tenderproof.contracts import Artifact, DiscoveredCandidate, PageText
from app.tenderproof.fields import extract_fields


def _artifact(sha=EXPECTED_ARTIFACT_SHA256):
    return Artifact(
        artifact_id="consulpam-test",
        sha256=sha,
        byte_len=1,
        url_requested="https://example.test/edital.pdf",
        url_final="https://example.test/edital.pdf",
        downloaded_at=datetime.now(timezone.utc),
    )


def test_maranguape_transcription_is_pinned_to_exact_identity():
    page = PageText(artifact_id="consulpam-test", page_number=25, text="001", char_count=3)
    assert len(ACS_AREAS) == 42
    assert extract_maranguape_jobs(
        _artifact("0" * 64), [page], lambda **kwargs: None,
        source=EXPECTED_SOURCE, external_id=EXPECTED_EXTERNAL_ID,
    ) is None


def test_fields_rejects_known_consulpam_identity_with_other_bytes():
    candidate = DiscoveredCandidate(
        candidate_id="consulpam_open-777",
        external_id=EXPECTED_EXTERNAL_ID,
        source=EXPECTED_SOURCE,
        detail_url_observed="https://example.test/777",
        observed_at=datetime.now(timezone.utc),
    )
    field = next(
        item for item in extract_fields(
            candidate=candidate,
            artifact=_artifact("0" * 64),
            pages=[PageText(artifact_id="consulpam-test", page_number=1, text="EDITAL 01/2026", char_count=13)],
        ) if item.field_name == "cargos"
    )
    assert field.state.value == "failed"
    assert "SHA" in field.reason
