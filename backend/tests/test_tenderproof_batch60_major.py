"""Dated official captures; all adverse mutations below are controlled fixtures."""
from pathlib import Path
import json
import hashlib
import pytest
from app.tenderproof.batch60_major_adapters import BATCH60_MAJOR_ADAPTERS
from app.tenderproof.contracts import DocumentCandidate
from app.tenderproof.security import DestinationBlocked

ROOT=Path(__file__).parent/'fixtures/tenderproof_batch60_major'
ADAPTERS={a.source:a for a in BATCH60_MAJOR_ADAPTERS}
SAMPLES={'ibam_open':('ibam.html','375','ibam.html'),'fcc_open':('fcc.html','abgfg126','fcc-abgf.html'),
 'avalia_open':('avalia.html','631','avalia631.html'),'cebraspe_open':('cebraspe-api.json','ADEAL_26','cebraspe-adeal.json'),
 'cesgranrio_open':('cesgranrio-list-api.json','27','cesgranrio-docs27.json')}

def sample(source):
    a=ADAPTERS[source];listing,key,detail=SAMPLES[source]
    html=(ROOT/listing).read_text(encoding='utf-8')
    page=a.parse_listing(html,a.listing_urls[0],2000)
    return a,page,next(c for c in page.candidates if c.external_id==key),(ROOT/detail).read_text(encoding='utf-8')


@pytest.mark.parametrize('source',SAMPLES)
def test_observed_listing_identity_and_bounded_scope(source):
    a,page,c,detail=sample(source)
    a.confirm_identity(c,detail,c.detail_url_observed)
    assert page.candidates and not page.terminal_evidence
    listing=(ROOT/SAMPLES[source][0]).read_text(encoding='utf-8')
    limited=a.parse_listing(listing,a.listing_urls[0],1)
    assert limited.truncated and len(limited.candidates)==1
    assert not any('vestibular' in (x.title_observed or '').lower() for x in page.candidates)


@pytest.mark.parametrize('source',SAMPLES)
def test_synthetic_wrong_identity_private_destination_and_challenge(source):
    a,_,c,html=sample(source)
    with pytest.raises(ValueError):a.confirm_identity(c.model_copy(update={'external_id':'wrong'}),html,c.detail_url_observed)
    if source!='cesgranrio_open':
        with pytest.raises(ValueError):a.confirm_identity(c.model_copy(update={'title_observed':'Completely Different Organization Atlantis'}),html,c.detail_url_observed)
    with pytest.raises(ValueError):a.parse_listing('<main>Verify you are human</main>',a.listing_urls[0])
    with pytest.raises((ValueError,DestinationBlocked)):a.validate_document_url('https://127.0.0.1/private.pdf',c)
    with pytest.raises(ValueError):a.validate_detail_url(c.detail_url_observed.replace('https://','http://'))


@pytest.mark.parametrize('source',SAMPLES)
def test_synthetic_no_unsubstantiated_empty_or_arbitrary_principal(source):
    a=ADAPTERS[source]
    if source in ('cebraspe_open','cesgranrio_open'):
        with pytest.raises(ValueError):a.parse_listing('{}',a.listing_urls[0])
        if source=='cebraspe_open':assert a.parse_listing('[]',a.listing_urls[0]).empty_evidence
    else:
        assert not a.parse_listing('<main>Loading</main>',a.listing_urls[0]).empty_evidence
    docs=[DocumentCandidate(doc_id=str(i),title='Edital de abertura',url_requested=f'https://example.test/{i}.pdf',kind='edital') for i in (1,2)]
    with pytest.raises(ValueError):a.choose_document(docs)


@pytest.mark.parametrize('source',['ibam_open','fcc_open','avalia_open','cebraspe_open'])
def test_observed_original_and_document_destinations(source):
    a,_,c,html=sample(source);docs=a.documents(html,c);selected=a.choose_document(docs)
    assert selected.kind=='edital' and 'abertura' in selected.title.lower()
    for doc in docs:a.validate_document_url(doc.url_requested,c)
    with pytest.raises(ValueError):a.validate_document_url(selected.url_requested.replace('.pdf','.pdf/../other.pdf'),c)


def test_ibam_single_page_sections_do_not_mix_documents():
    a,page,c,html=sample('ibam_open')
    other=next(x for x in page.candidates if x.external_id=='376')
    first={d.url_requested for d in a.documents(html,c)}
    assert first.isdisjoint({d.url_requested for d in a.documents(html,other)})
    with pytest.raises(ValueError):a.confirm_identity(c,html,other.detail_url_observed)
    assert '#docs-375' in c.detail_url_observed
    with pytest.raises(ValueError):a.documents(html.replace('id="docs-375"','id="docs-999"'),c)


def test_ibam_synthetic_large_body_and_duplicate_card_are_not_complete():
    from bs4 import BeautifulSoup
    a,_,c,html=sample('ibam_open')
    with pytest.raises(ValueError,match='limite'):a.parse_listing('x'*(2*1024*1024+1),a.listing_urls[0])
    card=BeautifulSoup(html,'html.parser').select_one('#docs-375').find_parent(class_='card')
    mutated=BeautifulSoup(html,'html.parser');mutated.body.append(card)
    page=a.parse_listing(str(mutated),a.listing_urls[0])
    assert page.truncated and '375' in page.diagnostics[0]
    assert '375' not in {c.external_id for c in page.candidates}
    with pytest.raises(ValueError):a.confirm_identity(c,str(mutated),c.detail_url_observed)


