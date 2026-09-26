"""TenderProof Fase 3 — endpoints autorizados, comparação e não-publicação."""

from datetime import datetime
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import get_current_user
from app.database import Base, get_db
from app.main import app
from app.models import Concurso, ConcursoVersion, Notification, Source, User


def _sqlite_session():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _client_with_overrides(db, user):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def _user():
    return User(id=1, name="Revisor", email="revisor@example.com", password_hash="x")


def test_endpoints_require_authentication():
    client = TestClient(app)
    assert client.post("/tenderproof/runs", json={"mode": "mock"}).status_code in (401, 403)
    assert client.get("/tenderproof/runs/abc").status_code in (401, 403)
    assert client.post("/tenderproof/runs/abc/select", json={"candidate_id": "x"}).status_code in (401, 403)
    assert client.get("/tenderproof/runs/abc/artifacts/a.pdf").status_code in (401, 403)
    assert client.post("/tenderproof/runs/abc/replay/refresh").status_code in (401, 403)
    assert client.post("/tenderproof/runs/abc/sessions/reconcile").status_code in (401, 403)


def test_mock_flow_end_to_end_without_touching_canonical_tables():
    db = _sqlite_session()
    try:
        source = Source(name="IBGP", base_url="https://novo.ibgpconcursos.com.br",
                        list_url="https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp",
                        source_type="ibgp_open")
        db.add(source)
        db.commit()

        def counts():
            return (
                db.execute(select(func.count()).select_from(Concurso)).scalar(),
                db.execute(select(func.count()).select_from(ConcursoVersion)).scalar(),
                db.execute(select(func.count()).select_from(Notification)).scalar(),
            )

        before = counts()
        client = _client_with_overrides(db, _user())

        started = client.post("/tenderproof/runs", json={"mode": "mock"})
        assert started.status_code == 201, started.text
        run = started.json()
        assert run["source"] == "ibgp_open"
        assert run["is_synthetic_sample"] is True
        assert "Amostra limitada" in run["sample_note"]
        assert len(run["candidates"]) == 2
        run_id = run["run_id"]

        progress = client.get(f"/tenderproof/runs/{run_id}")
        assert progress.status_code == 200
        assert progress.json()["execution_status"] == "awaiting_selection"

        # Sem botão de publicar: o payload de seleção não oferece publicação.
        selected = client.post(f"/tenderproof/runs/{run_id}/select",
                               json={"candidate_id": "cand-42", "mode": "mock"})
        assert selected.status_code == 200, selected.text
        body = selected.json()
        assert body["execution_status"] == "completed"
        assert body["document"]["kind"] == "edital"
        assert body["document"]["reason_chosen"]
        assert body["artifact"]["sha256"] and body["semantic_hash"]
        assert body["session_id"] == "mock-session-001"
        assert body["replay_available"] is True

        result = client.get(f"/tenderproof/runs/{run_id}/result")
        assert result.status_code == 200
        fields = {f["field_name"]: f for f in result.json()["fields"]}
        assert fields["edital_numero"]["state"] == "supported"
        assert fields["edital_numero"]["evidence"][0]["page_number"] == 1
        comparison = {c["field_name"]: c for c in result.json()["comparison"]["fields"]}
        assert result.json()["comparison"]["baseline_collected_at"]
        assert comparison["titulo"]["agreement"] == "agree"
        assert comparison["inscricao_fim"]["agreement"] == "diverge"

        artifact_id = body["artifact"]["artifact_id"]
        pdf = client.get(f"/tenderproof/runs/{run_id}/artifacts/{artifact_id}")
        assert pdf.status_code == 200
        assert pdf.headers["content-type"] == "application/pdf"
        assert pdf.content[:5] == b"%PDF-"

        assert counts() == before  # nenhuma alteração canônica
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        db.close()


def test_unknown_candidate_is_404_and_real_without_creds_is_503(monkeypatch):
    monkeypatch.delenv("SOLARI_API_KEY", raising=False)
    db = _sqlite_session()
    try:
        client = _client_with_overrides(db, _user())
        started = client.post("/tenderproof/runs", json={"mode": "mock"})
        run_id = started.json()["run_id"]
        missing = client.post(f"/tenderproof/runs/{run_id}/select",
                              json={"candidate_id": "cand-999", "mode": "mock"})
        assert missing.status_code == 404
        real = client.post("/tenderproof/runs", json={"mode": "real"})
        assert real.status_code == 503
        assert "pendente" in real.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        db.close()


