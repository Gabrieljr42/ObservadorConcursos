import json
import pytest
from app.tenderproof.fapemig_pages import LISTING,decode_payload,parse_api,documents,document_url

def test_nuxt_reference_decode_without_execution():
    assert decode_payload(json.dumps([{'data':1},['ShallowReactive',2],{'id':3,'slug':4},192,'chamada-2026']))=={'data':{'id':192,'slug':'chamada-2026'}}
    with pytest.raises(ValueError):decode_payload('[{"loop":0}]')

def test_api_rejects_duplicate_ids_and_wrong_page():
    d={'page':1,'total':2,'pagination':{'page':1,'per_page':12,'total':2,'total_pages':1},'data':[{'id':1,'slug':'a','publicacao_status':'publish'},{'id':1,'slug':'b','publicacao_status':'publish'}]}
    with pytest.raises(ValueError):parse_api(json.dumps(d),LISTING)
    d['data'][1]['id']=2
    assert len(parse_api(json.dumps(d),LISTING)[0])==2
    with pytest.raises(ValueError):parse_api(json.dumps(d),LISTING.replace('page=1&','page=2&'))

def test_retification_flag_and_outside_annex_are_preserved():
    a={'descricao':'Chamada 04/2026','tipo':'documento_geral','retificacao':True,'url_anexo':'https://api.site.fapemig.br/wp-content/uploads/a.pdf'}
    docs,pending=documents({'anexos':[a,{**a,'url_anexo':'https://outside.example/a.pdf'}]})
    assert docs[0]['kind']=='retificacao' and len(pending)==1

@pytest.mark.parametrize('url',['https://api.site.fapemig.br/wp-content/uploads/%2e%2e/a.pdf','https://api.site.fapemig.br/wp-content/uploads/a.pdf?next=x'])
def test_document_boundary(url):
    with pytest.raises(ValueError):document_url(url)
