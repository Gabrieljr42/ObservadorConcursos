"""Real HTML captures + explicitly synthetic perturbations and recovery scenarios."""
import hashlib
import json
import sqlite3
from pathlib import Path

import pytest
from bs4 import UnicodeDammit

from app.tenderproof.source_adapters import get_source_adapter, SourcePageBlocked
from app.tenderproof.pilot_adapters import PILOT_ADAPTERS, document_kind
from app.tenderproof.continuous_store import ContinuousStore, SourcePolicy, LeaseLost

ROOT=Path(__file__).parent/'fixtures'/'tenderproof_pilot'
MANIFEST=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
IDS=[a.source for a in PILOT_ADAPTERS]
COUNTS={'access_open':3,'abcp_open':5,'avancasp_open':9,'ibade_open':104,'fenix_open':128,'legalle_open':144,'fgv_open':33,'funcern_selection':2}


def captured(source,kind='listing'):
    row=next(r for r in MANIFEST['pages'] if r['source']==source and r['kind']==kind)
    data=(ROOT/row['file']).read_bytes()
    assert hashlib.sha256(data).hexdigest()==row['sha256']
    return row,UnicodeDammit(data,is_html=True).unicode_markup


def sample(source):
    a=get_source_adapter(source); row,html=captured(source)
    page=a.parse_listing(html,row['url'],1000)
    detail_row,detail=captured(source,'detail')
    candidate=next(c for c in page.candidates if c.detail_url_observed==detail_row['url'])
    return a,page,candidate,detail_row,detail


@pytest.mark.parametrize('source',IDS)
def test_official_capture_discovery_identity_documents_and_partial_coverage(source):
    a,page,candidate,row,html=sample(source)
    assert len(page.candidates)==COUNTS[source]
    assert len({c.external_id for c in page.candidates})==len(page.candidates)
    assert not page.empty_evidence and not page.terminal_evidence
    a.confirm_identity(candidate,html,row['url'])
    docs=a.documents(html,candidate)
    assert docs
    for doc in docs:a.validate_document_url(doc.url_requested,candidate)
    if source in ('access_open','fgv_open','funcern_selection'):
        with pytest.raises(ValueError):a.choose_document(docs)
    else:
        assert a.choose_document(docs).kind=='edital'


@pytest.mark.parametrize('source',IDS)
def test_candidate_limit_cannot_claim_full_coverage(source):
    a=get_source_adapter(source);row,html=captured(source)
    page=a.parse_listing(html,row['url'],1)
    assert len(page.candidates)==1 and page.truncated and not page.terminal_evidence
    assert any('parcial' in d for d in page.diagnostics)


@pytest.mark.parametrize('source',IDS)
def test_unknown_empty_shell_and_hidden_content_do_not_erase_known(source):
    a=get_source_adapter(source)
    _,html=captured(source)
    for body in ('<main></main>','<main><p>Nenhum concurso encontrado.</p></main>',f'<div hidden>{str(__import__("bs4").BeautifulSoup(html,"lxml").body)}</div>'):
        page=a.parse_listing(body,a.listing_urls[0])
        assert not page.candidates and not page.empty_evidence and not page.terminal_evidence
        assert any('preservar' in d for d in page.diagnostics)


@pytest.mark.parametrize('source',IDS)
def test_blocking_challenge_is_failure(source):
    a=get_source_adapter(source)
    for text in ('Just a moment','Access denied','Verifique que você é humano'):
        with pytest.raises(SourcePageBlocked):a.parse_listing(f'<main>{text}</main>',a.listing_urls[0])


@pytest.mark.parametrize('source',IDS)
def test_candidate_detail_mismatch_and_foreign_destinations(source):
    a,page,candidate,row,html=sample(source)
    other=next(c for c in page.candidates if c.external_id!=candidate.external_id)
    with pytest.raises(ValueError):a.confirm_identity(candidate,html,other.detail_url_observed)
    with pytest.raises(ValueError):a.confirm_identity(candidate.model_copy(update={'external_id':'unrelated'}),html,row['url'])
    for bad in ('https://127.0.0.1/a.pdf','https://metadata.google.internal/a.pdf','https://evil.test/a.pdf'):
        with pytest.raises(Exception):a.validate_document_url(bad,candidate)


@pytest.mark.parametrize('source',IDS)
def test_wrong_and_ambiguous_principal_documents(source):
    a,_,candidate,_,html=sample(source)
    docs=a.documents(html,candidate)
    first=docs[0].model_copy(update={'kind':'edital','title':'Edital de abertura'})
    second=first.model_copy(update={'doc_id':'controlled-second','url_requested':first.url_requested+'?controlled=1'})
    with pytest.raises(ValueError,match='ambíguos'):a.choose_document([first,second])
    for title in ('Resultado final do edital','Gabarito do edital','Anexo I do edital','Edital de convocação','Edital retificado','Edital - política de privacidade','Edital - Manual do candidato','Edital de classificação provisória','Edital cumprimento de decisão liminar'):
        assert document_kind(title,first.url_requested)!='edital'


@pytest.mark.parametrize('source',IDS[:6])
def test_foreign_document_identifier_is_rejected(source):
    a,_,candidate,_,html=sample(source)
    doc=a.documents(html,candidate)[0]
    wrong=doc.url_requested.replace('/'+candidate.external_id+'/', '/999999999/')
    with pytest.raises(ValueError,match='outro concurso'):a.validate_document_url(wrong,candidate)


@pytest.mark.parametrize('source',('access_open','abcp_open','avancasp_open'))
def test_shared_document_host_does_not_authorize_another_tenant(source):
    a,_,candidate,_,html=sample(source)
    url=a.documents(html,candidate)[0].url_requested.replace('/uploads/'+a.tenant+'/', '/uploads/999999/')
    with pytest.raises(ValueError,match='tenant'):a.validate_document_url(url,candidate)


