"""Persistent ledger + real local PDF subprocess; remote doubles explicitly labelled."""
import hashlib
import json
import sqlite3
import time
import threading
import os
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

from app.tenderproof.demo_pdf import make_text_pdf
from app.tenderproof.processing import ProcessingService, ProcessingLimits, ProcessingError
from app.tenderproof.processing_solari import SolariSandboxProcessor


@pytest.fixture
def pdf():
    return make_text_pdf(['TenderProof fixture text'])


def test_real_subprocess_persistence_and_hash(tmp_path, pdf):
    service = ProcessingService(tmp_path)
    job = service.enqueue('owner', pdf)
    finished = service.execute(job['id'], 'owner')
    assert finished['state'] == 'succeeded'
    assert finished['attempts'] == 1
    restarted = ProcessingService(tmp_path)
    result = restarted.result(job['id'], 'owner')
    assert result['input_sha256'] == hashlib.sha256(pdf).hexdigest()
    assert result['pages'][0]['page_number'] == 1
    assert 'fixture text' in result['pages'][0]['text']
    assert restarted.execute(job['id'], 'owner')['attempts'] == 1


@pytest.mark.skipif(os.name != 'nt', reason='Windows CreateProcess current-directory limit')
def test_windows_long_evidence_path_uses_real_subprocess(tmp_path, pdf):
    root = tmp_path
    while len(str(root)) < 190:
        root = root / ('evidence-' + 'x' * 20)
    service = ProcessingService(root)
    job = service.enqueue('long-path-owner', pdf)
    directory = root / hashlib.sha256(b'long-path-owner').hexdigest() / job['id']
    assert len(str(directory)) > 260
    assert service.execute(job['id'], 'long-path-owner')['state'] == 'succeeded'
    result = service.result(job['id'], 'long-path-owner')
    assert result['input_sha256'] == hashlib.sha256(pdf).hexdigest()
    assert 'fixture text' in result['pages'][0]['text']
    assert (directory / 'input.pdf').read_bytes() == pdf


@pytest.mark.parametrize('prefix',[b'\n\n',b' \t\r\n'*4])
def test_official_ascii_prefix_keeps_raw_hash_and_extracts(tmp_path,pdf,prefix):
    content=prefix+pdf
    service=ProcessingService(tmp_path)
    job=service.enqueue('owner',content)
    assert service.execute(job['id'],'owner')['state']=='succeeded'
    result=service.result(job['id'],'owner')
    assert result['input_sha256']==hashlib.sha256(content).hexdigest()
    assert 'fixture text' in result['pages'][0]['text']


@pytest.mark.parametrize('prefix',[b' '*17,b'<html>',b'\x00'])
def test_noncontract_pdf_prefix_rejected(tmp_path,pdf,prefix):
    with pytest.raises(ProcessingError,match='invalid_document'):
        ProcessingService(tmp_path).enqueue('owner',prefix+pdf)


def test_owner_isolation_and_generated_paths(tmp_path, pdf):
    service = ProcessingService(tmp_path)
    job = service.enqueue('../../owner', pdf)
    for method in (service.get, service.cancel, service.execute, service.result):
        with pytest.raises(ProcessingError, match='job_not_found'):
            method(job['id'], 'other')
    assert (tmp_path / hashlib.sha256(b'../../owner').hexdigest() / job['id'] / 'input.pdf').is_file()


@pytest.mark.parametrize('kwargs', [{'max_pages': 0}, {'max_attempts': 4}, {'total_seconds': float('nan')},
                                  {'budget_usd': float('inf')}, {'operation_seconds': 61}])
def test_invalid_limits(kwargs):
    with pytest.raises(ProcessingError):
        ProcessingLimits(**kwargs)


def test_invalid_and_input_limit(tmp_path, pdf):
    service = ProcessingService(tmp_path)
    with pytest.raises(ProcessingError, match='invalid_document'):
        service.enqueue('owner', b'HTML')
    with pytest.raises(ProcessingError, match='input_limit'):
        service.enqueue('owner', pdf, limits=ProcessingLimits(max_bytes=1))
    job = service.enqueue('owner', b'%PDF-invalid')
    assert service.execute(job['id'], 'owner')['error']['code'] == 'invalid_document'


@pytest.mark.parametrize('limits,code', [(ProcessingLimits(max_pages=1), 'page_limit'),
    (ProcessingLimits(max_output_bytes=20), 'output_limit'),
    (ProcessingLimits(total_seconds=0.001, operation_seconds=0.001), 'timeout')])
