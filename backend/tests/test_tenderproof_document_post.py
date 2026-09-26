"""POST export is explicit, bounded, fenced and separately identified."""
import json
from dataclasses import replace
from pathlib import Path
import httpx
import pytest
from pydantic import ValidationError
from app.tenderproof.contracts import DocumentAcquisitionRequest,DocumentCandidate
from app.tenderproof.batch99_regions_adapters import FapegSelectionAdapter
from app.tenderproof.http_driver import BoundedHTTPDriver
from app.tenderproof.security import TenderProofSettings,TenderProofLimits,DestinationBlocked
from app.tenderproof.acquisition import AcquisitionService
from app.tenderproof.document_identity import document_manifest,document_identity
from app.tenderproof.source_adapters import SOURCE_ADAPTERS

FIX=Path(__file__).parent/'fixtures/tenderproof_batch99_regions'

@pytest.fixture
def observed(monkeypatch):
    a=FapegSelectionAdapter()
    monkeypatch.setitem(SOURCE_ADAPTERS,a.source,a)
    def read(name):
        row=next(r for r in json.loads((FIX/name).read_text(encoding='utf-8'))['pages'] if r['source']==a.source)
        return row['url'],(FIX/row['file']).read_text(encoding=row['encoding'])
    url,listing=read('categories-manifest.json')
    c=a.parse_listing(listing,url).candidates[0]
    _,html=read('selection-manifest.json')
    d=a.choose_document(a.documents(html,c))
    return a,c,d,html

@pytest.mark.parametrize('kwargs',[{'method':'GET','body':'177,0'},{'body':'177,01'},{'body':'1&secret=2'},{'body':'177,0','content_type':'application/json'},{'body':'177,0','headers':{'Authorization':'x'}}])
def test_request_model_rejects_unobserved_shape(kwargs):
    with pytest.raises(ValidationError):DocumentAcquisitionRequest(**kwargs)

def test_post_exact_transport_and_raw_bytes(observed,monkeypatch):
    a,c,d,_=observed
    calls=[]
    def handler(request):
        calls.append(request)
        return httpx.Response(200,content=b'%PDF-1.7\nraw',headers={'Content-Type':'application/pdf'})
    monkeypatch.setattr('app.tenderproof.http_driver._public_dns',lambda host:None)
    client=httpx.Client(transport=httpx.MockTransport(handler))
    driver=BoundedHTTPDriver(a.source,TenderProofSettings(allowlist_hosts=a.allowed_hosts),client=client)
    driver.candidate=c
    result=driver.download_document(d,c,max_bytes=100)
    assert result.content==b'%PDF-1.7\nraw'
    assert calls[0].method=='POST' and calls[0].content==b'177,0'
    assert calls[0].headers['Content-Type']=='application/x-www-form-urlencoded'
    assert driver.requests==1
    driver.close();assert client.is_closed

@pytest.mark.parametrize('failure',['private','body','limit','redirect'])
def test_post_guard_before_access_and_no_redirect_follow(observed,monkeypatch,failure):
    a,c,d,_=observed
    d=d.model_copy(deep=True);calls=[]
    monkeypatch.setattr('app.tenderproof.http_driver._public_dns',lambda host:None)
    client=httpx.Client(transport=httpx.MockTransport(lambda request:(calls.append(request) or httpx.Response(302,headers={'Location':'http://127.0.0.1/private'}))))
    driver=BoundedHTTPDriver(a.source,TenderProofSettings(allowlist_hosts=a.allowed_hosts,limits=TenderProofLimits(max_navigations=1)),client=client);driver.candidate=c
    if failure=='private':d.url_requested='http://127.0.0.1/exportarEditalPdf'
    if failure=='body':d.acquisition_request.body='181,0'
    if failure=='limit':driver.requests=1
    with pytest.raises((ValueError,DestinationBlocked)):driver.download_document(d,c,max_bytes=100)
    assert len(calls)==(1 if failure=='redirect' else 0)
    driver.close()

def test_post_cannot_fallback_to_legacy_get(observed):
    a,c,d,html=observed
    class GetOnly:
        def open_detail(self,url):return html
        def download(self,*args,**kwargs):raise AssertionError('GET must never run')
    with pytest.raises(ValueError,match='POST'):
        AcquisitionService(TenderProofSettings(allowlist_hosts=a.allowed_hosts,limits=TenderProofLimits(max_documents=100))).select_and_fetch(GetOnly(),candidate=c)


