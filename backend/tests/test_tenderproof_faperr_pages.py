import pytest
from app.tenderproof.faperr_pages import discover,parse,document_url

def test_menu_categories_and_mobile_duplicates():
    item='<li><a href="#">{}</a><ul><li><a href="#">Voltar</a></li><li><a href="https://faperr.rr.gov.br/{}/">Chamada</a></li></ul></li>'
    html='<nav>'+''.join(item.format(label,slug) for label,slug in [('Abertos','atual'),('Em andamento','andamento'),('Encerrados','arquivo')])+'</nav>'
    assert len(discover(html+html))==3

def test_external_amendment_remains_pending():
    html='<article><h1 class="entry-title">PROFIX</h1><div class="entry-content"><a href="https://faperr.rr.gov.br/wp-content/uploads/2026/edital.pdf">Edital PROFIX</a><a href="https://drive.google.com/file/d/abcd/view">Retificação</a></div></article>'
    p=parse(html,'https://faperr.rr.gov.br/profix/')
    assert p['documents'][0]['kind']=='edital'
    assert p['pending_links'][0]['title']=='Retificação'

@pytest.mark.parametrize('url',['https://evil.example/wp-content/uploads/edital.pdf','https://faperr.rr.gov.br/wp-content/uploads/%2e%2e/edital.pdf','https://faperr.rr.gov.br/wp-content/uploads/edital.pdf?x=1'])
def test_document_boundary(url):
    with pytest.raises(ValueError):document_url(url)
