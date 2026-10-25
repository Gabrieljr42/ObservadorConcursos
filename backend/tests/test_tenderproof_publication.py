"""SQLite disposable DB, real PDF parsing, normal JWT, no network/paid sessions."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from datetime import timedelta
import hashlib
import os
from pathlib import Path
import threading
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import make_url
from sqlalchemy.schema import CreateSchema, DropSchema

from app.auth import create_access_token
from app.database import Base, get_db
from app.models import Alert, Concurso, ConcursoVersion, Notification, Source, User
from app.tenderproof import publication as pub
from app.tenderproof.contracts import Artifact, DiscoveredCandidate, DocumentCandidate, FieldState, TenderProofRun
from app.tenderproof.demo_pdf import make_text_pdf
from app.tenderproof.fields import extract_fields
from app.tenderproof.mock_demo import PDF_PAGE_1, EDITAL_URL_42
from app.tenderproof.pdf_text import extract_pages
from app.tenderproof.publication_models import PublicationOutbox, PublicationProposal, ensure_publication_schema
from app.tenderproof.publication_router import router
from app.tenderproof.store import TenderProofStore


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("TENDERPROOF_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("TENDERPROOF_PUBLICATION_ENABLED", "true")
    monkeypatch.setenv("TENDERPROOF_PUBLICATION_ALLOW_SYNTHETIC", "true")
    monkeypatch.setenv("TENDERPROOF_PUBLISHER_USER_IDS", "1,2")
    postgres_url = os.getenv("TENDERPROOF_TEST_POSTGRES_URL")
    schema = None
    admin_engine = None
    if postgres_url:
        parsed = make_url(postgres_url)
        if parsed.host != "127.0.0.1" or parsed.database != "tenderproof_acceptance" or parsed.username != "fixture":
            raise ValueError("Only the explicitly disposable loopback PostgreSQL fixture is allowed")
        schema = "tp_acceptance_" + uuid.uuid4().hex
        admin_engine = create_engine(postgres_url)
        with admin_engine.begin() as connection:
            connection.execute(CreateSchema(schema))
        engine = create_engine(postgres_url, connect_args={"options": f"-csearch_path={schema}"})
    else:
        engine = create_engine(f"sqlite:///{tmp_path / 'isolated.sqlite'}", connect_args={"check_same_thread": False, "timeout": 20})
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    db = factory()
    user = User(id=1, name="Reviewer", email="review@example.test", password_hash="unused", is_active=True)
    db.add_all([user, User(id=2, name="Other", email="other@example.test", password_hash="unused", is_active=True),
                User(id=3, name="No permission", email="no@example.test", password_hash="unused", is_active=True)])
    source = Source(name="IBGP", base_url="https://novo.ibgpconcursos.com.br", source_type="ibgp_open")
    db.add(source)
    db.flush()
    contest = Concurso(source_id=source.id, external_id="42", banca="IBGP", titulo="Título prévio",
                       orgao="Prefeitura Municipal De Exemplo", edital_numero="01/2026", content_hash="a" * 64,
                       link_pagina="https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42",
                       inscricao_inicio=datetime(2026, 3, 10), inscricao_fim=datetime(2026, 4, 19),
                       salario_min=3500, salario_max=3500, raw_data={"preserve": "canonical crawler context"})
    db.add(contest)
    db.flush()
    db.add(Alert(user_id=1, name="Isolated notification", active=True, only_open=False))
    db.commit()
    content = make_text_pdf([PDF_PAGE_1])
    artifact = Artifact(artifact_id="test-artifact", sha256=hashlib.sha256(content).hexdigest(), byte_len=len(content),
                        url_requested=EDITAL_URL_42, url_final=EDITAL_URL_42, downloaded_at=datetime.utcnow())
    store = TenderProofStore()
    store.save_artifact_file(artifact, content)
    candidate = DiscoveredCandidate(candidate_id="cand-42", external_id="42", title_observed="Concurso Prefeitura Municipal de Exemplo MG cod 42",
                                    detail_url_observed=contest.link_pagina, observed_at=datetime.utcnow())
    pages, *_ = extract_pages(content, artifact_id=artifact.artifact_id)
    run = TenderProofRun(run_id="test-run", owner_user_id=1, execution_status="completed", validation_status="valid",
                        is_synthetic_sample=True, candidates=[candidate], selected_candidate_id=candidate.candidate_id,
                        document=DocumentCandidate(doc_id="doc", title="Edital de abertura", kind="edital", url_requested=EDITAL_URL_42),
                        artifact=artifact, fields=extract_fields(candidate=candidate, artifact=artifact, pages=pages))
    yield db, factory, user, contest, run, store
    db.close()
    engine.dispose()
    if admin_engine:
        with admin_engine.begin() as connection:
            connection.execute(DropSchema(schema, cascade=True))
        admin_engine.dispose()


def test_access_birigui_reviewed_run_revalidates_cargos_and_material_diff(env):
    db, _, user, contest, run, store = env
    source = db.get(Source, contest.source_id)
    source.source_type = "access_open"
    source.name = "ACCESS"
    contest.external_id = "183"
    contest.titulo = "Concurso Público 01/2026"
    contest.orgao = "Prefeitura Municipal De Birigui-Sp"
    contest.edital_numero = "179/2026"
    contest.link_pagina = "https://access.selecao.net.br/informacoes/183/"
    content = (Path(__file__).resolve().parents[2] / "docs/execucao/evidencias/T010/id1.pdf").read_bytes()
    document_url = "https://anexos-r2.selecao.net.br/uploads/422/concursos/183/anexos/7dec9d89-d5ee-4948-bddb-46a2496f13f5.pdf"
    artifact = Artifact(artifact_id="art-5c4c41a458", sha256=hashlib.sha256(content).hexdigest(),
                        byte_len=len(content), url_requested=document_url,
                        url_final=document_url, downloaded_at=datetime.utcnow())
    store.save_artifact_file(artifact, content)
    candidate = DiscoveredCandidate(candidate_id="access-183", external_id="183",
                                    title_observed="Prefeitura Municipal de Birigui/SP",
                                    detail_url_observed=contest.link_pagina, observed_at=datetime.utcnow(), source="access_open")
    pages, *_ = extract_pages(content, artifact_id=artifact.artifact_id)
    extracted = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    imported_fields = [{"field_name": field.field_name, "value": field.value,
                        "original_value": field.original_value,
                        "evidence": [e.model_dump(mode="json") for e in field.evidence],
                        "units": field.units}
                       for field in extracted
                       if field.field_name == "cargos"]
    envelope = {
        "schema": "tenderproof.reviewed-run.v1", "source": "access_open", "concurso_id": contest.id,
        "external_id": "183", "title": "Prefeitura Municipal de Birigui/SP",
        "detail_url": contest.link_pagina, "observed_at": "2026-09-08T16:10:57.600948Z",
        "reference_only": True, "owner_user_id": user.id, "pending_fields": [],
        "artifact": {"artifact_id": artifact.artifact_id, "sha256": artifact.sha256, "byte_len": artifact.byte_len,
                      "url_requested": document_url, "url_final": document_url,
                      "content_type": "application/pdf", "downloaded_at": "2026-09-08T16:11:28.760592Z",
                      "content_path": str(Path(__file__).resolve().parents[2] / "docs/execucao/evidencias/T010/id1.pdf")},
        "fields": imported_fields,
    }
    imported = __import__("app.tenderproof.reviewed_run_import", fromlist=["import_reviewed_run"])
    imported.import_reviewed_run(envelope, store, dry_run=False)
    run = store.get_run(imported._run_id(imported.ReviewedRun.model_validate(envelope)))
    assert run is not None and list(run.field_map()) == ["cargos"]
    assert run.candidates[0].title_observed == "Prefeitura Municipal de Birigui/SP"
    assert run.field_map()["cargos"].units == {"remuneracao": "BRL/hora-aula", "jornada": "horas semanais"}
    eligible, blocked = pub._revalidate(run, contest, source, store)
    assert "cargos" not in blocked
    assert eligible["cargos"][0]["vagas_imediatas"] == 10
    assert eligible["cargos"][0]["vagas_ampla_concorrencia"] == 9
    assert eligible["cargos"][0]["vagas_pcd"] == 1
    assert eligible["cargos"][0]["remuneracao_observacao"] == "por hora-aula"
    assert contest.cargos is None
    proposal = pub.create_proposal(db, run=run, concurso_id=contest.id, user=user, store=store)
    assert proposal["state"] == "proposed"
    assert "cargos" in proposal["eligible_fields"]
    persisted = db.get(PublicationProposal, proposal["id"])
    assert persisted.payload["proposed"]["cargos"] == eligible["cargos"]
    assert persisted.payload["proposed"]["cargos"][0]["vagas_imediatas"] == 10


def proposal(env, fields=("inscricao_fim",)):
    db, _, user, contest, run, store = env
    result = pub.create_proposal(db, run=run, concurso_id=contest.id, user=user, store=store)
    return pub.approve_proposal(db, proposal_id=result["id"], proposal_hash=result["proposal_hash"], fields=list(fields), user=user, store=store)


def test_revalidation_uses_current_owner_source_limits(env, monkeypatch):
    from app.tenderproof.continuous_store import SourcePolicy, get_continuous_store
    db, _, user, contest, run, store = env
    monkeypatch.setenv('TENDERPROOF_MAX_DOWNLOAD_BYTES', '1024')
    content = make_text_pdf([PDF_PAGE_1, 'Documento de teste: ' + 'texto adicional ' * 30])
    run.artifact.sha256 = hashlib.sha256(content).hexdigest()
    run.artifact.byte_len = len(content)
    store.save_artifact_file(run.artifact, content)
    pages, *_ = extract_pages(content, artifact_id=run.artifact.artifact_id)
    run.fields = extract_fields(candidate=run.candidates[0], artifact=run.artifact, pages=pages)
    assert run.artifact.byte_len > 1024
    queue = get_continuous_store()
    # Another owner's allowance cannot authorize this run.
    queue.configure(2, run.source, SourcePolicy(max_download_bytes=45000000))
    with pytest.raises(HTTPException, match='limite excedido'):
        pub._revalidate(run, contest, db.get(Source, contest.source_id), store)
    queue.configure(user.id, run.source, SourcePolicy(enabled=False, max_download_bytes=45000000))
    eligible, _ = pub._revalidate(run, contest, db.get(Source, contest.source_id), store)
    assert eligible['inscricao_fim'] == next(f.value for f in run.fields if f.field_name == 'inscricao_fim')
    # Lowering the current policy must be enforced even for preserved bytes.
    queue.configure(user.id, run.source, SourcePolicy(max_download_bytes=1024))
    with pytest.raises(HTTPException, match='limite excedido'):
        pub._revalidate(run, contest, db.get(Source, contest.source_id), store)


def test_revalidation_refuses_scholarship_as_personnel_selection(env):
    from app.tenderproof.fapern_adapter import FapernAdapter, folder_url
    from app.tenderproof.fapern_drive import ROOT
    from test_tenderproof_selection_scope import HEADER, CLAUSE
    db, _, _, contest, run, store = env
    adapter=FapernAdapter()
    url=folder_url('https://drive.rn.gov.br/index.php/s/PublicFixture123',ROOT+'Editais 2033/Edital 42-2033/')
    candidate=adapter.candidate_from_url(url)
    source=db.get(Source,contest.source_id);source.source_type='fapern_selection'
    contest.external_id=candidate.external_id;contest.link_pagina=url
    run.source=candidate.source;run.candidates=[candidate];run.selected_candidate_id=candidate.candidate_id
    import json
    payload={'format':'fapern-directory/1','url':url,'path':ROOT+'Editais 2033/Edital 42-2033/',
             'proof':{'share_url':'https://drive.rn.gov.br/index.php/s/PublicFixture123'},
             'rows':[{'name':'Edital de Abertura.pdf','path':ROOT+'Editais 2033/Edital 42-2033/Edital de Abertura.pdf','is_directory':False}]}
    run.document=adapter.documents(json.dumps(payload),candidate)[0]
    content=make_text_pdf([HEADER,CLAUSE])
    run.artifact.sha256=hashlib.sha256(content).hexdigest();run.artifact.byte_len=len(content)
    run.artifact.url_requested=run.artifact.url_final=run.document.url_requested
    store.save_artifact_file(run.artifact,content)
    with pytest.raises(HTTPException,match='Fora do escopo de contratação de pessoal'):
        pub._revalidate(run,contest,source,store)


def apply(env, p):
    db, _, user, _, _, store = env
    return pub.apply_proposal(db, proposal_id=p["id"], proposal_hash=p["proposal_hash"], user=user, store=store)


def count(db, model):
    return db.scalar(select(func.count()).select_from(model))


def utc(value):
    """SQLite discards tzinfo; PostgreSQL returns aware UTC for timestamptz."""
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def test_apply_twice_one_version_correct_diff_and_no_precommit_notifications(env):
    db, _, _, contest, _, _ = env
    p = proposal(env)
    first = apply(env, p)
    assert first["state"] == "applied"
    assert set(first["result"]["diff"]) == {"inscricao_fim"}
    assert first["result"]["diff"]["inscricao_fim"]["old"].startswith("2026-04-19")
    assert first["result"]["diff"]["inscricao_fim"]["new"].startswith("2026-04-20")
    assert apply(env, p)["version_id"] == first["version_id"]
    assert count(db, ConcursoVersion) == count(db, PublicationOutbox) == 1
    assert count(db, Notification) == 0
    db.refresh(contest)
    assert contest.raw_data == {"preserve": "canonical crawler context"}
    assert contest.content_hash == "a" * 64


def test_reprocessed_same_values_metadata_do_not_create_version(env):
    db, _, _, _, run, _ = env
    apply(env, proposal(env))
    run.run_id = "reprocessed"
    run.session_id = "different-session"
    run.diagnostics = ["new nonsemantic diagnostic"]
    result = apply(env, proposal(env))
    assert result["state"] == "no_change"
    assert result["result"]["diff"] == {}
    assert count(db, ConcursoVersion) == count(db, PublicationOutbox) == 1


def test_unknown_conflict_and_salary_scope_preserve_existing(env):
    db, _, user, contest, run, store = env
    fields = run.field_map()
    fields["orgao"].state = FieldState.UNKNOWN
    fields["orgao"].reason = "no supported organization"
    fields["inscricao_inicio"].state = FieldState.CONFLICT
    fields["inscricao_inicio"].reason = "contradictory dates"
    p = pub.create_proposal(db, run=run, concurso_id=contest.id, user=user, store=store)
    assert {"orgao", "inscricao_inicio", "remuneracao"}.issubset(p["blocked_fields"])
    with pytest.raises(HTTPException) as exc:
        pub.approve_proposal(db, proposal_id=p["id"], proposal_hash=p["proposal_hash"], fields=["orgao"], user=user, store=store)
    assert exc.value.status_code == 422
    p = pub.approve_proposal(db, proposal_id=p["id"], proposal_hash=p["proposal_hash"], fields=["inscricao_fim"], user=user, store=store)
    apply(env, p)
    db.refresh(contest)
    assert contest.orgao == "Prefeitura Municipal De Exemplo"
    assert utc(contest.inscricao_inicio) == datetime(2026, 3, 10, tzinfo=timezone.utc)
    assert float(contest.salario_min) == float(contest.salario_max) == 3500


def test_stale_baseline_and_recomparison(env):
    db, _, user, contest, run, store = env
    p = proposal(env)
    contest.titulo = "Changed concurrently by crawler"
    db.commit()
    with pytest.raises(HTTPException) as exc:
        apply(env, p)
    assert exc.value.status_code == 409
    assert pub.get_proposal(db, p["id"], user)["stale"] is True
    fresh = pub.create_proposal(db, run=run, concurso_id=contest.id, user=user, store=store)
    assert fresh["id"] != p["id"] and fresh["state"] == "proposed"
    assert count(db, ConcursoVersion) == 0


def test_failure_rolls_back_canonical_version_outbox_and_claim(env, monkeypatch):
    db, _, _, contest, _, _ = env
    p = proposal(env)
    original = pub._version
    def broken(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("injected transaction failure")
    monkeypatch.setattr(pub, "_version", broken)
    with pytest.raises(RuntimeError):
        apply(env, p)
    db.refresh(contest)
    assert utc(contest.inscricao_fim) == datetime(2026, 4, 19, tzinfo=timezone.utc)
    assert count(db, ConcursoVersion) == count(db, PublicationOutbox) == 0
    row = db.get(PublicationProposal, p["id"])
    assert row.state == "approved" and row.applied_observation is None


def test_outbox_failure_retry_atomic_and_deduplicated(env, monkeypatch):
    db, _, user, _, _, _ = env
    apply(env, proposal(env))
    row = db.scalar(select(PublicationOutbox))
    original = pub.create_notifications_for_version
    def broken(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("isolated DB notification failure")
    monkeypatch.setattr(pub, "create_notifications_for_version", broken)
    with pytest.raises(RuntimeError):
        pub.drain_outbox(db, outbox_id=row.id, user=user)
    assert count(db, Notification) == 0
    assert count(db, ConcursoVersion) == 1
    db.refresh(row)
    assert row.state == "pending"
    monkeypatch.setattr(pub, "create_notifications_for_version", original)
    assert pub.drain_outbox(db, outbox_id=row.id, user=user)["created"] == 1
    assert pub.drain_outbox(db, outbox_id=row.id, user=user)["created"] == 0
    assert count(db, Notification) == 1


def test_rollback_audit_preserves_history_and_blocks_later_changes(env):
    db, _, user, contest, _, _ = env
    p = proposal(env)
    apply(env, p)
    result = pub.rollback_proposal(db, proposal_id=p["id"], reason="Reviewer corrects test observation", user=user)
    assert result["state"] == "rolled_back"
    assert result["rollback_by"] == user.id
    assert result["rollback_reason"] == "Reviewer corrects test observation"
    assert result["rollback_version_id"] != result["version_id"]
    assert count(db, ConcursoVersion) == 2
    db.refresh(contest)
    assert utc(contest.inscricao_fim) == datetime(2026, 4, 19, tzinfo=timezone.utc)
    assert db.scalar(select(PublicationOutbox).where(PublicationOutbox.version_id == result["version_id"])).state == "superseded"
    assert pub.rollback_proposal(db, proposal_id=p["id"], reason="retry", user=user)["rollback_version_id"] == result["rollback_version_id"]


def test_rollback_rejects_later_canonical_change(env):
    db, _, user, contest, _, _ = env
    p = proposal(env)
    apply(env, p)
    contest.titulo = "Later change"
    db.commit()
    with pytest.raises(HTTPException) as exc:
        pub.rollback_proposal(db, proposal_id=p["id"], reason="cannot erase later change", user=user)
    assert exc.value.status_code == 409
    assert count(db, ConcursoVersion) == 1


@pytest.mark.parametrize("tamper", ["hash", "page", "snippet", "source", "value"])
def test_invalid_evidence_is_rejected_or_field_blocked(env, tamper):
    db, _, user, contest, run, store = env
    f = run.field_map()["inscricao_fim"]
    if tamper == "hash":
        run.artifact.sha256 = "0" * 64
        with pytest.raises(HTTPException):
            pub.create_proposal(db, run=run, concurso_id=contest.id, user=user, store=store)
        return
    if tamper == "page": f.evidence[0].page_number = 999
    if tamper == "snippet": f.evidence[0].snippet = "Not in the PDF"
    if tamper == "source": f.evidence[0].source_url = "https://evil.example/pdf"
    if tamper == "value": f.value = "2099-01-01"
    p = pub.create_proposal(db, run=run, concurso_id=contest.id, user=user, store=store)
    assert "inscricao_fim" in p["blocked_fields"]


def test_approval_bound_to_hash_and_artifact_revalidated_at_apply(env):
    db, _, user, _, run, store = env
    p = proposal(env)
    with pytest.raises(HTTPException) as exc:
        pub.apply_proposal(db, proposal_id=p["id"], proposal_hash="0" * 64, user=user, store=store)
    assert exc.value.status_code == 409
    store.put_blob(run.artifact.artifact_id, b"tampered")
    with pytest.raises(HTTPException) as exc:
        apply(env, p)
    assert exc.value.status_code == 422
    assert count(db, ConcursoVersion) == 0


@pytest.mark.parametrize("tamper", ["contest_id", "url", "annex", "other_pdf"])
def test_strong_identity_refuses_wrong_target_and_annex(env, tamper):
    db, _, user, contest, run, store = env
    if tamper == "contest_id": contest.external_id = "77"
    if tamper == "url": contest.link_pagina += "&other=77"
    if tamper == "annex": run.document.title = "Anexo ao edital"
    if tamper == "other_pdf":
        data = make_text_pdf([PDF_PAGE_1.replace("cod=42", "cod=77")])
        run.artifact.sha256 = hashlib.sha256(data).hexdigest()
        run.artifact.byte_len = len(data)
        store.put_blob(run.artifact.artifact_id, data)
    with pytest.raises(HTTPException) as exc:
        pub.create_proposal(db, run=run, concurso_id=contest.id, user=user, store=store)
    assert exc.value.status_code == 422


def test_real_jwt_authorization_and_owner_isolation(env, monkeypatch):
    db, factory, _, contest, run, store = env
    store.put_run(run)
    import app.tenderproof.publication_router as api
    monkeypatch.setattr(api, "get_store", lambda: store)
    app = FastAPI()
    app.include_router(router)
    def dependency():
        with factory() as session:
            yield session
    app.dependency_overrides[get_db] = dependency
    client = TestClient(app)
    path = "/tenderproof/publications/proposals"
    payload = {"run_id": run.run_id, "concurso_id": contest.id}
    assert client.post(path, json=payload).status_code == 401
    assert client.post(path, json=payload, headers={"Authorization": "Bearer invalid"}).status_code == 401
    assert client.post(path, json=payload, headers={"Authorization": "Bearer " + create_access_token(3)}).status_code == 403
    assert client.post(path, json=payload, headers={"Authorization": "Bearer " + create_access_token(2)}).status_code == 404
    headers = {"Authorization": "Bearer " + create_access_token(1)}
    response = client.post(path, json=payload, headers=headers)
    assert response.status_code == 201, response.text
    p = response.json()
    detail = path + "/" + p["id"]
    assert client.get(detail, headers={"Authorization": "Bearer " + create_access_token(2)}).status_code == 404
    assert client.post(detail + "/approve", json={"proposal_hash": p["proposal_hash"], "fields": ["inscricao_fim"]}, headers=headers).status_code == 200
    result = client.post(detail + "/apply", json={"proposal_hash": p["proposal_hash"]}, headers=headers)
    assert result.status_code == 200, result.text
    assert result.json()["state"] == "applied"


def test_concurrent_duplicate_requests_persist_one_application(env):
    db, factory, _, _, _, store = env
    p = proposal(env)
    db.rollback()
    barrier = threading.Barrier(2)
    def worker():
        with factory() as session:
            user = session.get(User, 1)
            barrier.wait(timeout=10)
            try:
                return pub.apply_proposal(session, proposal_id=p["id"], proposal_hash=p["proposal_hash"], user=user, store=store)["state"]
            except HTTPException as exc:
                return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: worker(), range(2)))
    assert "applied" in results and all(r in ("applied", 409) for r in results)
    assert count(db, ConcursoVersion) == count(db, PublicationOutbox) == 1
    assert count(db, PublicationProposal) == 1


def test_distinct_semantic_replay_returns_original_without_second_version(env):
    db, _, user, contest, run, store = env
    first = proposal(env)
    applied = apply(env, first)
    assert applied["state"] == "applied"
    versions = count(db, ConcursoVersion)
    outbox = count(db, PublicationOutbox)
    run.updated_at = run.updated_at + timedelta(seconds=1)
    requested = pub.create_proposal(db, run=run, concurso_id=contest.id, user=user, store=store)
    assert requested["id"] != first["id"]
    requested = pub.approve_proposal(db, proposal_id=requested["id"], proposal_hash=requested["proposal_hash"],
                                     fields=["inscricao_fim"], user=user, store=store)
    replay = apply(env, requested)
    assert replay["idempotent_replay"] is True
    assert replay["original_proposal_id"] == first["id"]
    assert replay["requested_proposal_id"] == requested["id"]
    assert count(db, ConcursoVersion) == versions
    assert count(db, PublicationOutbox) == outbox


def test_semantic_replay_divergent_fields_or_stale_baseline_remains_409(env):
    db, _, user, contest, run, store = env
    first = proposal(env)
    apply(env, first)
    run.updated_at = run.updated_at + timedelta(seconds=1)
    divergent = pub.create_proposal(db, run=run, concurso_id=contest.id, user=user, store=store)
    divergent = pub.approve_proposal(db, proposal_id=divergent["id"], proposal_hash=divergent["proposal_hash"],
                                     fields=["inscricao_inicio"], user=user, store=store)
    with pytest.raises(HTTPException) as exc:
        apply(env, divergent)
    assert exc.value.status_code == 409
    run.updated_at = run.updated_at + timedelta(seconds=1)
    stale = pub.create_proposal(db, run=run, concurso_id=contest.id, user=user, store=store)
    stale = pub.approve_proposal(db, proposal_id=stale["id"], proposal_hash=stale["proposal_hash"],
                                 fields=["inscricao_fim"], user=user, store=store)
    contest.titulo = "Alteração concorrente"
    db.commit()
    with pytest.raises(HTTPException) as exc:
        apply(env, stale)
    assert exc.value.status_code == 409


def test_migration_repeatable_and_defaults_fail_closed(env, monkeypatch):
    db, _, user, _, _, _ = env
    ensure_publication_schema(db.get_bind())
    ensure_publication_schema(db.get_bind())
    p = proposal(env)
    monkeypatch.delenv("TENDERPROOF_PUBLICATION_ENABLED")
    with pytest.raises(HTTPException) as exc:
        apply(env, p)
    assert exc.value.status_code == 403
    monkeypatch.delenv("TENDERPROOF_PUBLISHER_USER_IDS")
    with pytest.raises(HTTPException) as exc:
        pub.get_proposal(db, p["id"], user)
    assert exc.value.status_code == 403


def test_unchanged_traditional_crawl_after_merge_creates_no_version(env, monkeypatch, legacy_crawler_enabled):
    from app.connectors.common import build_hash
    from app.services import CrawlService
    import app.services as crawler
    db, _, _, contest, _, _ = env
    # Production connectors hash raw_data, not normalized business fields.
    contest.content_hash = build_hash(contest.raw_data)
    db.commit()
    apply(env, proposal(env))
    db.refresh(contest)
    item = {column.name: getattr(contest, column.name) for column in Concurso.__table__.columns
            if column.name not in ("id", "source_id", "created_at", "updated_at")}
    item["content_hash"] = build_hash(item["raw_data"])
    item["fetched_at"] = datetime(2026, 9, 8)
    class ConnectorDouble:
        def crawl(self):
            return [item]
    monkeypatch.setattr(crawler, "get_connector", lambda *args, **kwargs: ConnectorDouble())
    result = CrawlService(db).crawl_source(contest.source_id)
    assert result["unchanged"] == 1
    assert result["versions_created"] == 0
    assert count(db, ConcursoVersion) == 1


def test_concurrent_outbox_drain_creates_one_internal_notification(env):
    db, factory, _, _, _, _ = env
    apply(env, proposal(env))
    outbox_id = db.scalar(select(PublicationOutbox.id))
    db.rollback()
    barrier = threading.Barrier(2)
    def worker():
        with factory() as session:
            user = session.get(User, 1)
            barrier.wait(timeout=10)
            try:
                return pub.drain_outbox(session, outbox_id=outbox_id, user=user)
            except HTTPException as exc:
                return {"status": exc.status_code}
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: worker(), range(2)))
    assert sum(r.get("created", 0) for r in results) == 1
    assert count(db, Notification) == 1


def test_rollback_preserves_delivered_notifications_and_has_distinct_reversal(env):
    db, _, user, _, _, _ = env
    p = proposal(env)
    apply(env, p)
    original = db.scalar(select(PublicationOutbox))
    pub.drain_outbox(db, outbox_id=original.id, user=user)
    result = pub.rollback_proposal(db, proposal_id=p["id"], reason="Correct already notified change", user=user)
    assert count(db, Notification) == 1
    reversal = db.scalar(select(PublicationOutbox).where(PublicationOutbox.version_id == result["rollback_version_id"]))
    assert pub.drain_outbox(db, outbox_id=reversal.id, user=user)["created"] == 1
    assert count(db, Notification) == 2
    db.refresh(original)
    assert original.state == "delivered"


def test_additive_migration_over_canonical_schema_and_seed_snapshot_provenance(tmp_path):
    from app.tenderproof.publication_demo import seed_isolated_baseline
    engine = create_engine(f"sqlite:///{tmp_path / 'migration.sqlite'}")
    Base.metadata.create_all(engine, tables=[Source.__table__, User.__table__, Concurso.__table__, ConcursoVersion.__table__])
    assert "tenderproof_publication_proposals" not in inspect(engine).get_table_names()
    ensure_publication_schema(engine)
    ensure_publication_schema(engine)
    assert "tenderproof_publication_outbox" in inspect(engine).get_table_names()
    with sessionmaker(engine)() as db:
        snapshot = {"titulo": "Preserved fixture baseline", "banca": "IBGP", "external_id": "42",
                    "link_pagina": "https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42", "content_hash": "a" * 64}
        source = {"name": "IBGP", "base_url": "https://novo.ibgpconcursos.com.br", "source_type": "ibgp_open"}
        with pytest.raises(ValueError):
            seed_isolated_baseline(db, canonical_snapshot=snapshot, source_snapshot=source, provenance={})
        contest, receipt = seed_isolated_baseline(db, canonical_snapshot=snapshot, source_snapshot=source,
                                                  provenance={"kind": "synthetic_fixture", "origin": "unit fixture", "collected_at": "2026-09-07"})
        assert contest.titulo == snapshot["titulo"]
        assert receipt["kind"] == "synthetic_fixture" and len(receipt["snapshot_sha256"]) == 64
    engine.dispose()
