from pathlib import Path

import pytest

from app.tenderproof.apta_aragarcas_parser import (
    RETIFICATION_BYTE_LEN, RETIFICATION_SHA256, RETIFICATION_TITLE, RETIFICATION_URL,
    validate_retification,
)
from app.tenderproof.contracts import Artifact, DiscoveredCandidate, PageText
from app.tenderproof.review_cases import review_fields


ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "docs/execucao/evidencias/T012/apta_open/artifacts/Edital_Retificacao_2_2026_07_28_17_32_37.pdf"


def _case():
    from app.tenderproof.processing import extract_pages_isolated
    content = PDF.read_bytes()
    artifact = Artifact(artifact_id="art-apta-ret2-708", sha256=RETIFICATION_SHA256,
                        byte_len=RETIFICATION_BYTE_LEN, url_requested=RETIFICATION_URL,
                        url_final=RETIFICATION_URL, content_type="application/pdf",
                        downloaded_at="2026-09-13T00:00:00Z")
    pages, total, processed, truncated, errors = extract_pages_isolated(
        content, artifact_id=artifact.artifact_id, owner_id="1", max_pages=60,
        max_bytes=1_000_000, reuse_completed=False)
    assert (len(pages), total, processed, truncated, errors) == (1, 1, 1, False, [])
    candidate = DiscoveredCandidate(candidate_id="apta-708", external_id="708",
                                    source="apta_open", title_observed="Câmara Municipal de Aragarças",
                                    detail_url_observed="https://www.aptaconcursos.com.br/concursos/publicacoes/Câmara+Municipal+de+Aragarças+/708",
                                    observed_at="2026-09-13T00:00:00Z")
    document = {"title": RETIFICATION_TITLE, "url": RETIFICATION_URL, "kind": "retificacao"}
    return artifact, pages, candidate, document


def test_apta_retification_is_one_page_no_field_change_and_not_principal():
    artifact, pages, candidate, document = _case()
    validate_retification(artifact, pages, source="apta_open", external_id="708", document=document)
    assert review_fields(candidate, artifact, pages, document=document) == []


@pytest.mark.parametrize("mutation", ["sha", "url", "title", "pages"])
def test_apta_retification_drift_fails_closed(mutation):
    artifact, pages, candidate, document = _case()
    if mutation == "sha":
        artifact = artifact.model_copy(update={"sha256": "0" * 64})
    elif mutation == "url":
        document = {**document, "url": document["url"] + "?drift=1"}
    elif mutation == "title":
        document = {**document, "title": "Edital estranho"}
    else:
        pages = []
    with pytest.raises(ValueError):
        review_fields(candidate, artifact, pages, document=document)