@pytest.mark.parametrize('source',('fgv_open','funcern_selection'))
def test_observed_pagination_is_traversable_and_unobserved_params_refused(source):
    a=get_source_adapter(source);row,html=captured(source)
    page=a.parse_listing(html,row['url'],1000)
    second,html2=captured(source,'page2')
    assert second['url'] in page.next_urls
    assert a.parse_listing(html2,second['url'],1000).candidates
    with pytest.raises(ValueError):a.validate_listing_url(row['url']+'?secret_filter=1')
    with pytest.raises(ValueError):a.validate_listing_url(row['url']+'?page=1&page=2')


def test_funcern_observed_localhost_canonical_is_never_a_destination():
    a,_,c,row,html=sample('funcern_selection')
    assert 'http://localhost/concursos/' in html
    a.confirm_identity(c,html,row['url'])
    with pytest.raises(Exception):a.validate_detail_url('http://localhost/concursos/concurso-equador-2026/')
    with pytest.raises(ValueError):a.confirm_identity(c,html.replace('http://localhost/concursos/','https://evil.test/concursos/'),row['url'])


def test_institutional_filter_excludes_admission_and_scholarships():
    a=get_source_adapter('funcern_selection'); row,html=captured(a.source)
    page=a.parse_listing(html,row['url'],1000)
    assert all('concurso' in c.title_observed.lower() for c in page.candidates)
    for title in ('Processo Seletivo Simplificado Bolsa de Pesquisa','Concurso Público Bolsistas','IFRN Integrado 2027','Vestibular 2026','PROITEC IFRN 2026'):
        assert not a.in_scope(title,'https://funcern.br/concursos/test/')


@pytest.mark.parametrize('source',IDS)
def test_controlled_crash_resume_repeat_cycles_deduplicate_and_preserve(source,tmp_path):
    """Real listing parsed; detail result and worker clock intentionally synthetic."""
    a=get_source_adapter(source);row,html=captured(source)
    queue=ContinuousStore(tmp_path/'queue.sqlite3')
    queue.configure(1,source,SourcePolicy(enabled=True,mode='real',interval_s=60,min_request_gap_s=0,max_candidates=1,max_listing_pages=1,max_attempts=2,job_timeout_s=10),now=1000)
    for cycle_time in (1000,1300):
        cycle=queue.enqueue(1,source,[row['url']],now=cycle_time)
        jobs=queue.cycle(cycle,1)['jobs']
        listing_id=next(j['job_id'] for j in jobs if j['kind']=='listing')
        first=queue.claim(listing_id,now=cycle_time)
        restarted=ContinuousStore(queue.path)
        second=restarted.claim(listing_id,now=first.lease_until+1)
        with pytest.raises(LeaseLost):queue.complete_listing(first,html,a.parse_listing(html,row['url'],1),now=first.lease_until+2)
        now=first.lease_until+2
        restarted.complete_listing(second,html,a.parse_listing(html,row['url'],1),now=now)
        detail_id=next(j['job_id'] for j in queue.cycle(cycle,1)['jobs'] if j['kind']=='detail')
        detail=restarted.claim(detail_id,now=now+1)
        restarted.detail_checkpoint(detail,'controlled detail',[],now=now+2)
        restarted.complete_detail(detail,'controlled-run','same-semantic-hash',{'validation_status':'valid'},now=now+3)
        assert restarted.claim(detail_id,now=now+4) is None
        assert queue.cycle(cycle,1)['status']=='partial'
    assert len(queue.observations(1))==1
    with sqlite3.connect(queue.path) as db:
        assert db.execute('SELECT COUNT(*) FROM known_candidates').fetchone()[0]==1
        assert db.execute('SELECT last_valid_run_id FROM known_candidates').fetchone()[0]=='controlled-run'



@pytest.mark.parametrize('source',IDS)
def test_title_mismatch_requires_review_even_with_same_portal_id(source):
    a,_,c,row,html=sample(source)
    changed=c.model_copy(update={'title_observed':'Prefeitura Municipal de Incompatibilissima'})
    with pytest.raises(ValueError,match='título'):a.confirm_identity(changed,html,row['url'])


def test_observed_ibade_redirect_stays_in_exact_bucket_contest_and_query_contract():
    a,_,c,_,_=sample('ibade_open')
    url='https://s3.sa-east-1.amazonaws.com/cdn-ibade.selecao.site/edital/1/127/ba13c6a0dbe47510fa87cdc9cabb0f81.pdf'
    a.validate_document_url(url+'?X-Amz-Signature=CONTROLLED',c)
    for bad in (url.replace('/127/','/128/'),url.replace('/cdn-ibade.selecao.site/','/other-tenant/'),url+'?file=other',url+'?X-Amz-Date=1&X-Amz-Date=2'):
        with pytest.raises(ValueError):a.validate_document_url(bad,c)


def test_observed_funcern_redirect_cannot_download_another_contest():
    a=get_source_adapter('funcern_selection')
    c=a.candidate_from_url('https://funcern.br/concursos/concurso-lagoa-de-pedras-2026/')
    url='https://nyc3.digitaloceanspaces.com/repo/funcern.br/media/documents/Edital_LagoadePedrasRN_4_49lUN1f.pdf'
    a.validate_document_url(url,c)
    for bad in (url.replace('LagoadePedras','Equador'),url.replace('/repo/funcern.br/','/repo/other/'),url.replace('/documents/','/documents/%2e%2e/')):
        with pytest.raises(ValueError):a.validate_document_url(bad,c)
