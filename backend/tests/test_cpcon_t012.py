from pathlib import Path
from datetime import datetime, timezone
import pytest
from sqlalchemy import func, select

from app.tenderproof.contracts import Artifact, DiscoveredCandidate
from app.tenderproof.cpcon_t012 import document_identity_ids, extract_identity
from app.tenderproof.batch60_extended_adapters import CPCONAdapter
from app.tenderproof.validation import document_identity_ids as validation_identity_ids
from app.tenderproof.fields import extract_fields
from app.tenderproof import publication as pub
from app.models import Source
from app.tenderproof.publication_models import PublicationOutbox, PublicationProposal
from app.models import ConcursoVersion
from test_tenderproof_publication import env  # noqa: F401
from app.tenderproof.processing import extract_pages_isolated

ROOT = Path(__file__).parents[2]
PDF = ROOT / "docs/execucao/evidencias/T012/cpcon_open/processo-seletivo-002-2026.pdf"
SHA = "6a613684e806b59a350d25a614d6412b86e7daf47bc84c109f37da19fb40ef05"


def _artifact(sha=SHA):
    return Artifact(artifact_id="art-46d2f9fe5e", sha256=sha, byte_len=498894,
                    url_requested="https://cpcon.uepb.edu.br/download/edital-processo-seletivo-simplificado-no-002-2026-uepb/?wpdmdl=9836&refresh=6aa01b90f3b551788877712",
                    url_final="https://cpcon.uepb.edu.br/download/edital-processo-seletivo-simplificado-no-002-2026-uepb/?wpdmdl=9836&refresh=6aa01b90f3b551788877712",
                    downloaded_at=datetime(2026, 9, 8, 14, 28, 22, 681364, tzinfo=timezone.utc), storage_path="processo-seletivo-002-2026.pdf")


def _candidate(external= "processo-seletivo-simplificado-no-002-2026"):
    return DiscoveredCandidate(candidate_id="cpcon_open-processo-seletivo-simplificado-no-002-2026",
        title_observed="PROCESSO SELETIVO SIMPLIFICADO Nº 002/2026",
        detail_url_observed="https://cpcon.uepb.edu.br/processo-seletivo-simplificado-no-002-2026/",
        external_id=external, observed_at=datetime(2026, 9, 8, 14, 28, 20, 212777, tzinfo=timezone.utc), source="cpcon_open")


def test_cpcon_identity_parser_is_verbatim_and_strong():
    pages, total, processed, truncated, errors = extract_pages_isolated(PDF.read_bytes(), artifact_id="art-46d2f9fe5e", owner_id="t012", max_pages=40, capacity_wait_s=5)
    assert (total, processed, truncated, errors) == (13, 13, False, [])
    result = extract_identity(_artifact(), pages, _candidate())
    assert result.state.value == "supported"
    assert document_identity_ids(_candidate(), pages) == {_candidate().external_id}
    assert all("\ufffd" not in e.snippet and e.snippet in next(p.text for p in pages if p.page_number == e.page_number) for e in result.evidence)


def test_cpcon_identity_parser_fails_closed_on_identity_or_bytes_drift():
    pages, *_ = extract_pages_isolated(PDF.read_bytes(), artifact_id="art-46d2f9fe5e", owner_id="t012", max_pages=40, capacity_wait_s=5)
    assert extract_identity(_artifact("0" * 64), pages, _candidate()) is None
    assert extract_identity(_artifact(), pages, _candidate("processo-seletivo-simplificado-no-001-2026")) is None
    page = next(p for p in pages if p.page_number == 1).model_copy(update={"text": pages[0].text.replace("002/2026", "009/2026", 1)})
    assert extract_identity(_artifact(), [page, *[p for p in pages if p.page_number != 1]], _candidate()).state.value == "failed"


def test_cpcon_adapter_and_validation_use_candidate_pages_contract():
    """Exercise the real validation dispatcher, not only the parser helper."""
    class BoundCPCONAdapter(CPCONAdapter):
        def document_identity_ids(self, candidate, pages):
            return document_identity_ids(candidate, pages)

    pages, *_ = extract_pages_isolated(PDF.read_bytes(), artifact_id="art-46d2f9fe5e", owner_id="t012", max_pages=40, capacity_wait_s=5)
    adapter = BoundCPCONAdapter()
    assert validation_identity_ids(adapter, _candidate(), pages) == {_candidate().external_id}
    assert document_identity_ids(_candidate(), pages) == {_candidate().external_id}


def test_cpcon_resolver_rejects_replacement_and_truncation_without_typeerror():
    pages, *_ = extract_pages_isolated(PDF.read_bytes(), artifact_id="art-46d2f9fe5e", owner_id="t012", max_pages=40, capacity_wait_s=5)
    bad_encoding = pages[0].model_copy(update={"text": pages[0].text.replace("002/2026", "00\ufffd/2026", 1)})
    bad_truncation = pages[0].model_copy(update={"truncated": True})
    assert document_identity_ids(_candidate(), [bad_encoding, *pages[1:]]) == set()
    assert document_identity_ids(_candidate(), [bad_truncation, *pages[1:]]) == set()


