from pathlib import Path

from app.tenderproof.contracts import Artifact, Evidence, EvidenceValidation, PageText
from app.tenderproof.idib_reriutaba_jobs import extract_reriutaba_jobs
from app.tenderproof.processing import extract_pages_isolated
from app.tenderproof.processing import pinned_page_limit, is_pinned_id8


SHA = "fef17aa38c078810cbfedfa999782c3d02318bd9e5fa764502b5c4bb116ab28a"
PDF = Path("docs/execucao/evidencias/T010/id8.pdf")


def _artifact(sha=SHA):
    return Artifact(
        artifact_id="art-cdeead8742", sha256=sha, byte_len=1048994,
        url_requested="https://concurso.idib.org.br/ConcursoDownloadArquivo.aspx?ID=362",
        url_final="https://concurso.idib.org.br/ConcursoDownloadArquivo.aspx?ID=362",
        content_type="application/pdf", downloaded_at="2026-09-08T21:00:00Z",
    )


def _evidence(*, artifact, page, snippet):
    assert snippet in page.text
    return Evidence(evidence_id="ev-test", artifact_id=artifact.artifact_id,
                    document_sha256=artifact.sha256, source_url=artifact.url_final,
                    page_number=page.page_number, snippet=snippet,
                    method="test", method_version="test/1",
                    validation=EvidenceValidation(ok=True))


def _pages():
    pages, total, processed, truncated, errors = extract_pages_isolated(
        PDF.read_bytes(), artifact_id="art-cdeead8742", owner_id="test-id8",
        max_bytes=30 * 1024 * 1024, max_pages=100,
    )
    assert (total, processed, truncated, errors) == (75, 75, False, [])
    return pages


def test_reriutaba_extracts_full_pinned_cargo_from_both_table_pages():
    result = extract_reriutaba_jobs(_artifact(), _pages(), _evidence,
                                    source="idib_open", external_id="362")
    assert result.state.value == "supported"
    assert len(result.value) == 1
    cargo = result.value[0]
    assert (cargo["vagas_imediatas"], cargo["vagas_ampla_concorrencia"], cargo["vagas_pcd"], cargo["vagas_ppp"], cargo["cadastro_reserva"]) == (9, 6, 1, 2, 11)
    assert cargo["remuneracao"].startswith("salário-mínimo")
    assert all("\ufffd" not in (ev.snippet or "") for ev in result.evidence)


def test_reriutaba_fails_closed_on_sha_drift_and_replacement_character():
    assert extract_reriutaba_jobs(_artifact("0" * 64), _pages(), _evidence,
                                  source="idib_open", external_id="362") is None
    pages = _pages()
    for page in pages:
        if page.page_number == 72:
            page.text = page.text.replace("Guarda", "Gu\ufffdarda", 1)
    result = extract_reriutaba_jobs(_artifact(), pages, _evidence,
                                    source="idib_open", external_id="362")
    assert result.state.value == "failed"
    assert "U+FFFD" in result.reason


def test_id8_page_limit_exception_is_exact_and_fail_closed():
    assert pinned_page_limit("idib_open", "362", SHA, 1048994) == 75
    assert is_pinned_id8("idib_open", "362", SHA, 1048994, 75)
    assert pinned_page_limit("other", "362", SHA, 1048994) == 60
    assert pinned_page_limit("idib_open", "362", "0" * 64, 1048994) == 60
    assert pinned_page_limit("idib_open", "362", SHA, 1048993) == 60
    assert not is_pinned_id8("idib_open", "362", SHA, 1048994, 74)
    assert not is_pinned_id8("idib_open", "362", SHA, 1048994, 76)