def test_new_observed_versions_and_phase_exports_are_bound_to_manifest(observed):
    a,c,_,html=observed
    changed=html.replace('data-id="195"','data-id="987"')
    docs=a.documents(changed,c)
    assert any(d.acquisition_request.body=='987,0' for d in docs)
    result=next(d for d in docs if d.acquisition_request.body=='59,59')
    assert result.kind=='resultado'
    assert result.url_requested.endswith('/exportarResultadoCertamePdf')
    a.validate_document_request(result,c)
    for body in ('60,59','59,777','59,0'):
        forged=result.model_copy(deep=True);forged.acquisition_request.body=body
        with pytest.raises(ValueError):a.validate_document_request(forged,c)
    with pytest.raises(ValueError):FapegSelectionAdapter().validate_document_request(result,c)


def test_wrong_contest_or_unknown_button_does_not_silently_drop_documents(observed):
    a,c,_,html=observed
    for changed in (html.replace('value="59"','value="60"'),html.replace('exportArquivoFaseDinamica','exportUnknownDocument')):
        with pytest.raises(ValueError):a.documents(changed,c)


def test_future_personnel_selection_is_discovered_and_exports_use_its_id(observed):
    a,old,_,html=observed
    url=old.detail_url_observed.replace('0092024','0132028').replace('|59','|731').replace('%7C59','%7C731')
    title='Processo Seletivo Simplificado - EDITAL Nº 013/2028–SEAD/FAPEG'
    page=a.parse_listing(f'<a href="{url}">{title}</a>',a.listing_urls[0])
    assert len(page.candidates)==1
    candidate=page.candidates[0]
    assert candidate.external_id=='013/2028' and candidate.candidate_id.endswith('-731')
    changed=html.replace('009/2024','013/2028').replace('value="59"','value="731"')
    a.confirm_identity(candidate,changed,url)
    docs=a.documents(changed,candidate)
    assert a.choose_document(docs).title=='Edital 013/2028 SEAD/FAPEG'
    result=next(d for d in docs if d.url_requested.endswith('/exportarResultadoCertamePdf'))
    assert result.acquisition_request.body.startswith('731,')
    with pytest.raises(ValueError):a.documents(html,candidate)
    with pytest.raises(ValueError):a.validate_document_request(result,old)

def test_post_body_retained_in_run_manifest_and_identity(observed):
    a,c,d,_=observed
    serialized=d.model_dump_json()
    copy=DocumentCandidate.model_validate_json(serialized)
    assert copy.acquisition_request.body=='177,0'
    first=document_manifest(copy)
    copy.acquisition_request.body='181,0'
    second=document_manifest(copy)
    assert first['url']==second['url']
    assert document_identity(first)[:4]!=document_identity(second)[:4]
    legacy=DocumentCandidate(doc_id='get',title='Edital',url_requested='https://x.test/a.pdf')
    assert document_manifest(legacy)=={'title':'Edital','url':'https://x.test/a.pdf','kind':'outro'}


from test_tenderproof_publication import env
from test_tenderproof_document_review_gate import checkpoint

def test_changed_post_body_holds_review_durably_even_same_url_title(env):
    from app.tenderproof.continuous_store import ContinuousStore
    first={'title':'Edital FAPEG','url':'https://selecao.go.gov.br/exportarEditalPdf','kind':'edital','acquisition_request':DocumentAcquisitionRequest(body='177,0').model_dump()}
    queue,_=checkpoint(env,[first],100)
    second={**first,'acquisition_request':DocumentAcquisitionRequest(body='181,0').model_dump()}
    queue,_=checkpoint(env,[second],4000)
    review=ContinuousStore(queue.path).review_for_run(env[4])
    assert review['pending'] and review['documents']==[second]
    checkpoint(env,[first],8000)
    later=ContinuousStore(queue.path).review_for_run(env[4])
    assert later['pending'] and second in later['documents'] and later['detected_at']==review['detected_at']

