"""TenderProof Fase 2 — páginas físicas, evidência verificável, parcialidade."""

import pytest

from app.tenderproof.contracts import Artifact, DiscoveredCandidate, FieldState, PageText
from app.tenderproof.demo_pdf import make_text_pdf
from app.tenderproof.fields import _evidence, extract_fields, semantic_hash
from app.tenderproof.mock_demo import PDF_PAGE_1
from app.tenderproof.pdf_text import extract_pages
from datetime import datetime, timezone


def _candidate():
    return DiscoveredCandidate(
        candidate_id="cand-42",
        title_observed="Concurso Prefeitura Municipal de Exemplo MG cod 42",
        detail_url_observed="https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42",
        external_id="42",
        observed_at=datetime(2026, 3, 2, tzinfo=timezone.utc),
    )


def _artifact():
    return Artifact(
        artifact_id="art-ev",
        sha256="0" * 64,
        byte_len=10,
        url_requested="https://novo.ibgpconcursos.com.br/e.pdf",
        url_final="https://novo.ibgpconcursos.com.br/e.pdf",
        downloaded_at=datetime(2026, 3, 2, tzinfo=timezone.utc),
    )


def test_physical_pages_total_vs_processed_and_truncation():
    pdf = make_text_pdf(["pagina um Edital n. 01/2026", "pagina dois", "pagina tres"])
    pages, total, processed, truncated, errors = extract_pages(pdf, artifact_id="a", max_pages=2)
    assert total == 3 and processed == 2 and truncated is True
    assert [p.page_number for p in pages] == [1, 2]
    assert any("truncado" in e for e in errors)


def test_page_failure_is_recorded_without_losing_other_pages():
    pdf = make_text_pdf(["Edital n. 01/2026 texto valido"])
    pages, total, processed, truncated, errors = extract_pages(pdf, artifact_id="a")
    assert total == 1 and processed == 1
    assert pages[0].page_number == 1 and pages[0].char_count > 0


def test_evidence_snippet_must_exist_verbatim():
    page = PageText(artifact_id="a", page_number=2, text="conteudo real da pagina dois", char_count=10)
    with pytest.raises(AssertionError):
        _evidence(artifact=_artifact(), page=page, snippet="trecho de outra pagina")
    ev = _evidence(artifact=_artifact(), page=page, snippet="pagina dois")
    assert ev.page_number == 2 and ev.artifact_id == "art-ev"


def test_existing_snippet_without_meaning_is_unknown():
    # Data existe, mas sem contexto de inscrição -> semanticamente inadequada.
    pages = [PageText(artifact_id="a", page_number=1, text="Publicado em 10/03/2026. Edital n. 01/2026.", char_count=10)]
    fields = extract_fields(candidate=_candidate(), artifact=_artifact(), pages=pages)
    by_name = {f.field_name: f for f in fields}
    assert by_name["inscricao_inicio"].state == FieldState.UNKNOWN
    # Valor monetário existe, mas é taxa -> não vira remuneração.
    pages = [PageText(
        artifact_id="a", page_number=1,
        text="Edital n. 01/2026. Taxa de inscricao no valor de R$ 80,00.",
        char_count=10,
    )]
    fields = extract_fields(candidate=_candidate(), artifact=_artifact(), pages=pages)
    by_name = {f.field_name: f for f in fields}
    assert by_name["remuneracao"].state == FieldState.UNKNOWN
    assert "taxa" in (by_name["remuneracao"].reason or "")


def test_single_cargo_salary_is_not_global_min_max():
    fields = extract_fields(
        candidate=_candidate(),
        artifact=_artifact(),
        pages=[PageText(artifact_id="a", page_number=1, text=PDF_PAGE_1, char_count=len(PDF_PAGE_1))],
    )
    remuneracao = next(f for f in fields if f.field_name == "remuneracao")
    assert remuneracao.state == FieldState.SUPPORTED
    assert isinstance(remuneracao.value, dict)
    assert "escopo" in remuneracao.value and "nota" in remuneracao.value


def test_reprocessing_same_bytes_preserves_semantic_result():
    pdf = make_text_pdf([PDF_PAGE_1])
    first, _, _, _, _ = extract_pages(pdf, artifact_id="art-same")
    second, _, _, _, _ = extract_pages(pdf, artifact_id="art-same")
    fields_a = extract_fields(candidate=_candidate(), artifact=_artifact(), pages=first)
    fields_b = extract_fields(candidate=_candidate(), artifact=_artifact(), pages=second)
    assert semantic_hash(fields_a) == semantic_hash(fields_b)


def test_dates_and_money_are_normalized():
    fields = extract_fields(
        candidate=_candidate(),
        artifact=_artifact(),
        pages=[PageText(artifact_id="a", page_number=1, text=PDF_PAGE_1, char_count=len(PDF_PAGE_1))],
    )
    by_name = {f.field_name: f for f in fields}
    assert by_name["inscricao_inicio"].value == "2026-03-10"
    assert by_name["inscricao_fim"].value == "2026-04-20"
    assert by_name["remuneracao"].value["valores_observados"] == ["3500.00"]
