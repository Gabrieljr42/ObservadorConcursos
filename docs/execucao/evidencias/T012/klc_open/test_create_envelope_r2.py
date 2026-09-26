import hashlib
import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[5]
EVIDENCE = ROOT / "docs/execucao/evidencias/T012/klc_open"
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(EVIDENCE))

from app.tenderproof.pdf_text import extract_pages  # noqa: E402
from app.tenderproof.reviewed_run_import import ReviewedRun  # noqa: E402
from klc_parser_r3 import parse  # noqa: E402


def _payloads():
    envelope = json.loads((EVIDENCE / "create-envelope-r2.json").read_text(encoding="utf-8"))
    package = json.loads((EVIDENCE / "document-review-package-r2.json").read_text(encoding="utf-8"))
    return envelope, package


def test_create_envelope_is_owner_bound_null_target_and_exact_store_artifact():
    envelope, package = _payloads()
    assert envelope["operation"] == "CREATE"
    assert envelope["source"] == package["source"] == "klc_open"
    assert envelope["source_number"] == package["source_number"] == 57
    assert envelope["external_id"] == package["external_id"] == "632"
    assert envelope["owner_user_id"] == package["owner_user_id"] == 1
    assert envelope["concurso_id"] is None and envelope["run_id"] is None
    assert envelope["proposal_target"] is None and package["proposal_target"] is None
    assert "ephemeral_concurso_id" not in envelope
    artifact = envelope["artifact"]
    path = ROOT / artifact["store_path"]
    content = path.read_bytes()
    assert path.is_file()
    assert len(content) == artifact["byte_len"] == 348300
    assert hashlib.sha256(content).hexdigest() == artifact["sha256"]
    assert artifact["pages"] == 10


def test_only_parser_accepted_fields_and_cargo_are_carried():
    envelope, _ = _payloads()
    content = (ROOT / envelope["artifact"]["store_path"]).read_bytes()
    pages, *_ = extract_pages(content, artifact_id=envelope["artifact"]["artifact_id"])
    parsed = parse(
        source=envelope["source"], external_id=envelope["external_id"], content=content,
        pages=pages, document_url=envelope["artifact"]["url_final"], total_pages=10,
    )
    parsed_map = {field.field_name: field.value for field in parsed}
    envelope_map = {field["field_name"]: field["value"] for field in envelope["fields"]}
    assert set(envelope_map) == {"titulo", "orgao", "edital_numero", "inscricao_inicio", "inscricao_fim", "cargos"}
    assert parsed_map == envelope_map
    assert len(envelope_map["cargos"]) == 1


def test_import_schema_and_replay_are_explicitly_deferred_without_canonical_id():
    envelope, _ = _payloads()
    original = json.loads((EVIDENCE / "klc-632-reviewed-run.json").read_text(encoding="utf-8"))
    original["concurso_id"] = None
    with pytest.raises(ValidationError):
        ReviewedRun.model_validate(original)
    first = json.dumps(envelope, sort_keys=True, ensure_ascii=False)
    second = json.dumps(json.loads(first), sort_keys=True, ensure_ascii=False)
    assert first == second


@pytest.mark.parametrize(
    "source,external_id,url",
    [
        ("other_source", "632", "https://www.klcconcursos.com.br/editais/4fe007a9a3f5afb03835272439f1812f.pdf"),
        ("klc_open", "631", "https://www.klcconcursos.com.br/editais/4fe007a9a3f5afb03835272439f1812f.pdf"),
        ("klc_open", "632", "https://www.klcconcursos.com.br/editais/other.pdf"),
    ],
)
def test_parser_rejects_source_external_or_url_substitution(source, external_id, url):
    envelope, _ = _payloads()
    content = (ROOT / envelope["artifact"]["store_path"]).read_bytes()
    pages, *_ = extract_pages(content, artifact_id=envelope["artifact"]["artifact_id"])
    with pytest.raises(ValueError):
        parse(source=source, external_id=external_id, content=content, pages=pages, document_url=url, total_pages=10)


def test_parser_rejects_markers_and_pin_drift():
    envelope, _ = _payloads()
    content = (ROOT / envelope["artifact"]["store_path"]).read_bytes()
    pages, *_ = extract_pages(content, artifact_id=envelope["artifact"]["artifact_id"])
    with pytest.raises(ValueError):
        parse(source="klc_open", external_id="632", content=content + b"x", pages=pages, total_pages=10)
    bad = pages.copy()
    bad[0] = bad[0].model_copy(update={"text": bad[0].text + "\ufffd"})
    with pytest.raises(ValueError):
        parse(source="klc_open", external_id="632", content=content, pages=bad, total_pages=10)
