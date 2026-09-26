import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "tests"))
sys.path.insert(0, str(Path(__file__).parent))

from app.tenderproof.contracts import Artifact  # noqa: E402
from test_t012_apta_open_selection import _case  # noqa: E402
import apta_aragarcas_parser_r7_proposed as r7  # noqa: E402


def test_r7_returns_only_three_supported_identity_fields():
    _, candidate, _, artifact, pages = _case()
    fields = r7.extract_identity_r7(artifact, pages, source=candidate.source,
                                    external_id=candidate.external_id,
                                    detail_url=candidate.detail_url_observed,
                                    document_url=artifact.url_final)
    assert [field.field_name for field in fields] == ["titulo", "orgao", "edital_numero"]
    assert all(field.state.value == "supported" for field in fields)
    assert all(field.evidence and field.evidence[0].document_sha256 == r7.EXPECTED_SHA256 for field in fields)


@pytest.mark.parametrize("mutation", ["sha", "bytes", "pages", "source", "external", "document_url"])
def test_r7_rejects_all_identity_and_artifact_drift(mutation):
    _, candidate, _, artifact, pages = _case()
    if mutation == "sha":
        artifact.sha256 = "0" * 64
    elif mutation == "bytes":
        artifact.byte_len += 1
    elif mutation == "pages":
        pages = pages[:-1]
    elif mutation == "source":
        candidate.source = "other_open"
    elif mutation == "external":
        candidate.external_id = "999"
    else:
        artifact.url_final = artifact.url_requested + "?drift=1"
    with pytest.raises(ValueError):
        r7.extract_identity_r7(artifact, pages, source=candidate.source,
                               external_id=candidate.external_id,
                               detail_url=candidate.detail_url_observed,
                               document_url=artifact.url_final)


def test_r7_rejects_page_order_and_replacement_character():
    _, candidate, _, artifact, pages = _case()
    pages[0].page_number = 2
    with pytest.raises(ValueError):
        r7.extract_identity_r7(artifact, pages, source=candidate.source, external_id=candidate.external_id,
                               detail_url=candidate.detail_url_observed, document_url=artifact.url_final)