def test_enforced_local_limits(tmp_path, limits, code):
    service = ProcessingService(tmp_path)
    job = service.enqueue('owner', make_text_pdf(['one', 'two']), limits=limits)
    assert service.execute(job['id'], 'owner')['error']['code'] == code


def test_cancellation_queued(tmp_path, pdf):
    service = ProcessingService(tmp_path)
    job = service.enqueue('owner', pdf)
    service.cancel(job['id'], 'owner')
    assert service.execute(job['id'], 'owner')['state'] == 'cancelled'
    assert service.get(job['id'], 'owner')['attempts'] == 0


def test_tampered_artifacts_and_cleanup(tmp_path, pdf):
    service = ProcessingService(tmp_path)
    job = service.enqueue('owner', pdf)
    service.execute(job['id'], 'owner')
    output = next(tmp_path.glob('*/*/output.json'))
    output.write_text('{}')
    with pytest.raises(ProcessingError, match='artifact_hash_mismatch'):
        service.result(job['id'], 'owner')
    assert service.cleanup(retention_seconds=0) == 1
    assert not output.exists()
    assert service.get(job['id'], 'owner')['artifacts_deleted']


def test_no_environment_secrets_in_subprocess(tmp_path, pdf, monkeypatch):
    from app.tenderproof import processing
    real = processing.subprocess.Popen
    seen = []
    def capture(*args, **kwargs):
        seen.append(kwargs['env'])
        return real(*args, **kwargs)
    monkeypatch.setenv('SOLARI_API_KEY', 'secret-marker')
    monkeypatch.setenv('DATABASE_URL', 'secret-marker')
    monkeypatch.setattr(processing.subprocess, 'Popen', capture)
    service = ProcessingService(tmp_path)
    job = service.enqueue('owner', pdf)
    service.execute(job['id'], 'owner')
    assert 'secret-marker' not in json.dumps(seen)
    assert 'secret-marker' not in service.db_path.read_bytes().decode(errors='ignore')


class RemoteDouble:
    hourly_usd = .086
    tariff_source = 'double; not billed'
    def __init__(self, *, failure=False, close_failure=False):
        self.failure, self.close_failure, self.created = failure, close_failure, 0
    def create(self, key, limits):
        self.created += 1
        return 'sensitive-capability'
    def process(self, resource, content, limits, cancelled):
        if self.failure:
            raise RuntimeError('secret-marker')
        return json.dumps({'input_sha256': hashlib.sha256(content).hexdigest(),
                           'extractor_version': 'tenderproof-pdf-v2', 'pages': [], 'total_pages': 0}).encode()
    def close(self, resource):
        if self.close_failure:
            raise RuntimeError('secret-marker')
        return True
    def status(self, resource):
        return 'unknown' if self.close_failure else 'gone'


@pytest.mark.parametrize('failure,close_failure', [(False, False), (True, False), (False, True)])
def test_remote_double_lifecycle(tmp_path, pdf, failure, close_failure):
    remote = RemoteDouble(failure=failure, close_failure=close_failure)
    service = ProcessingService(tmp_path, budget_usd=1, remote=remote)
    job = service.enqueue('owner', pdf, mode='solari', limits=ProcessingLimits(budget_usd=.1))
    result = service.execute(job['id'], 'owner')
    assert result['state'] == ('failed' if failure else 'succeeded')
    assert result['close_requested']
    assert result['close_confirmed'] is (not close_failure)
    assert result['confirmed_cost_usd'] is None
    assert 'secret-marker' not in json.dumps(result)
    assert 'sensitive-capability' not in json.dumps(result)
    if close_failure:
        assert service.cleanup(retention_seconds=0) == 0
        second = service.enqueue('owner', pdf, mode='solari', limits=ProcessingLimits(budget_usd=.1))
        with pytest.raises(ProcessingError, match='concurrency_limit'):
            service.execute(second['id'], 'owner')


def test_persistent_budget_reservation_concurrent(tmp_path, pdf):
    remote = RemoteDouble()
    service = ProcessingService(tmp_path, budget_usd=.002, remote=remote)
    def enqueue(_):
        try:
            return service.enqueue('owner', pdf, mode='solari', limits=ProcessingLimits(budget_usd=.1))
        except ProcessingError:
            return None
    with ThreadPoolExecutor(2) as pool:
        jobs = list(pool.map(enqueue, range(2)))
    assert sum(j is not None for j in jobs) == 1
    restarted = ProcessingService(tmp_path, budget_usd=.002, remote=remote)
    with pytest.raises(ProcessingError, match='budget_exceeded'):
        restarted.enqueue('owner', pdf, mode='solari', limits=ProcessingLimits(budget_usd=.1))
    assert remote.created == 0


