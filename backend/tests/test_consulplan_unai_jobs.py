from datetime import datetime, timezone
from pathlib import Path

from app.tenderproof.consulplan_unai_jobs import extract_unai_jobs, extract_unai_prova
from app.tenderproof.contracts import Artifact
from app.tenderproof.fields import _evidence
from app.tenderproof.processing import extract_pages_isolated


ROOT = Path(__file__).parents[2]
PDF = ROOT / "docs/execucao/evidencias/T010/id5.pdf"
SHA = "9bdb0e77fde501c33363ce636744b8be8107c64a996c1bde6b4aa2faa96dac32"


def artifact(sha=SHA):
    return Artifact(
        artifact_id="art-c2eb665edc",
        sha256=sha,
        byte_len=565628,
        url_requested="https://cdnsite.institutoconsulplan.org.br/concursos/1333/dc1fe1e393a346f0803722772b630442.pdf",
        url_final="https://cdnsite.institutoconsulplan.org.br/concursos/1333/dc1fe1e393a346f0803722772b630442.pdf",
        downloaded_at=datetime(2026, 9, 8, 14, 23, 24, tzinfo=timezone.utc),
        storage_path="id5.pdf",
    )


def test_unai_parser_reproduces_three_cargo_rows_from_preserved_pdf():
    pages, total, processed, truncated, errors = extract_pages_isolated(
        PDF.read_bytes(), artifact_id="art-c2eb665edc", owner_id="t010-id5-test",
        max_pages=60, capacity_wait_s=5,
    )
    assert (total, processed, truncated, errors) == (31, 31, False, [])
    result = extract_unai_jobs(artifact(), pages, _evidence, source="institutoconsulplan_open", external_id="unai2026")
    assert result.state.value == "supported"
    assert len(result.value) == 3
    assert [j["nome"] for j in result.value] == [
        "Analista de Atividades da Secretaria - Analista de Sistemas",
        "Analista de Atividades da Secretaria - Consultor Jurídico",
        "Analista de Atividades da Secretaria - Contador",
    ]
    assert all(j["remuneracao"] == "9193.89" and j["jornada"] == "30 horas semanais" for j in result.value)
    assert all(j["taxa_inscricao"] == "80.00" for j in result.value)
    row_evidence = [e for e in result.evidence if e.page_number == 1]
    assert len(row_evidence) == 3
    assert all("Auxílio" in e.snippet and "alimentação" in e.snippet for e in row_evidence)
    fee_evidence = [e for e in result.evidence if e.page_number == 3]
    assert len(fee_evidence) == 3
    assert [e.json_path for e in fee_evidence] == ["cargos[0].taxa_inscricao", "cargos[1].taxa_inscricao", "cargos[2].taxa_inscricao"]
    assert all(e.method_version == "consulplan-unai-2026/5" for e in result.evidence)


def test_unai_parser_fails_closed_if_vagas_heading_drifts():
    pages, *_ = extract_pages_isolated(PDF.read_bytes(), artifact_id="a", owner_id="t010-id5-test", max_pages=60, capacity_wait_s=5)
    page = next(p for p in pages if p.page_number == 1)
    drift_page = page.model_copy(update={"text": page.text.replace("I - DAS VAGAS", "I - DOS CARGOS", 1)})
    result = extract_unai_jobs(artifact(), [drift_page, *[p for p in pages if p.page_number != 1]], _evidence, source="institutoconsulplan_open", external_id="unai2026")
    assert result.state.value == "failed"


def test_unai_parser_fails_closed_on_sha_or_page_drift():
    pages, *_ = extract_pages_isolated(PDF.read_bytes(), artifact_id="a", owner_id="t010-id5-test", max_pages=60, capacity_wait_s=5)
    page = next(p for p in pages if p.page_number == 1)
    bad_sha = extract_unai_jobs(artifact("0" * 64), [page], _evidence, source="institutoconsulplan_open", external_id="unai2026")
    assert bad_sha is None
    bad_text = page.model_copy(update={"text": page.text.replace("R$ 9.193,89", "R$ 9.193,90", 1)})
    drift = extract_unai_jobs(artifact(), [bad_text], _evidence, source="institutoconsulplan_open", external_id="unai2026")
    assert drift.state.value == "failed"
    extra = next(p for p in pages if p.page_number == 1).model_copy(update={"text": pages[0].text + "\nAnalista de Atividades da Secretaria - Extra"})
    extra_result = extract_unai_jobs(artifact(), [extra, next(p for p in pages if p.page_number == 2)], _evidence, source="institutoconsulplan_open", external_id="unai2026")
    assert extra_result.state.value == "failed"


def test_unai_prova_parser_is_pinned_to_page_31_and_date():
    pages, *_ = extract_pages_isolated(PDF.read_bytes(), artifact_id="art-c2eb665edc", owner_id="t010-id5-test", max_pages=60, capacity_wait_s=5)
    result = extract_unai_prova(artifact(), pages, _evidence, source="institutoconsulplan_open", external_id="unai2026")
    assert result.state.value == "supported"
    assert result.value == "2027-01-10"
    assert result.evidence[0].page_number == 31
    assert result.evidence[0].snippet == "Realização da Prova Objetiva e Discursiva 10/1/2027"
    drift_page = next(p for p in pages if p.page_number == 31).model_copy(update={"text": pages[-1].text.replace("10/1/2027", "11/1/2027")})
    drift = extract_unai_prova(artifact(), [drift_page], _evidence, source="institutoconsulplan_open", external_id="unai2026")
    assert drift.state.value == "failed"