def test_cpcon_real_revalidate_has_no_resolver_typeerror_and_accepts_pinned_identity(env):
    db, _, _, contest, run, store = env
    source = db.get(Source, contest.source_id)
    source.source_type = "cpcon_open"
    contest.external_id = _candidate().external_id
    contest.link_pagina = _candidate().detail_url_observed
    content = PDF.read_bytes()
    artifact = _artifact()
    store.save_artifact_file(artifact, content)
    pages, *_ = extract_pages_isolated(content, artifact_id=artifact.artifact_id, owner_id="t012", max_pages=40, capacity_wait_s=5)
    run.mode = "real"; run.is_synthetic_sample = False; run.source = "cpcon_open"
    run.candidates = [_candidate()]; run.selected_candidate_id = run.candidates[0].candidate_id
    from app.tenderproof.contracts import DocumentCandidate
    run.document = DocumentCandidate(doc_id="cpcon-doc-9836", title="PROCESSO SELETIVO SIMPLIFICADO Nº 002/2026",
                                     url_requested=artifact.url_requested, url_final=artifact.url_final, kind="edital")
    run.artifact = artifact; run.fields = extract_fields(candidate=run.candidates[0], artifact=artifact, pages=pages)
    eligible, blocked = pub._revalidate(run, contest, source, store)
    assert eligible["orgao"] == "Universidade Estadual da Paraíba"
    assert eligible["edital_numero"] == "002/2026"
    assert eligible["titulo"] == "PROCESSO SELETIVO SIMPLIFICADO Nº 002/2026"
    assert len(eligible["cargos"]) == 6
    assert eligible["cargos"][0]["nome"] == "Técnico em Laboratório (Esterilização)"
    cargo_field = next(field for field in run.fields if field.field_name == "cargos")
    assert all("Campus" in evidence.snippet and ("01" in evidence.snippet or "02" in evidence.snippet)
               for evidence in cargo_field.evidence)
    assert all("Campus" in evidence.snippet for evidence in cargo_field.evidence)
    assert "TypeError" not in str(blocked)
    assert db.scalar(select(func.count()).select_from(PublicationProposal)) == 0
    assert db.scalar(select(func.count()).select_from(ConcursoVersion)) == 0
    assert db.scalar(select(func.count()).select_from(PublicationOutbox)) == 0


def test_cpcon_stale_r2_evidence_is_rejected_by_fresh_bytes():
    """Bounded reproduction of live run drift; never mutates/imports a run."""
    import json
    from app.tenderproof.reviewed_run_import import ReviewedRun, build_run
    from app.tenderproof.publication import _reproduced_evidence
    payload = json.loads((ROOT / "docs/execucao/evidencias/T012/cpcon_open/cpcon-002-reviewed-run-r2.json").read_text(encoding="utf-8"))
    payload["concurso_id"] = 34
    # The preserved r2 receipt contains the old generic title snippet.  Make
    # the drift explicit: fresh extraction must reject this stale evidence.
    payload["fields"] = [
        ({**field, "evidence": [{**evidence, "snippet": "001/2026"} for evidence in field.get("evidence", [])]}
         if field.get("field_name") == "titulo" else field)
        for field in payload["fields"]
    ]
    payload["artifact"]["content_path"] = str(PDF.resolve())
    model = ReviewedRun.model_validate(payload)
    content = PDF.read_bytes(); run = build_run(model, content)
    pages, *_ = extract_pages_isolated(content, artifact_id=run.artifact.artifact_id, owner_id="1", max_pages=40, capacity_wait_s=5)
    artifact = run.artifact.model_copy(update={"storage_path": str(PDF.resolve())})
    fresh = extract_fields(candidate=run.candidates[0], artifact=artifact, pages=pages)
    fresh_title = next(field for field in fresh if field.field_name == "titulo")
    stale_title = next(field for field in run.fields if field.field_name == "titulo")
    assert not _reproduced_evidence(stale_title.evidence[0], fresh_title, {artifact.artifact_id: artifact})
    assert any(field.field_name == "cargos" and field.state.value == "supported" for field in fresh)


def test_cpcon_live_r5_roundtrip_revalidates_all_four_fields(env):
    import json
    from app.tenderproof.reviewed_run_import import ReviewedRun, build_run
    db, _, _, contest, _, store = env
    payload = json.loads((ROOT / "docs/execucao/evidencias/T012/cpcon_open/live-envelope-ready-r6.json").read_text(encoding="utf-8"))
    payload["concurso_id"] = 999
    model = ReviewedRun.model_validate(payload)
    content = PDF.read_bytes(); run = build_run(model, content)
    artifact = run.artifact.model_copy(update={"storage_path": str(PDF.resolve())})
    run.artifact = artifact; store.save_artifact_file(artifact, content)
    source = db.get(Source, contest.source_id); source.source_type = "cpcon_open"
    contest.external_id = _candidate().external_id; contest.link_pagina = _candidate().detail_url_observed
    eligible, blocked = pub._revalidate(run, contest, source, store)
    assert set(("titulo", "orgao", "edital_numero", "cargos")).issubset(eligible)
    assert not any(name in blocked for name in ("titulo", "orgao", "edital_numero", "cargos"))
