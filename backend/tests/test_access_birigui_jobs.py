from pathlib import Path

from app.tenderproof.access_birigui_jobs import SHA256, extract_birigui_jobs
from app.tenderproof.contracts import Artifact, PageText


def _artifact(sha=SHA256):
    return Artifact(artifact_id="art-5c4c41a458", sha256=sha, byte_len=496688,
                    url_requested="https://example.test/183.pdf", url_final="https://example.test/183.pdf",
                    downloaded_at="2026-09-08T16:11:28.760592Z")


def _evidence(**kwargs):
    from app.tenderproof.fields import _evidence
    return _evidence(**kwargs)


def test_birigui_targeted_extractor_is_supported_and_exact():
    text = Path("../docs/execucao/evidencias/T010/id1.txt").read_text(encoding="utf-8")
    page = text.split("PAGE 2", 1)[1].split("PAGE 3", 1)[0]
    result = extract_birigui_jobs(_artifact(), [PageText(artifact_id="art-5c4c41a458", page_number=2, text=page)], _evidence, source="access_open", external_id="183")
    assert result.state.value == "supported"
    assert result.value[0]["vagas_imediatas"] == 10
    assert result.value[0]["vagas_ampla_concorrencia"] == 9
    assert result.value[0]["vagas_pcd"] == 1
    assert result.value[0]["remuneracao"] == "30.53"
    assert result.value[0]["moeda"] == "BRL"
    assert result.value[0]["remuneracao_observacao"] == "por hora-aula"
    assert len(result.evidence) == 5


def test_birigui_targeted_extractor_fails_closed_on_sha_or_structure():
    text = Path("../docs/execucao/evidencias/T010/id1.txt").read_text(encoding="utf-8")
    page = text.split("PAGE 2", 1)[1].split("PAGE 3", 1)[0]
    failed_sha = extract_birigui_jobs(_artifact("0" * 64), [PageText(artifact_id="x", page_number=2, text=page)], _evidence, source="access_open", external_id="183")
    assert failed_sha is None
    failed_text = extract_birigui_jobs(_artifact(), [PageText(artifact_id="x", page_number=2, text=page.replace("R$ 30,53", "R$ 30,54"))], _evidence, source="access_open", external_id="183")
    assert failed_text.state.value == "failed"

    broken = PageText(artifact_id="x", page_number=2, text=page, truncated=True)
    assert extract_birigui_jobs(_artifact(), [broken], _evidence, source="access_open", external_id="183").state.value == "failed"
