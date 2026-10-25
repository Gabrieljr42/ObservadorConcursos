from pathlib import Path

from app.tenderproof.contracts import Artifact, DiscoveredCandidate
from app.tenderproof.fields import extract_fields
from app.tenderproof.processing import extract_pages_isolated


PDF = (Path(__file__).resolve().parents[2] / "docs/execucao/evidencias/T010/id7.pdf")
SHA = "00dc6e0d8e560b8b0a5aae557016d7e6a169b1ebc00aeb31d7ff95babf497b2a"
URL = "https://anexos-r2.selecao.net.br/uploads/567/concursos/2868/anexos/6b72e3c6-333b-49b5-b871-801295856d49.pdf"


def _inputs():
    content = PDF.read_bytes()
    pages, *_ = extract_pages_isolated(content, artifact_id="art-b415916df7", owner_id="1")
    artifact = Artifact(artifact_id="art-b415916df7", sha256=SHA, byte_len=len(content),
                        url_requested=URL, url_final=URL, content_type="application/pdf",
                        downloaded_at="2026-09-07T23:41:35.699706Z")
    candidate = DiscoveredCandidate(candidate_id="abcp_open-2868",
        title_observed="Concurso Público - 001/2026 - CÂMARA MUNICIPAL DE GARÇA- SP",
        detail_url_observed="https://abcp.selecao.net.br/informacoes/2868/",
        external_id="2868", observed_at="2026-09-07T23:41:29.423319Z", source="abcp_open")
    return artifact, candidate, pages


def test_garca_targeted_parser_supported_and_fail_closed_on_drift():
    artifact, candidate, pages = _inputs()
    fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    cargo = next(field for field in fields if field.field_name == "cargos")
    assert cargo.state.value == "supported"
    assert cargo.value[0]["nome"] == "Técnico Legislativo"
    assert cargo.value[0]["remuneracao"] == "3378.77"
    assert cargo.value[0]["jornada"] == "35 horas semanais"
    assert cargo.value[0]["vagas_imediatas"] == 1
    assert all("�" not in e.snippet for e in cargo.evidence)
    assert "�" not in (cargo.units or {}).get("remuneracao", "")
    artifact.sha256 = "0" * 64
    drift = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    assert not any(field.field_name == "cargos" and field.state.value == "supported" for field in drift)


def test_garca_targeted_parser_rejects_unrecoverable_replacement():
    artifact, candidate, pages = _inputs()
    pages[0].text = pages[0].text.replace("TÉCNICO", "TÉCNICO�")
    fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    assert not any(field.field_name == "cargos" and field.state.value == "supported" for field in fields)
