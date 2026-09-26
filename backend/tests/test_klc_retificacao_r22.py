from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.tenderproof.contracts import Artifact, DiscoveredCandidate, FieldState
from app.tenderproof.processing import extract_pages_isolated
from app.tenderproof.klc_retificacao_t012 import (
    ARTIFACT_BYTE_LEN, ARTIFACT_ID, ARTIFACT_SHA256, DOCUMENT_KIND,
    DOCUMENT_TITLE, DOCUMENT_URL, EXTERNAL_ID, SOURCE, extract_fields,
)
from app.tenderproof.review_cases import review_fields

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "docs/execucao/evidencias/T012/klc_open/retificacao-1-1887b316.pdf"


def _case():
    content = PDF.read_bytes()
    artifact = Artifact(artifact_id=ARTIFACT_ID, sha256=ARTIFACT_SHA256,
                        byte_len=ARTIFACT_BYTE_LEN, url_requested=DOCUMENT_URL,
                        url_final=DOCUMENT_URL, content_type="application/pdf",
                        downloaded_at=datetime.now(timezone.utc), storage_path=str(PDF))
    candidate = DiscoveredCandidate(candidate_id="klc_open-632", source=SOURCE,
                                    external_id=EXTERNAL_ID,
                                    title_observed="Processo Seletivo 002/2026 - Prefeitura Municipal de Teodoro Sampaio - SP",
                                    detail_url_observed="https://www.klcconcursos.com.br?pag=mco&id=632",
                                    observed_at=datetime.now(timezone.utc))
    pages, *_ = extract_pages_isolated(content, artifact_id=ARTIFACT_ID,
                                       owner_id="r22", max_pages=10,
                                       max_bytes=2_000_000, capacity_wait_s=15,
                                       reuse_completed=False)
    document = {"title": DOCUMENT_TITLE, "kind": DOCUMENT_KIND, "url": DOCUMENT_URL}
    return content, artifact, candidate, pages, document


def test_active_klc_retification_parser_promotes_only_date_and_review_diff():
    content, artifact, candidate, pages, document = _case()
    parsed = extract_fields(candidate=candidate, artifact=artifact, pages=pages,
                            content=content, document=document)
    assert [field.field_name for field in parsed] == ["prova_data"]
    assert parsed[0].value == "2026-05-17"
    assert parsed[0].evidence[0].snippet == "ser aplicada no dia 17 de maio de 2026"
    reviewed = review_fields(candidate, artifact, pages, document=document)
    assert [field["field_name"] for field in reviewed] == ["prova_data"]
    assert reviewed[0]["value"] == "2026-05-17"
    baseline = {"prova_data": "2026-05-10"}
    changed = [name for name, value in {"prova_data": reviewed[0]["value"]}.items()
               if baseline.get(name) != value]
    assert changed == ["prova_data"]
    from app.tenderproof.fields import extract_fields as deployed_extract
    dispatched = deployed_extract(candidate=candidate, artifact=artifact, pages=pages,
                                 document=document)
    assert [field.field_name for field in dispatched] == ["prova_data"]
    assert dispatched[0].value == "2026-05-17"


@pytest.mark.parametrize("document", [None,
    {"title": "Outro", "kind": DOCUMENT_KIND, "url": DOCUMENT_URL},
    {"title": DOCUMENT_TITLE, "kind": "edital", "url": DOCUMENT_URL}])
def test_real_fields_dispatch_rejects_missing_or_wrong_manifest(document):
    content, artifact, candidate, pages, _ = _case()
    from app.tenderproof.fields import extract_fields as deployed_extract
    fields = deployed_extract(candidate=candidate, artifact=artifact, pages=pages,
                              document=document)
    assert fields and all(field.state is not FieldState.SUPPORTED for field in fields)


@pytest.mark.parametrize("mutation", ["sha", "url", "bytes", "pages", "marker"])
def test_klc_retification_fails_closed_on_any_pin_or_text_drift(mutation):
    content, artifact, candidate, pages, document = _case()
    if mutation == "sha":
        artifact.sha256 = "0" * 64
    elif mutation == "url":
        artifact.url_final += "?drift=1"
    elif mutation == "bytes":
        artifact.byte_len += 1
    elif mutation == "pages":
        pages[0].page_number = 2
    else:
        pages[0].text += "\ufffd"
    with pytest.raises(ValueError):
        extract_fields(candidate=candidate, artifact=artifact, pages=pages,
                       content=content, document=document)
