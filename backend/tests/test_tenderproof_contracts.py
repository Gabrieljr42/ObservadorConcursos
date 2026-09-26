"""TenderProof Fase 0 — contratos distinguem correto, incompleto e inválido (offline)."""

from datetime import datetime, timezone

from app.tenderproof.contracts import (
    SAMPLE_LIMIT,
    TARGET_FIELDS,
    Agreement,
    ExecutionStatus,
    ExtractedField,
    FieldState,
    ValidationStatus,
)
from app.tenderproof.compare import compare
from app.tenderproof.demo_pdf import make_text_pdf
from app.tenderproof.fields import extract_fields, semantic_hash
from app.tenderproof.mock_demo import (
    MOCK_BASELINE,
    MOCK_BASELINE_COLLECTED_AT,
    MOCK_BASELINE_ORIGIN,
    PDF_PAGE_1,
    build_mock_driver,
)
from app.tenderproof.pdf_text import extract_pages
from app.tenderproof.service import TenderProofService, read_only_baseline_from_concurso
from app.tenderproof.security import TenderProofSettings
from app.tenderproof.store import TenderProofStore
from app.tenderproof.validation import validate_identity
from app.tenderproof.contracts import Artifact, DiscoveredCandidate


def _candidate(**over):
    base = {
        "candidate_id": "cand-42",
        "title_observed": "Concurso Prefeitura Municipal de Exemplo MG cod 42",
        "detail_url_observed": "https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42",
        "external_id": "42",
        "observed_at": datetime(2026, 3, 2, tzinfo=timezone.utc),
    }
    base.update(over)
    return DiscoveredCandidate(**base)


def _artifact(**over):
    base = {
        "artifact_id": "art-test",
        "sha256": "0" * 64,
        "byte_len": 10,
        "url_requested": "https://novo.ibgpconcursos.com.br/fake.pdf",
        "url_final": "https://novo.ibgpconcursos.com.br/fake.pdf",
        "downloaded_at": datetime(2026, 3, 2, tzinfo=timezone.utc),
    }
    base.update(over)
    return Artifact(**base)


def _pages(texts, artifact_id="art-test"):
    from app.tenderproof.contracts import PageText

    return [
        PageText(artifact_id=artifact_id, page_number=i + 1, text=t, char_count=len(t))
        for i, t in enumerate(texts)
    ]


def test_target_fields_and_sample_limit_are_explicit():
    assert set(TARGET_FIELDS) == {
        "titulo", "orgao", "edital_numero",
        "inscricao_inicio", "inscricao_fim", "remuneracao",
    }
    assert SAMPLE_LIMIT == 5


def test_correct_contest_and_edital_are_supported_with_evidence():
    pages = _pages([PDF_PAGE_1])
    fields = extract_fields(candidate=_candidate(), artifact=_artifact(), pages=pages)
    by_name = {f.field_name: f for f in fields}
    for name in TARGET_FIELDS:
        assert by_name[name].state == FieldState.SUPPORTED, name
        assert by_name[name].evidence, name
        ev = by_name[name].evidence[0]
        assert ev.page_number == 1
        assert ev.snippet in PDF_PAGE_1  # trecho existe no material preservado
        assert ev.method and ev.method_version


def test_wrong_contest_document_is_flagged():
    pages = _pages(["Edital n. 05/2026 outro municipio concurso.jsp?cod=99 resultado final"])
    result = validate_identity(
        candidate=_candidate(), pages=pages,
        document_title="Edital 05/2026", document_url="https://novo.ibgpconcursos.com.br/x.pdf",
    )
    assert result.status == ValidationStatus.WRONG_CONTEST


def test_result_gabarito_confused_with_edital_is_non_edital():
    pages = _pages(["Gabarito oficial e resultado final das provas objetivas"])
    result = validate_identity(
        candidate=_candidate(), pages=pages,
        document_title="Gabarito oficial", document_url="https://novo.ibgpconcursos.com.br/g.pdf",
    )
    assert result.status == ValidationStatus.NON_EDITAL


def test_unreadable_document_without_text():
    pages = _pages(["", "   "])
    result = validate_identity(
        candidate=_candidate(), pages=pages,
        document_title="Edital", document_url="https://novo.ibgpconcursos.com.br/e.pdf",
    )
    assert result.status == ValidationStatus.UNREADABLE


