import hashlib
from pathlib import Path
from io import BytesIO

import pytest
from test_tenderproof_publication import env  # noqa: F401

from app.tenderproof.barra_longa_parser import (
    EXPECTED_SHA256, EXPECTED_BYTES, DOCUMENT_URL, ARTIFACT_ID, build_reviewed_payload, derive, parse, preflight,
)
from app.tenderproof.contracts import Artifact, DiscoveredCandidate, PageText
from app.tenderproof.fields import extract_fields

PDF = Path(__file__).parents[2] / "docs/execucao/evidencias/T005/artifacts/T005-concurso32-art-07b137af65.pdf"


def test_t005_offline_extraction_is_complete_and_pinned():
    content = PDF.read_bytes()
    assert len(content) == EXPECTED_BYTES and hashlib.sha256(content).hexdigest() == EXPECTED_SHA256
    assert preflight(content)["pages"] == 23
    out = parse(content)
    assert len(out["cargos"]) == 7
    assert {c["vagas"] for c in out["cargos"]} == {1}
    assert {c["remuneracao"] for c in out["cargos"]} == {"3242.00"}
    assert {c["taxa"] for c in out["cargos"]} == {"162.10"}
    assert all({e["page_number"] for e in c["evidence"]} == {18, 23} for c in out["cargos"])
    assert all(any("18/10/2026" in e["snippet"] for e in c["evidence"]) for c in out["cargos"])
    assert out["retificacoes"] == out["publicacoes"] == []
    assert derive(out) == derive(parse(content))


def test_t005_fail_closed_on_drift_and_replacement_character():
    content = PDF.read_bytes()
    with pytest.raises(ValueError, match="drift"):
        preflight(content[:-1])
    # Any byte mutation is rejected before field promotion (the U+FFFD guard
    # is exercised by the parser's page-text extraction path).
    with pytest.raises(ValueError, match="drift"):
        parse(content + b"x")


def test_t005_reviewed_payload_is_owner_one_reference_only_and_pinned():
    payload = build_reviewed_payload(PDF.read_bytes(), owner_user_id=1)
    assert payload["owner_user_id"] == 1 and payload["reference_only"] is True
    assert payload["pending_fields"] == []
    assert payload["artifact"]["sha256"] == EXPECTED_SHA256
    assert {f["field_name"] for f in payload["fields"]} == {"cargos"}


def test_t005_extract_fields_routes_pinned_parser_without_generic_downgrade(monkeypatch, tmp_path):
    content = PDF.read_bytes()
    monkeypatch.setenv("TENDERPROOF_ARTIFACT_DIR", str(tmp_path))
    stored = tmp_path / "art-07b137af65-a5a7ff5a11bef285d389bd71a5e2d53b8ad5e82dec8d545edcea653c0fbef5a2.pdf"
    stored.write_bytes(content)
    artifact = Artifact(artifact_id=ARTIFACT_ID, sha256=EXPECTED_SHA256,
                        byte_len=EXPECTED_BYTES, url_requested=DOCUMENT_URL,
                        url_final=DOCUMENT_URL, content_type="application/pdf",
                        downloaded_at="2026-09-13T00:00:00Z", storage_path=stored.name)
    pages = [PageText(artifact_id=ARTIFACT_ID, page_number=i + 1, text=text)
             for i, page in enumerate(__import__("pypdf").PdfReader(BytesIO(content)).pages)
             for text in [(page.extract_text() or "")]]
    candidate = DiscoveredCandidate(candidate_id="elo-129", title_observed="PREFEITURA MUNICIPAL DE BARRA LONGA",
        detail_url_observed="https://novo.eloassessoriaeservicos.com.br/concurso/129",
        external_id="129", observed_at="2026-09-13T00:00:00Z", source="elo_open")
    fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    cargo = next(field for field in fields if field.field_name == "cargos")
    assert cargo.state.value == "supported" and len(cargo.value) == 7
    assert cargo.value[0]["vagas_imediatas"] == 1 and cargo.value[0]["remuneracao"] == "3242.00"
    assert all(e.artifact_id == ARTIFACT_ID for e in cargo.evidence)
    reviewed = next(f for f in build_reviewed_payload(content)["fields"] if f["field_name"] == "cargos")
    assert reviewed["value"] == cargo.value


def test_t005_disposable_store_and_catalogue_propose_only_cargos(env):
    """Faithful basename-store reproduction; no canonical write is applied."""
    from datetime import datetime, timezone
    from app.tenderproof.reviewed_run_import import import_reviewed_run
    from app.tenderproof import publication as pub
    db, _, user, contest, _, store = env
    content = PDF.read_bytes()
    payload = build_reviewed_payload(content, owner_user_id=user.id)
    payload["concurso_id"] = 32
    payload["artifact"].pop("content_base64", None)
    payload["artifact"]["content_path"] = str(PDF.resolve())
    import_reviewed_run(payload, store, dry_run=False)
    run_id = __import__("app.tenderproof.reviewed_run_import", fromlist=["_run_id"])._run_id(
        __import__("app.tenderproof.reviewed_run_import", fromlist=["ReviewedRun"]).ReviewedRun.model_validate(payload))
    run = store.get_run(run_id)
    source = db.get(__import__("app.models", fromlist=["Source"]).Source, contest.source_id)
    source.source_type = "elo_open"; source.name = "Elo Assessoria"
    contest.id = 32; contest.external_id = "129"
    contest.titulo = "PREFEITURA MUNICIPAL DE BARRA LONGA"
    contest.orgao = "Prefeitura Municipal De Barra Longa"; contest.edital_numero = "01/2026"
    contest.link_pagina = "https://novo.eloassessoriaeservicos.com.br/concurso/129"
    contest.inscricao_inicio = datetime(2026, 8, 18, 18)
    contest.inscricao_fim = datetime(2026, 9, 18, 18)
    contest.cargos = None
    eligible, blocked = pub._revalidate(run, contest, source, store)
    print('T005 proposal reproduction', eligible, blocked)
    assert list(eligible) == ["cargos"]
    assert "cargos" not in blocked