def test_provider_unavailable_and_budget(tmp_path, pdf):
    service = ProcessingService(tmp_path)
    with pytest.raises(ProcessingError, match='provider_unavailable'):
        service.enqueue('owner', pdf, mode='solari')
    service.remote = RemoteDouble()
    with pytest.raises(ProcessingError, match='budget_exceeded'):
        service.enqueue('owner', pdf, mode='solari')


def test_restart_recovery_no_create(tmp_path, pdf):
    remote = RemoteDouble(close_failure=True)
    service = ProcessingService(tmp_path, budget_usd=1, remote=remote)
    job = service.enqueue('owner', pdf, mode='solari', limits=ProcessingLimits(budget_usd=.1))
    with service._db() as db:
        data = service._read(db, job['id'], 'owner')
        data.update(state='running', resource='sensitive-capability', updated_at=time.time()-1000)
        db.execute('UPDATE processing_jobs SET data=? WHERE id=?', (json.dumps(data), job['id']))
    restarted = ProcessingService(tmp_path, budget_usd=1, remote=remote)
    assert restarted.recover() == 1
    result = restarted.get(job['id'], 'owner')
    assert result['error']['code'] == 'interrupted'
    assert not result['close_confirmed']
    assert remote.created == 0
    remote.close_failure = False
    assert restarted.reconcile_close(job['id'], 'owner')['close_confirmed']


def test_periodic_local_recovery_preserves_recent_completed_and_remote_jobs(tmp_path, pdf):
    service = ProcessingService(tmp_path, budget_usd=1, remote=RemoteDouble())
    jobs = [service.enqueue('owner',pdf,mode=mode,limits=ProcessingLimits(budget_usd=.1))
            for mode in ('local','local','local','solari')]
    with service._db() as db:
        for i, job in enumerate(jobs):
            data = service._read(db,job['id'],'owner')
            data.update(state='succeeded' if i==2 else 'running',
                        updated_at=time.time()-(1000 if i!=1 else 30))
            if i==3:
                data['creation_unknown']=True
            db.execute('UPDATE processing_jobs SET data=? WHERE id=?',(json.dumps(data),job['id']))
    assert service.recover_local()==1
    assert service.get(jobs[0]['id'],'owner')['error']['code']=='interrupted'
    assert [service.get(j['id'],'owner')['state'] for j in jobs[1:]]==['running','succeeded','running']
    assert service.recover_local()==0


def test_bounded_retry(tmp_path):
    service = ProcessingService(tmp_path)
    job = service.enqueue('owner', b'%PDF-bad', limits=ProcessingLimits(max_attempts=2))
    service.execute(job['id'], 'owner')
    service.retry(job['id'], 'owner')
    service.execute(job['id'], 'owner')
    with pytest.raises(ProcessingError, match='retry_limit'):
        service.retry(job['id'], 'owner')


def test_remote_http_no_launch_without_authorization():
    calls = []
    client = httpx.Client(transport=httpx.MockTransport(lambda request: calls.append(request)))
    processor = SolariSandboxProcessor('fake-key', http=client)
    with pytest.raises(ProcessingError, match='live_authorization_required'):
        processor.create('job', ProcessingLimits())
    assert calls == []


def test_remote_http_404_not_closed_or_secret_exception():
    client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(404, json={'error':'secret-marker'})))
    processor = SolariSandboxProcessor('fake-key', http=client)
    assert processor.status('sensitive-capability') == 'unknown'
    with pytest.raises(ProcessingError, match='provider_failure'):
        processor.close('sensitive-capability')


def test_remote_http_fixed_contract_and_file_credentials(pdf):
    calls = []
    output = json.dumps({'input_sha256': hashlib.sha256(pdf).hexdigest(), 'extractor_version':'tenderproof-pdf-v2',
                         'total_pages':0, 'pages':[]}).encode()
    def handle(request):
        calls.append(request)
        path = request.url.path
        if path == '/sandboxes':
            return httpx.Response(201, json={'sandboxId':'fake-resource'})
        if path.endswith('/files/upload-url'):
            return httpx.Response(200, json={'url':'https://api.getsolari.com/files/upload?token=fake'})
        if path.endswith('/files/download-url'):
            return httpx.Response(200, json={'url':'https://api.getsolari.com/files/download?token=fake'})
        if path == '/files/download':
            return httpx.Response(200, content=output)
        return httpx.Response(200, json={'exitCode':0, 'ok':True})
    processor = SolariSandboxProcessor('fake-key', live_authorized=True, http=httpx.Client(transport=httpx.MockTransport(handle)))
    limits = ProcessingLimits()
    resource = processor.create('job-key', limits)
    assert processor.process(resource, pdf, limits, lambda:False) == output
    assert processor.close(resource)
    creation = json.loads(calls[0].content)
    assert creation['lifecycle'] == {'onTimeout':'kill', 'autoResume':False}
    assert creation['envs'] == {}
    assert calls[0].headers['Idempotency-Key'] == 'job-key'
    assert all('authorization' not in r.headers for r in calls if r.url.path.startswith('/files/'))
    command = next(json.loads(r.content) for r in calls if r.url.path.endswith('/exec'))
    assert command['cmd'] == 'python3'
    assert command['args'][0] == '-I'
    assert command['args'][1:3] == ['-S', '/tmp/tenderproof-worker.pyz']