def test_missing_field_is_unknown_with_reason():
    pages = _pages(["PREFEITURA MUNICIPAL DE EXEMPLO\nEdital n. 01/2026"])
    fields = extract_fields(candidate=_candidate(), artifact=_artifact(), pages=pages)
    by_name = {f.field_name: f for f in fields}
    assert by_name["inscricao_inicio"].state == FieldState.UNKNOWN
    assert by_name["inscricao_inicio"].reason
    assert by_name["remuneracao"].state == FieldState.UNKNOWN
    assert "contexto suficiente" in (by_name["remuneracao"].reason or "")


def test_conflicting_dates_are_conflict_not_supported():
    pages = _pages([
        "Edital n. 01/2026\ninscricoes de 10/03/2026 a 20/04/2026, retificado: "
        "inscricoes de 15/03/2026 a 25/05/2026"
    ])
    fields = extract_fields(candidate=_candidate(), artifact=_artifact(), pages=pages)
    by_name = {f.field_name: f for f in fields}
    # Janelas distintas com contexto de inscrição -> conflito explícito.
    assert by_name["inscricao_inicio"].state == FieldState.CONFLICT
    assert by_name["inscricao_fim"].state == FieldState.CONFLICT


def test_execution_validation_and_comparison_states_are_separate():
    store = TenderProofStore()
    svc = TenderProofService(store, TenderProofSettings())
    run = svc.start_discovery(build_mock_driver())
    assert run.execution_status == ExecutionStatus.AWAITING_SELECTION
    assert run.validation_status == ValidationStatus.PENDING
    assert run.comparison_status == "pending"
    run2 = svc.select_and_process(
        run.run_id, "cand-42", build_mock_driver(),
        baseline=MOCK_BASELINE, baseline_collected_at=MOCK_BASELINE_COLLECTED_AT,
        baseline_origin=MOCK_BASELINE_ORIGIN,
    )
    assert run2.execution_status == ExecutionStatus.COMPLETED
    assert run2.validation_status == ValidationStatus.VALID
    assert run2.comparison_status == "compared"
    # Baseline independente da validação: diverge sem invalidar o TenderProof.
    agreements = {c.field_name: c.agreement for c in run2.comparison.fields}
    assert agreements["inscricao_fim"] == Agreement.DIVERGE
    assert run2.validation_status == ValidationStatus.VALID


def test_semantic_hash_is_stable_and_ignores_session_time_urls():
    pages = _pages([PDF_PAGE_1])
    fields_a = extract_fields(candidate=_candidate(), artifact=_artifact(), pages=pages)
    fields_b = extract_fields(candidate=_candidate(), artifact=_artifact(), pages=pages)
    assert semantic_hash(fields_a) == semantic_hash(fields_b)
    # Reprocessar o mesmo material preserva o resultado semântico.
    pdf = make_text_pdf([PDF_PAGE_1])
    again, total, processed, truncated, errors = extract_pages(pdf, artifact_id="art-test")
    fields_c = extract_fields(candidate=_candidate(), artifact=_artifact(), pages=again)
    assert semantic_hash(fields_a) == semantic_hash(fields_c)


def test_read_only_baseline_never_calls_crawl_service(monkeypatch):
    import app.tenderproof.service as service_mod

    called = []

    class FakeCrawlService:
        def __init__(self, db):
            called.append("init")

        def crawl_source(self, source_id):
            called.append("crawl_source")
            return {}

    monkeypatch.setattr(service_mod, "CrawlService", FakeCrawlService, raising=False)

    class FakeConcurso:
        id = 7
        titulo = "T"
        orgao = "O"
        edital_numero = "01/2026"
        inscricao_inicio = datetime(2026, 3, 10, tzinfo=timezone.utc)
        inscricao_fim = datetime(2026, 4, 20, tzinfo=timezone.utc)
        salario_min = "3500.00"
        salario_max = "3500.00"
        updated_at = datetime(2026, 3, 5, tzinfo=timezone.utc)
        fetched_at = None

    baseline, collected, origin = read_only_baseline_from_concurso(FakeConcurso())
    assert called == []
    assert baseline["edital_numero"] == "01/2026"
    assert collected == FakeConcurso.updated_at
    assert "somente leitura" in origin or "leitura" in origin


def test_session_closure_distinguishes_request_confirmation_and_unknown():
    from app.tenderproof.contracts import SessionRecord
    record = SessionRecord(phase='detail')
    assert record.model_dump()['closure_status'] == 'unknown'
    record.close_requested = True
    assert record.model_dump()['closure_status'] == 'requested'
    record.closed = True
    assert record.model_dump()['closure_status'] == 'confirmed'
