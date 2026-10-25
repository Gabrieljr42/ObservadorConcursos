from pathlib import Path
from io import BytesIO
from datetime import datetime
import hashlib

from pypdf import PdfReader
from test_tenderproof_publication import env

from app.models import Source
from app.tenderproof import publication as pub
from app.tenderproof.contracts import Artifact, DiscoveredCandidate, PageText
from app.tenderproof.fields import extract_fields
from app.tenderproof.fapese_pronera_parser import (
    ARTIFACT_ID, CONCURSO_ID, DOCUMENT_URL, EXPECTED_BYTES, EXPECTED_SHA256,
    EXTERNAL_ID, SOURCE, build_reviewed_payload, derive, parse, preflight,
)
from app.tenderproof.reviewed_run_import import ReviewedRun, _run_id, build_run


PDF = Path(__file__).parents[2] / "docs/execucao/evidencias/T010/id14.pdf"


def test_id14_parser_is_pinned_and_preserves_service_units():
    content = PDF.read_bytes()
    assert len(content) == EXPECTED_BYTES
    assert hashlib.sha256(content).hexdigest() == EXPECTED_SHA256
    assert preflight(content)["pages"] == 17
    parsed = parse(content)
    assert derive(parsed) == derive(parse(content))
    assert [c["nome"] for c in parsed["cargos"]] == [
        "Articulador(a) político-pedagógico", "Técnico de apoio"
    ]
    assert [c["remuneracao"] for c in parsed["cargos"]] == ["60.00", "7488.00"]
    assert all(c["vagas_imediatas"] is None and c["cadastro_reserva"] is None for c in parsed["cargos"])
    assert parsed["pending_fields"] == ["quantidade de oportunidades", "entrevista_data"]
    payload = build_reviewed_payload(content)
    assert payload["pending_fields"] == [] and payload["reference_only"] is True
    assert {f["field_name"] for f in payload["fields"]} == {"cargos"}


def test_id14_fields_route_and_isolated_proposal(env):
    db, _, user, contest, _, store = env
    content = PDF.read_bytes()
    artifact = Artifact(artifact_id=ARTIFACT_ID, sha256=EXPECTED_SHA256,
        byte_len=EXPECTED_BYTES, url_requested=DOCUMENT_URL, url_final=DOCUMENT_URL,
        downloaded_at="2026-09-09T21:16:56.621551Z", storage_path=None)
    artifact = store.save_artifact_file(artifact, content)
    candidate = DiscoveredCandidate(candidate_id="fapese-007", external_id=EXTERNAL_ID,
        title_observed="FAPESE - PRONERA - EDITAL Nº 007/2026",
        detail_url_observed="https://www.fapese.org.br/pronera/",
        observed_at="2026-09-09T21:16:56.621551Z", source=SOURCE)
    pages = [PageText(artifact_id=ARTIFACT_ID, page_number=i + 1,
             text=(page.extract_text() or ""))
             for i, page in enumerate(PdfReader(BytesIO(content)).pages)]
    fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    jobs = next(f for f in fields if f.field_name == "cargos")
    assert jobs.state.value == "supported" and len(jobs.value) == 2
    payload = build_reviewed_payload(content, owner_user_id=user.id)
    payload["concurso_id"] = contest.id
    payload["artifact"].pop("content_base64")
    payload["artifact"]["content_path"] = str(PDF.resolve())
    local_run = build_run(ReviewedRun.model_validate(payload), content)
    local_run.artifact.storage_path = artifact.storage_path
    store.put_run(local_run)
    run = store.get_run(_run_id(ReviewedRun.model_validate(payload)))
    source = db.get(Source, contest.source_id)
    source.source_type = SOURCE
    source.name = "FAPESE"
    contest.external_id = EXTERNAL_ID
    contest.titulo = payload["title"]
    contest.orgao = "FAPESE"
    contest.edital_numero = EXTERNAL_ID
    contest.link_pagina = "https://www.fapese.org.br/pronera/"
    contest.cargos = None
    contest.inscricao_inicio = datetime(2026, 9, 7)
    contest.inscricao_fim = datetime(2026, 9, 14)
    db.commit()
    eligible, blocked = pub._revalidate(run, contest, source, store)
    assert list(eligible) == ["cargos"]
    assert set(blocked) == {"titulo", "orgao", "edital_numero", "prova_data", "inscricao_inicio", "inscricao_fim", "taxa"}
    assert all(item["vagas_imediatas"] is None and item["cadastro_reserva"] is None for item in eligible["cargos"])
    proposal = pub.create_proposal(db, run=run, concurso_id=contest.id, user=user, store=store)
    assert proposal["state"] == "proposed"
    assert set(proposal["eligible_fields"]) == {"cargos"}
