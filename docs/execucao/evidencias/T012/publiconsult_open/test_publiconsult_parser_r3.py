from pathlib import Path
import importlib.util

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("publiconsult_parser_r3", HERE / "publiconsult_parser_r3.py")
parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser)

PDF = next(Path("backend/.tenderproof/r30bytes/publiconsult_open/artifacts").glob("*7e3bc67ae2d209679dabaa791d7d63fb12369dd53e1da85cda9831721bd9917f.pdf"))


def test_preserved_identity_and_strong_binding():
    parsed = parser.parse_pdf_bytes(PDF.read_bytes(), source="publiconsult_open", external_id="681")
    assert parsed["identity_ids"] == []
    assert parsed["orgao"] == "Prefeitura Municipal de Votuporanga/SP"
    assert parsed["edital_numero"] == "1/2026"
    assert len(parsed["pages"]) == 25


def test_real_contract_fields_and_validation():
    from app.tenderproof.contracts import Artifact, ValidationStatus
    content = PDF.read_bytes()
    artifact = Artifact(artifact_id="art-74ea1bc8f9", sha256=parser.ARTIFACT_SHA256, byte_len=parser.ARTIFACT_BYTE_LEN, url_requested=parser.OFFICIAL_DOCUMENT_URL, url_final=parser.OFFICIAL_DOCUMENT_URL, downloaded_at="2026-09-08T12:51:29.654529Z", content_type="application/pdf", storage_path=PDF.name)
    fields, validation, identity = parser.fields_for_run(content, artifact, source="publiconsult_open", external_id="681")
    assert validation.status is ValidationStatus.VALID
    assert [f.field_name for f in fields] == ["orgao", "edital_numero"]
    assert all(f.state.value == "supported" and len(f.evidence) == 1 for f in fields)
    assert identity["identity_ids"] == []


def test_official_url_host_path_and_length_drift_fail_closed():
    from app.tenderproof.contracts import Artifact
    content = PDF.read_bytes()
    for url, size in [(parser.OFFICIAL_DOCUMENT_URL.replace("gsistbucket", "evilbucket"), parser.ARTIFACT_BYTE_LEN), (parser.OFFICIAL_DOCUMENT_URL.replace("/681/", "/682/"), parser.ARTIFACT_BYTE_LEN), (parser.OFFICIAL_DOCUMENT_URL, parser.ARTIFACT_BYTE_LEN - 1)]:
        artifact = Artifact(artifact_id="art-74ea1bc8f9", sha256=parser.ARTIFACT_SHA256, byte_len=size, url_requested=url, url_final=url, downloaded_at="2026-09-08T12:51:29.654529Z", content_type="application/pdf", storage_path=PDF.name)
        try:
            parser.fields_for_run(content, artifact, source="publiconsult_open", external_id="681")
        except ValueError:
            pass
        else:
            raise AssertionError("URL/length drift accepted")


def test_wrong_source_external_and_sha_fail_closed():
    content = PDF.read_bytes()
    for kwargs in ({"source": "other", "external_id": "681"}, {"source": "publiconsult_open", "external_id": "682"}):
        try:
            parser.parse_pdf_bytes(content, **kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError("identity guard accepted non-pinned input")
    try:
        parser.parse_pdf_bytes(content + b"x", source="publiconsult_open", external_id="681")
    except ValueError:
        pass
    else:
        raise AssertionError("SHA guard accepted altered bytes")


def test_real_revalidate_dispatch_with_controlled_source_fields(tmp_path, monkeypatch):
    import json, os
    from types import SimpleNamespace
    from app.tenderproof.reviewed_run_import import ReviewedRun, build_run
    from app.tenderproof.store import TenderProofStore
    from app.tenderproof import publication

    content = PDF.read_bytes()
    envelope = json.loads((HERE / "reviewed-envelope-publiconsult-681.json").read_text(encoding="utf-8"))
    envelope["concurso_id"] = 999999
    run = build_run(ReviewedRun.model_validate(envelope), content)
    actual = run.candidates[0]
    decoy = actual.model_copy(update={"candidate_id": "decoy-999", "external_id": "999", "source": "other"})
    run.candidates = [decoy, actual]
    prepared, identity = parser.prepare_for_revalidate(run, content, contest_orgao="Prefeitura Municipal de Votuporanga/SP", contest_edital_numero="1/2026")
    assert identity["external_id"] == "681"
    os.environ["TENDERPROOF_ARTIFACT_DIR"] = str(tmp_path)
    store = TenderProofStore()
    store.save_artifact_file(prepared.artifact, content)
    source = SimpleNamespace(source_type="publiconsult_open")
    contest = SimpleNamespace(external_id="681", link_pagina=prepared.candidates[0].detail_url_observed, orgao="Prefeitura Municipal de Votuporanga/SP", edital_numero="1/2026")
    real_fields = prepared.fields
    monkeypatch.setattr(publication, "extract_fields", lambda **kwargs: real_fields)
    eligible, blocked = publication._revalidate(prepared, contest, source, store)
    assert set(eligible) == {"orgao", "edital_numero"}
    assert set(blocked) == {"titulo", "inscricao_inicio", "inscricao_fim", "prova_data", "taxa", "cargos"}
    assert store.get_run(prepared.run_id) is None