def test_checkpoint_post_checks_lease_before_driver(observed,monkeypatch):
    from types import SimpleNamespace
    from app.tenderproof.continuous import CheckpointDriver
    from app.tenderproof.continuous_store import LeaseLost
    a,c,d,_=observed
    def lost(*args):raise LeaseLost('expired fence')
    engine=SimpleNamespace(queue=SimpleNamespace(check_lease=lost))
    lease=SimpleNamespace(source=a.source)
    class Driver:
        def download_document(self,*args,**kwargs):pytest.fail('network after lost lease')
    wrapper=CheckpointDriver(Driver(),engine,lease)
    with pytest.raises(LeaseLost):wrapper.download_document(d,c,max_bytes=10)


def test_completed_official_post_run_recovers_without_repost(env,observed,monkeypatch):
    import hashlib
    import sqlite3
    from app.tenderproof.continuous import ContinuousEngine
    from app.tenderproof.continuous_store import ContinuousStore,SourcePolicy
    from app.tenderproof.solari_adapter import DownloadedBytes
    from app.tenderproof.contracts import ExecutionStatus
    a,c,d,detail_html=observed
    listing_row=next(r for r in json.loads((FIX/'categories-manifest.json').read_text(encoding='utf-8'))['pages'] if r['source']==a.source)
    listing_html=(FIX/listing_row['file']).read_text(encoding=listing_row['encoding'])
    pdfrow=json.loads((FIX/'pdf-retry-manifest.json').read_text(encoding='utf-8'))['documents'][0]
    raw=(FIX/pdfrow['file']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==pdfrow['sha256']
    calls=[];drivers=[]
    class OfflinePost:
        session_id=None
        replay_available=False
        def __init__(self):self.closed=False;drivers.append(self)
        def open_listing(self,url):assert url==listing_row['url'];return listing_html
        def open_detail(self,url):assert url==c.detail_url_observed;return detail_html
        def download(self,*args,**kwargs):pytest.fail('POST cannot downgrade to GET')
        def download_document(self,document,candidate,*,max_bytes):
            a.validate_document_request(document,candidate)
            assert document.acquisition_request.body==pdfrow['body'] and len(raw)<=max_bytes
            calls.append(document.acquisition_request.body)
            return DownloadedBytes(url_requested=document.url_requested,url_final=document.url_requested,content=raw,content_type='application/pdf')
        def observed_json(self):return []
        def session_records(self):return []
        def replay_url(self):return None
        def diagnostics(self):return ['offline exact official POST response']
        def close(self):self.closed=True
    monkeypatch.setenv('TENDERPROOF_CONTINUOUS_ENABLED','true')
    monkeypatch.setenv('TENDERPROOF_CONTINUOUS_OPERATOR_USER_IDS','1')
    monkeypatch.setenv('TENDERPROOF_PROCESSING_MODE','local')
    queue=ContinuousStore()
    queue.configure(1,a.source,SourcePolicy(enabled=True,mode='real',max_candidates=1,max_listing_pages=1,max_attempts=2,max_pdf_pages=60,min_request_gap_s=0))
    engine=ContinuousEngine(queue=queue,run_store=env[5],driver_factory=lambda *args,**kwargs:OfflinePost())
    cycle=engine.enqueue(1,a.source,force=True)
    assert engine.process_job(queue.ready_jobs()[0])['status']=='succeeded'
    job=queue.ready_jobs()[0]
    original=queue.complete_detail
    def crash(*args,**kwargs):raise OSError('controlled queue commit crash')
    monkeypatch.setattr(queue,'complete_detail',crash)
    engine.process_job(job)
    item=next(j for j in queue.cycle(cycle,1)['jobs'] if j['job_id']==job)
    run=env[5].get_run(item['run_id'])
    assert run.execution_status==ExecutionStatus.COMPLETED,run.error
    assert run.validation_status.value=='valid'
    assert run.document.acquisition_request.body=='177,0' and run.artifact.sha256==pdfrow['sha256']
    assert calls==['177,0'] and all(driver.closed for driver in drivers)
    monkeypatch.setattr(queue,'complete_detail',original)
    engine.driver_factory=lambda *args,**kwargs:pytest.fail('committed POST must recover without new driver/request')
    with sqlite3.connect(queue.path) as db:db.execute('UPDATE jobs SET available_at=0 WHERE job_id=?',(job,))
    result=engine.process_job(job)
    assert result['recovered'] and calls==['177,0']
    observation=queue.observations(1)[0]
    assert observation['summary']['selected_document']['acquisition_request']['body']=='177,0'