def test_running_cancel_and_concurrent_claim(tmp_path, pdf):
    entered = threading.Event()
    class WaitingDouble(RemoteDouble):
        def process(self, resource, content, limits, cancelled):
            entered.set()
            deadline = time.monotonic() + 5
            while not cancelled() and time.monotonic() < deadline:
                time.sleep(.01)
            raise ProcessingError('cancelled')
    service = ProcessingService(tmp_path, remote=WaitingDouble(), budget_usd=1)
    job = service.enqueue('owner', pdf, mode='solari', limits=ProcessingLimits(budget_usd=.1))
    with ThreadPoolExecutor(1) as pool:
        future = pool.submit(service.execute, job['id'], 'owner')
        assert entered.wait(3)
        with pytest.raises(ProcessingError, match='job_already_claimed'):
            ProcessingService(tmp_path).execute(job['id'], 'owner')
        service.cancel(job['id'], 'owner')
        result = future.result(timeout=5)
    assert result['state'] == 'cancelled'
    assert result['close_requested'] and result['close_confirmed']


def test_processing_router_normal_jwt_owner_isolation(tmp_path, pdf, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.database import Base, get_db
    from app.models import User
    from app.auth import create_access_token
    from app.tenderproof import processing_router
    from app.tenderproof.contracts import TenderProofRun, Artifact
    from app.tenderproof.store import TenderProofStore

    engine = create_engine('sqlite://', connect_args={'check_same_thread':False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    db.add_all([User(id=61,name='one',email='one@example.test',password_hash='unused'),
                User(id=62,name='two',email='two@example.test',password_hash='unused')])
    db.commit()
    app = FastAPI()
    app.include_router(processing_router.router)
    app.dependency_overrides[get_db] = lambda: db
    service = ProcessingService(tmp_path / 'jobs')
    monkeypatch.setattr(processing_router, 'get_processing_service', lambda: service)
    monkeypatch.setenv('TENDERPROOF_ARTIFACT_DIR', str(tmp_path / 'artifacts'))
    store = TenderProofStore()
    artifact = Artifact(artifact_id='art-local-test',sha256=hashlib.sha256(pdf).hexdigest(),byte_len=len(pdf), downloaded_at=datetime.now(timezone.utc),
                        url_requested='https://official.example/test.pdf',url_final='https://official.example/test.pdf')
    store.save_artifact_file(artifact,pdf)
    store.put_run(TenderProofRun(run_id='run-local-test',owner_user_id=61,artifact=artifact))
    monkeypatch.setattr(processing_router, 'get_store', lambda:store)
    client = TestClient(app)
    headers = {'Authorization':'Bearer '+create_access_token(61)}
    other = {'Authorization':'Bearer '+create_access_token(62)}
    assert client.post('/tenderproof/processing/from-run/run-local-test').status_code == 401
    assert client.post('/tenderproof/processing/from-run/run-local-test',headers=other).status_code == 404
    created = client.post('/tenderproof/processing/from-run/run-local-test',headers=headers)
    assert created.status_code == 201, created.text
    job_id = created.json()['id']
    path = '/tenderproof/processing/' + job_id
    assert client.post(path+'/execute',headers=other).status_code == 404
    executed = client.post(path+'/execute',headers=headers)
    assert executed.json()['state'] == 'succeeded', executed.text
    assert client.get(path+'/result',headers=headers).status_code == 200
    assert client.get(path+'/result',headers=other).status_code == 404
    assert client.post('/tenderproof/processing/from-run/run-local-test',headers=other,
                       json={'operation':'ocr_pdf'}).status_code == 404
    ocr = client.post('/tenderproof/processing/from-run/run-local-test',headers=headers,
                      json={'operation':'ocr_pdf'})
    assert ocr.status_code == 201
    assert ocr.json()['operation'] == 'ocr_pdf'
    assert ocr.json()['extractor_version'] == 'tenderproof-ocr-v1'
    assert ocr.json()['limits']['budget_usd'] == 0
    assert client.post('/tenderproof/processing/from-run/run-local-test',headers=headers,
                       json={'operation':'ocr_pdf','command':'untrusted'}).status_code == 422
    db.close()
    engine.dispose()


def test_bundled_worker_runs_without_site_packages(tmp_path, pdf):
    import subprocess
    import sys
    import zipfile
    import io
    from app.tenderproof.processing_bundle import build_processing_bundle
    payload, manifest = build_processing_bundle()
    assert build_processing_bundle()[0] == payload
    assert hashlib.sha256(payload).hexdigest() == manifest['bundle_sha256']
    archive = zipfile.ZipFile(io.BytesIO(payload))
    assert all(name == '__main__.py' or name == 'pypdf-LICENSE' or
               (name.startswith('pypdf/') and name.endswith('.py')) for name in archive.namelist())
    assert not any('.env' in name or '.pyc' in name or 'site-packages' in name for name in archive.namelist())
    app = tmp_path / 'worker.pyz'
    app.write_bytes(payload)
    source, output = tmp_path/'input.pdf', tmp_path/'output.json'
    source.write_bytes(pdf)
    # -S proves imports work without installed site packages; -I excludes environment/cwd injection.
    result = subprocess.run([sys.executable, '-I', '-S', str(app), str(source), str(output), '1', '100000'],
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=10, cwd=tmp_path)
    assert result.returncode == 0, result.stderr.decode(errors='replace')
    parsed = json.loads(output.read_bytes())
    assert parsed['total_pages'] == 1
    assert 'TenderProof fixture text' in parsed['pages'][0]['text']
    assert parsed['input_sha256'] == hashlib.sha256(pdf).hexdigest()


def test_bundle_pin_refuses_unreviewed_dependency(monkeypatch):
    from app.tenderproof import processing_bundle
    monkeypatch.setattr(processing_bundle.importlib.metadata, 'version', lambda _: '0.0.0')
    with pytest.raises(ProcessingError, match='dependency_bundle_version_mismatch'):
        processing_bundle.build_processing_bundle()


def test_exact_live_fixture_preflight_and_bundled_extraction(tmp_path):
    import subprocess
    import sys
    from io import BytesIO
    from pypdf import PdfReader
    from scripts.tenderproof_sandbox_live_check import prepare_single_page_fixture
    from app.tenderproof.processing_bundle import build_processing_bundle
    pdf = prepare_single_page_fixture()
    assert len(PdfReader(BytesIO(pdf)).pages) == 1
    app, source, output = tmp_path/'worker.pyz', tmp_path/'input.pdf', tmp_path/'output.json'
    app.write_bytes(build_processing_bundle()[0])
    source.write_bytes(pdf)
    finished = subprocess.run([sys.executable,'-I','-S',str(app),str(source),str(output),'1','100000'],
                              stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                              timeout=10,cwd=tmp_path)
    assert finished.returncode == 0
    data = json.loads(output.read_bytes())
    assert data['total_pages'] == 1
    assert data['input_sha256'] == hashlib.sha256(pdf).hexdigest()
    assert 'TenderProof authorized synthetic sandbox check.' in data['pages'][0]['text']


def test_live_preflight_wrong_page_count_never_constructs_remote(tmp_path, monkeypatch):
    import sys
    import dotenv
    from scripts import tenderproof_sandbox_live_check as live
    from app.tenderproof import demo_pdf, processing_solari
    two_pages = make_text_pdf(['first page','second page'])
    monkeypatch.setattr(live, 'BACKEND', tmp_path)
    monkeypatch.setattr(sys, 'argv', ['live-check','zipapp-v2'])
    monkeypatch.setattr(dotenv, 'dotenv_values', lambda _: {'SOLARI_API_KEY':'fake'})
    monkeypatch.setattr(demo_pdf, 'make_text_pdf', lambda _: two_pages)
    calls = []
    class RefuseRemote:
        def __init__(self,*args,**kwargs):
            calls.append('constructed')
            raise AssertionError('remote must not be constructed')
    monkeypatch.setattr(processing_solari, 'SolariSandboxProcessor', RefuseRemote)
    with pytest.raises(ValueError, match='fixture_must_have_exactly_one_page'):
        live.main()
    assert calls == []
    assert not list(tmp_path.rglob('authorization-consumed.json'))