def test_fcc_wrapper_does_not_authorize_other_contest_and_scope_excludes_admissions():
    a,page,c,html=sample('fcc_open');doc=a.choose_document(a.documents(html,c))
    with pytest.raises(ValueError):a.validate_document_url(doc.url_requested.replace('/abgfg126/','/cpupe125/'),c)
    assert all(x.external_id not in ('unasp126','fdsbc126') for x in page.candidates)
    assert not any('prorroga' in d.title.lower() for d in a.documents(html,c) if d.kind=='edital')


def test_cebraspe_observed_duplicate_route_is_excluded_not_fused():
    a,page,c,html=sample('cebraspe_open')
    assert 'INSS_22' not in {x.external_id for x in page.candidates}
    assert page.truncated and 'INSS_22' in page.diagnostics[0]
    doc=a.choose_document(a.documents(html,c))
    with pytest.raises(ValueError):a.validate_document_url(doc.url_requested.replace('/ADEAL_26/','/INSS_22/'),c)
    data=json.loads(html);data['eventoURL']='INSS_22'
    with pytest.raises(ValueError):a.documents(json.dumps(data),c)


def test_cebraspe_short_acronym_title_is_compared_in_full():
    a=ADAPTERS['cebraspe_open']
    row={'eventoURL':'XYZ_29','eventoTipo':'concursos','eventoNomeAbreviado':'XYZ AL 29'}
    c=a.candidate_from_url(a.api+'/XYZ_29','XYZ AL 29')
    a.confirm_identity(c,json.dumps(row),c.detail_url_observed)
    for field,value in [('eventoURL','XYZ_28'),('eventoTipo','vestibulares'),
                        ('eventoNomeAbreviado','XYZ SP 29'),('eventoNomeAbreviado','XYZ AL 28'),
                        ('eventoNomeAbreviado',''),('eventoNomeAbreviado',None)]:
        with pytest.raises(ValueError):
            a.confirm_identity(c,json.dumps({**row,field:value}),c.detail_url_observed)
    with pytest.raises(ValueError):
        a.confirm_identity(c,json.dumps(row),a.api+'/XYZ_28')


def test_cebraspe_exam_locations_are_not_an_opening_notice():
    a=ADAPTERS['cebraspe_open']
    titles=['Edital nº 1 - Abertura','Edital nº 5 - Locais de aplicação das provas objetivas',
            'Edital nº 2 - Retificação do edital de abertura','Edital nº 3 - Prorrogação das inscrições']
    row={'eventoURL':'XYZ_29','eventoTipo':'concursos','eventoNomeAbreviado':'XYZ AL 29',
         'arquivosEdital':[{'tipoExtensaoArquivo':'_.pdf','isGuid':False,'nomeArquivo':f'{i}.pdf',
                            'descricaoArquivo':title} for i,title in enumerate(titles)]}
    c=a.candidate_from_url(a.api+'/XYZ_29','XYZ AL 29')
    docs=a.documents(json.dumps(row),c)
    assert [d.kind for d in docs]==['edital','outro','retificacao','prorrogacao']
    assert a.choose_document(docs).title==titles[0]


def test_cesgranrio_ethics_pdf_never_substitutes_notice():
    a,_,c,html=sample('cesgranrio_open')
    doc=a.choose_document(a.documents(html,c))
    assert doc.title=='EDITAL Nº 01/2026'
    with pytest.raises((ValueError,DestinationBlocked)):a.validate_document_url('https://www.cesgranrio.org.br/wp-content/uploads/2026/01/Codigo-de-Etica-e-Conduta-V3.pdf',c)
    with pytest.raises(ValueError):a.validate_document_url(doc.url_requested.replace('/eventos/27/','/eventos/22/'),c)
    with pytest.raises(ValueError):a.documents(html.replace('/eventos/27/','/eventos/22/'),c)


def test_cesgranrio_api_pagination_and_scope_are_structural():
    a=ADAPTERS['cesgranrio_open'];data=json.loads((ROOT/'cesgranrio-list-api.json').read_text(encoding='utf-8'))
    assert 'page=2' in a.parse_listing(json.dumps(data),a.listing_urls[0]).next_urls[0]
    data['data']['items'][0]['descricao']='Vestibular para ingresso de estudantes'
    assert '27' not in {c.external_id for c in a.parse_listing(json.dumps(data),a.listing_urls[0]).candidates}
    data['data']['totalCount']+=1
    data['data']['items']=[]
    with pytest.raises(ValueError):a.parse_listing(json.dumps(data),a.listing_urls[0])


def test_cesgranrio_signed_read_urls_keep_document_id_and_reject_extra_permissions():
    a,_,c,html=sample('cesgranrio_open')
    original=a.choose_document(a.documents(html,c))
    query='?sv=2025-01-05&se=2036-09-05T14%3A15%3A46Z&sr=c&sp=r&sig=controlled'
    signed_html=html.replace(original.url_requested,original.url_requested+query)
    signed=a.choose_document(a.documents(signed_html,c))
    assert signed.doc_id==original.doc_id
    with pytest.raises(ValueError):a.validate_document_url(signed.url_requested.replace('sp=r','sp=rw'),c)
    with pytest.raises(ValueError):a.validate_document_url(signed.url_requested+'&other=1',c)


def test_capture_provenance_hashes():
    for path in ROOT.glob('manifest-*.json'):
        for row in json.loads(path.read_text(encoding='utf-8')):
            if row.get('file'):
                assert hashlib.sha256((ROOT/row['file']).read_bytes()).hexdigest()==row['fixture_sha256']
