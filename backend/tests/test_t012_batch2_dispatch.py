from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.tenderproof.contracts import Artifact, DiscoveredCandidate
from app.tenderproof.fields import extract_fields
from app.tenderproof.processing import extract_pages_isolated

ROOT = Path(__file__).resolve().parents[2]


CASES = [
    ("klc_open", "632", "84c944ec1eb0eeadd52ddbc9b8b212ba9dce9072db1f0f51694f198e0f7111b4", 348300,
     "https://www.klcconcursos.com.br/editais/4fe007a9a3f5afb03835272439f1812f.pdf",
     ROOT / "backend/.tenderproof/processing/2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881/3d5c7c6702d54fd6a7021344c7b080b1/input.pdf"),
    ("epl_open", "52", "b040f8c3ff74845185dfdfec2096b70da84a7ee10c54d228afe7b82ed205805f", 784614,
     "https://cdn-arquivo.concursos.srv.br/EPL_CONCURSOS/00052/PUBLICA%C3%87%C3%95ES/01%20-%20EDITAL%20DE%20ABERTURA%20-%20VERSAO%20FINAL_1701470854.pdf",
     ROOT / "backend/.tenderproof/r60rec/artifacts/art-8c5dbef058-b040f8c3ff74845185dfdfec2096b70da84a7ee10c54d228afe7b82ed205805f.pdf"),
    ("publiconsult_open", "681", "7e3bc67ae2d209679dabaa791d7d63fb12369dd53e1da85cda9831721bd9917f", 720592,
     "https://gsistbucket.s3.amazonaws.com/publiconsult/Anexos/681/PM%20VOTUPORANGA%20-%20PS%201-2026%20-%20Edital%20de%20Abertura%20de%20Inscri%C3%A7%C3%B5es.pdf",
     ROOT / "backend/.tenderproof/r30new/publiconsult_open/artifacts/art-75595d4caf-7e3bc67ae2d209679dabaa791d7d63fb12369dd53e1da85cda9831721bd9917f.pdf"),
    ("avancasp_open", "272", "b0ba7e154786ce20c7bbe5fd454933c552558c4dfcfc588b60a71eab6a4ca06a", 742298,
     "https://anexos-r2.selecao.net.br/uploads/301/concursos/272/anexos/aa3e927b-faeb-414e-ae6c-28800427a051.pdf",
     ROOT / "docs/execucao/evidencias/T012/avancasp_open/avancasp-open-edital-272.pdf"),
    ("apta_open", "708", "db9c6d26a285102ae051761500d893c81616b07b69a086ec5353307d5975d79c", 362093,
     "https://cdn-arquivo.concursos.srv.br/APTA/00708/PUBLICACOES/Edital_Completo_2026_07_31_09_13_43.pdf",
     ROOT / "backend/.tenderproof/r60kill/apta_open/artifacts/art-0eb77bcb19-db9c6d26a285102ae051761500d893c81616b07b69a086ec5353307d5975d79c.pdf"),
]
DETAIL_URLS = {
    "avancasp_open": "https://avancasp.selecao.net.br/informacoes/272/",
    "apta_open": "https://www.aptaconcursos.com.br/concursos/publicacoes/Câmara+Municipal+de+Aragarças+/708",
}


@pytest.mark.parametrize("source,external_id,sha256,byte_len,url,pdf", CASES)
def test_batch2_dispatch_extracts_from_pinned_pdf(source, external_id, sha256, byte_len, url, pdf, monkeypatch):
    content = pdf.read_bytes()
    artifact = Artifact(artifact_id=f"batch2-{source}", sha256=sha256, byte_len=byte_len,
                        url_requested=url, url_final=url,
                        downloaded_at=datetime(2026, 9, 13, tzinfo=timezone.utc),
                        storage_path=pdf.as_posix())
    if source == "avancasp_open":
        monkeypatch.setattr("app.tenderproof.store.artifact_dir", lambda: pdf.parent)
        artifact.storage_path = pdf.name
    candidate = DiscoveredCandidate(candidate_id=f"{source}-{external_id}", source=source,
                                    external_id=external_id, title_observed="pinned selection",
                                    detail_url_observed=DETAIL_URLS.get(source, "https://example.invalid/detail"),
                                    observed_at=datetime(2026, 9, 13, tzinfo=timezone.utc))
    pages, *_ = extract_pages_isolated(content, artifact_id=artifact.artifact_id,
                                       owner_id=f"batch2-{source}", max_pages=75,
                                       capacity_wait_s=15, reuse_completed=False)
    fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    supported = {field.field_name for field in fields if field.state.value == "supported"}
    assert "edital_numero" in supported
    assert any(field.evidence for field in fields if field.field_name == "edital_numero")


def test_batch2_source_branch_rejects_external_drift_without_generic_fallback():
    artifact = Artifact(artifact_id="drift", sha256="0" * 64, byte_len=1,
                        url_requested="https://invalid", url_final="https://invalid",
                        downloaded_at=datetime(2026, 9, 13, tzinfo=timezone.utc))
    candidate = DiscoveredCandidate(candidate_id="drift", source="epl_open", external_id="999",
                                    detail_url_observed="https://invalid",
                                    observed_at=datetime(2026, 9, 13, tzinfo=timezone.utc))
    from app.tenderproof.contracts import PageText
    fields = extract_fields(candidate=candidate, artifact=artifact,
                            pages=[PageText(artifact_id="drift", page_number=1, text="EDIÇÃO")])
    assert fields and all(field.state.value == "failed" for field in fields)


@pytest.mark.parametrize("case_index,mutation", [(0, "sha"), (0, "url"), (3, "url"), (4, "detail"), (4, "url")])
def test_batch2_dispatch_rejects_pinned_metadata_drift(case_index, mutation, monkeypatch):
    source, external_id, sha256, byte_len, url, pdf = CASES[case_index]
    content = pdf.read_bytes()
    artifact = Artifact(artifact_id=f"drift-{source}", sha256=sha256, byte_len=byte_len,
                        url_requested=url, url_final=url,
                        downloaded_at=datetime(2026, 9, 13, tzinfo=timezone.utc),
                        storage_path=pdf.as_posix())
    detail = DETAIL_URLS.get(source, "https://example.invalid/detail")
    candidate = DiscoveredCandidate(candidate_id=f"{source}-drift", source=source,
                                    external_id=external_id, detail_url_observed=detail,
                                    observed_at=datetime(2026, 9, 13, tzinfo=timezone.utc))
    if mutation == "sha":
        artifact.sha256 = "0" * 64
    elif mutation == "url":
        artifact.url_final = url + "?drift=1"
    else:
        candidate.detail_url_observed = detail + "?drift=1"
    pages, *_ = extract_pages_isolated(content, artifact_id=artifact.artifact_id,
                                       owner_id=f"drift-{source}", max_pages=75,
                                       capacity_wait_s=15, reuse_completed=False)
    if source == "avancasp_open":
        monkeypatch.setattr("app.tenderproof.store.artifact_dir", lambda: pdf.parent)
        artifact.storage_path = pdf.name
    fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    assert fields and all(field.state.value != "supported" for field in fields)