def test_baseline_from_existing_concurso_is_read_only():
    db = _sqlite_session()
    try:
        source = Source(name="IBGP", base_url="https://novo.ibgpconcursos.com.br",
                        list_url="https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp",
                        source_type="ibgp_open")
        db.add(source)
        db.flush()
        concurso = Concurso(
            source_id=source.id, banca="IBGP", orgao="Prefeitura Municipal De Exemplo",
            titulo="Concurso Prefeitura Municipal de Exemplo MG cod 42",
            edital_numero="01/2026",
            inscricao_inicio=datetime(2026, 3, 10), inscricao_fim=datetime(2026, 4, 20),
            link_pagina="https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42",
            content_hash="h",
        )
        db.add(concurso)
        db.commit()
        client = _client_with_overrides(db, _user())
        started = client.post("/tenderproof/runs", json={"mode": "mock"})
        run_id = started.json()["run_id"]
        selected = client.post(
            f"/tenderproof/runs/{run_id}/select",
            json={"candidate_id": "cand-42", "mode": "mock", "baseline_concurso_id": concurso.id},
        )
        assert selected.status_code == 200, selected.text
        comparison = selected.json()["comparison"]
        assert "somente leitura" in comparison["baseline_origin"] or "leitura" in comparison["baseline_origin"]
        by_name = {c["field_name"]: c for c in comparison["fields"]}
        assert by_name["inscricao_fim"]["agreement"] == "agree"
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        db.close()


def test_review_interface_files_exist_with_required_markers():
    from pathlib import Path

    mobile = Path(__file__).resolve().parents[2] / "mobile"
    screen = mobile / "app" / "tenderproof.tsx"
    api = mobile / "src" / "api" / "tenderproof.ts"
    assert screen.exists() and api.exists()
    text = screen.read_text(encoding="utf-8")
    for marker in ("TenderProof", "candidatos", "evid", "baseline", "replay"):
        assert marker.lower() in text.lower(), marker
    # The multi-source screen now delegates controlled publication to its own
    # component; behavioral approval/stale/rollback tests live in mobile/scripts.
    review = (mobile / "src" / "components" / "TenderProofReview.tsx").read_text(encoding="utf-8")
    assert "ContinuousReview" in text and "PublicationReview" in text
    for marker in ("Aprovar os", "Publicar:", "onEvidence", "proposal.stale", "rollbackTenderProofProposal"):
        assert marker in review, marker
    for marker in ("Demonstra", "Fonte oficial", "sessions", "replay", "diagnostics"):
        assert marker.lower() in text.lower(), marker
    api_text = api.read_text(encoding="utf-8")
    assert "mode" in api_text
    import re
    timeout = re.search(r"LONG_TIMEOUT_MS = ([\d_]+)", api_text)
    assert timeout and int(timeout.group(1).replace("_", "")) >= 400_000


def test_mode_cannot_change_mid_run():
    db = _sqlite_session()
    try:
        client = _client_with_overrides(db, _user())
        started = client.post("/tenderproof/runs", json={"mode": "mock"})
        run_id = started.json()["run_id"]
        assert started.json()["mode"] == "mock"
        swapped = client.post(f"/tenderproof/runs/{run_id}/select",
                              json={"candidate_id": "cand-42", "mode": "real"})
        assert swapped.status_code == 409
        assert "divergente" in swapped.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        db.close()


def test_replay_refresh_and_reconcile_on_mock_run():
    db = _sqlite_session()
    try:
        client = _client_with_overrides(db, _user())
        started = client.post("/tenderproof/runs", json={"mode": "mock"})
        run_id = started.json()["run_id"]
        refresh = client.post(f"/tenderproof/runs/{run_id}/replay/refresh")
        assert refresh.status_code == 200  # sintético: passthrough sem browser
        reconcile = client.post(f"/tenderproof/runs/{run_id}/sessions/reconcile")
        assert reconcile.status_code == 200
        assert any("sintética" in note for note in reconcile.json()["diagnostics"])
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        db.close()


