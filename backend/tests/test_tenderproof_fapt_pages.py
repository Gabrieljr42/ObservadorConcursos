import pytest
from app.tenderproof.fapt_pages import parse,page_url,document_url,document_kind

def test_content_graph_ignores_navigation_and_keeps_documents():
    html='''<a href="https://evil.example">nav</a><div class="page_headline"><h1>Edital</h1></div><div class="page_main_content"><a href="http://www.to.gov.br/fapt/edital/abc123"><i>link</i>Edital filho</a><a href="https://central.to.gov.br/download/123">Edital.pdf</a></div>'''
    p=parse(html,'https://www.to.gov.br/fapt/selecoes/abc')
    assert p['children']=={'https://www.to.gov.br/fapt/edital/abc123':'Edital filho'}
    assert len(p['documents'])==1 and not p['pending_links']

def test_roles_do_not_promote_results_or_annexes_to_originals():
    assert document_kind('Resultado preliminar do EDITAL 07.pdf')=='outro'
    assert document_kind('Retificação 002_EDITAL 07.pdf')=='retificacao'
    assert document_kind('ANEXO I do Edital.docx')=='anexo'
    assert document_kind('EDITAL 07 - Bolsistas.pdf')=='edital'

@pytest.mark.parametrize('url',['https://central.to.gov.br/download/1?x=2','https://central.to.gov.br/download/../123','https://evil.example/download/123'])
def test_document_boundary(url):
    with pytest.raises(ValueError):document_url(url)

def test_source_boundary():
    with pytest.raises(ValueError):page_url('https://www.to.gov.br/outra-agencia/edital/123')
