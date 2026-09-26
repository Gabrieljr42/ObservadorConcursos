import pytest
from app.tenderproof.fapesq_detail import parse_detail,parse_file_view

URL='https://fapesq.rpp.br/editais/2035/selecao-tecnica'


def html(links):
    return '<link rel="canonical" href="'+URL+'"><div id="content"><h1 class="documentFirstHeading">Edital 17/2035</h1><div id="parent-fieldname-text">'+links+'</div></div>'


def test_original_amendment_and_broken_link_remain_in_manifest():
    data=parse_detail(html('<a href="/editais/original.pdf">Edital 17/2035</a><a href="/editais/atual.pdf">Edital 17/2035 (Retificado)</a><a href="https://fapesq.rpp.br/../../editais-2035/resultado.pdf/view">Homologação</a>'),URL)
    assert [d['kind'] for d in data['documents']]==['edital','consolidado','outro']
    last=data['documents'][-1]
    assert last['requires_file_page'] and last['normalized_dot_segments']
    assert last['url']=='https://fapesq.rpp.br/editais-2035/resultado.pdf/view'
    assert '/../' in last['href_observed']


def test_wrong_identity_host_and_missing_document_body_fail():
    with pytest.raises(ValueError):parse_detail(html('<a href="https://evil.invalid/file.pdf">Edital</a>'),URL)
    with pytest.raises(ValueError):parse_detail(html('<a href="/editais/file.pdf">Edital</a>').replace(URL,URL+'-other'),URL)
    with pytest.raises(ValueError):parse_detail(html(''),URL)


def test_malformed_other_link_remains_explicit_without_losing_valid_document():
    data=parse_detail(html('<a href="/editais/file.pdf">Edital</a><a href="http://Edital Nº 32">Endereço malformado</a>'),URL)
    assert len(data['documents'])==1 and not data['manifest_complete']
    assert data['unresolved_links'][0]['href_observed']=='http://Edital Nº 32'


def test_file_view_requires_canonical_binding_and_observed_download():
    base='https://fapesq.rpp.br/editais/editais-2035/resultado.pdf'
    markup='<link rel="canonical" href="'+base+'"><div id="content"><a href="'+base+'/@@download/file/Resultado final.pdf">Arquivo</a></div>'
    assert parse_file_view(markup,base+'/view')==base+'/@@download/file/Resultado%20final.pdf'
    with pytest.raises(ValueError):parse_file_view(markup.replace('rel="canonical"','rel="other"'),base+'/view')
    with pytest.raises(ValueError):parse_file_view(markup.replace('/@@download/file/','/elsewhere/'),base+'/view')
    with pytest.raises(ValueError):parse_file_view(markup.replace('Resultado final.pdf','..%2Fother.pdf'),base+'/view')