def test_reconcile_missing_session_remains_unconfirmed(monkeypatch):
    import app.tenderproof.solari_adapter as adapter_mod
    from app.tenderproof.contracts import SessionRecord
    from app.tenderproof.store import get_store

    class _Gone(Exception):
        def __init__(self):
            super().__init__("session not found")
            self.status = 404

    class _Sessions:
        async def get(self, session_id):
            raise _Gone()

        async def release(self, session_id):  # pragma: no cover
            raise AssertionError("não deveria soltar sessão inexistente")

    class _Client:
        def __init__(self, **kwargs):
            self.sessions = _Sessions()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

    monkeypatch.setattr(adapter_mod, "_get_solari_class", lambda: _Client)
    monkeypatch.setenv("SOLARI_API_KEY", "test-key")

    from app.tenderproof.service import TenderProofService
    from app.tenderproof.security import TenderProofSettings

    store = get_store()
    service = TenderProofService(store, TenderProofSettings.from_env())
    # Monta run real (não sintético) com sessão aberta não confirmada.
    from app.tenderproof.contracts import TenderProofRun, ExecutionStatus

    probe = TenderProofRun(run_id="tpr-reconcile", execution_status=ExecutionStatus.AWAITING_SELECTION)
    probe.sessions.append(SessionRecord(phase="detail", session_id="sess-gone", closed=False))
    store.put_run(probe)
    out = service.reconcile_sessions("tpr-reconcile")
    assert out.sessions[0].closed is False  # GET 404 não prova encerramento
    assert "desconhecido" in (out.sessions[0].replay_note or "")


def test_other_user_cannot_access_run_or_artifact():
    db = _sqlite_session()
    try:
        client = _client_with_overrides(db, _user())
        run = client.post('/tenderproof/runs', json={'mode': 'mock'}).json()
        run_id = run['run_id']
        result = client.post(f'/tenderproof/runs/{run_id}/select',
                             json={'candidate_id': 'cand-42', 'mode': 'mock'}).json()
        artifact_id = result['artifact']['artifact_id']
        stranger = User(id=2, name='Outro', email='outro@example.com', password_hash='x')
        app.dependency_overrides[get_current_user] = lambda: stranger
        for suffix in ('', '/result', f'/artifacts/{artifact_id}'):
            assert client.get(f'/tenderproof/runs/{run_id}{suffix}').status_code == 404
        for suffix, payload in (('/select', {'candidate_id': 'cand-42'}),
                                ('/replay/refresh', {}), ('/sessions/reconcile', {})):
            assert client.post(f'/tenderproof/runs/{run_id}{suffix}', json=payload).status_code == 404
    finally:
        app.dependency_overrides.clear()
        db.close()


@pytest.mark.parametrize('workbook',[False,True])
def test_owned_supplementary_artifact_is_served_but_unlinked_and_other_owner_are_not(workbook):
    from app.tenderproof.contracts import SupplementaryDocument
    from app.tenderproof.store import get_store
    db = _sqlite_session()
    try:
        client = _client_with_overrides(db, _user())
        created = client.post('/tenderproof/runs', json={'mode':'mock'}).json()
        run_id = created['run_id']
        client.post(f'/tenderproof/runs/{run_id}/select',json={'candidate_id':'cand-42','mode':'mock'})
        store = get_store(); run = store.get_run(run_id)
        content = store.load_artifact_bytes(run.artifact)
        extra = run.artifact.model_copy(update={'artifact_id':'owned-annex','storage_path':None})
        if workbook:
            import hashlib
            content=b'PK\x03\x04preserved workbook'
            extra=extra.model_copy(update={'sha256':hashlib.sha256(content).hexdigest(),'byte_len':len(content),'content_type':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'})
        store.save_artifact_file(extra,content)
        run.supplementary_documents=[SupplementaryDocument(document=run.document,artifact=extra)]
        store.put_run(run)
        response=client.get(f'/tenderproof/runs/{run_id}/artifacts/owned-annex')
        assert response.status_code==200 and response.content==content
        assert response.headers['content-type'].split(';')[0]==('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if workbook else 'application/pdf')
        assert response.headers['content-disposition']==('attachment; filename="owned-annex.xlsx"' if workbook else 'inline; filename="owned-annex.pdf"')
        unlinked=extra.model_copy(update={'artifact_id':'unlinked-annex','storage_path':None})
        store.save_artifact_file(unlinked,content)
        assert client.get(f'/tenderproof/runs/{run_id}/artifacts/unlinked-annex').status_code==404
        app.dependency_overrides[get_current_user]=lambda: User(id=2,name='Outro',email='other@example.com',password_hash='x')
        assert client.get(f'/tenderproof/runs/{run_id}/artifacts/owned-annex').status_code==404
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_run_error_redacts_sdk_connection_credentials():
    from app.tenderproof.service import TenderProofService
    from app.tenderproof.store import TenderProofStore
    from app.tenderproof.solari_adapter import FakeSolariDriver
    class BrokenDriver(FakeSolariDriver):
        def open_listing(self, url):
            raise RuntimeError('wss://example.invalid/connect?token=fixture-sensitive-token')
    run = TenderProofService(TenderProofStore()).start_discovery(BrokenDriver())
    assert run.execution_status.value == 'failed'
    assert 'fixture-sensitive-token' not in run.model_dump_json()
    assert 'suprimido' in run.error
