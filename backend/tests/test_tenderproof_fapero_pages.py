import pytest
from app.tenderproof.fapero_pages import annual_links,panels,document_url

def test_year_label_keeps_published_mismatching_path():
    url='https://rondonia.ro.gov.br/fapero/publicacoes/2017-2/'
    assert annual_links('<a href="'+url+'">2020</a>')=={url:'2020'}

def test_sections_exclude_statewide_service_documents():
    html='<a href="https://rondonia.ro.gov.br/wp-content/uploads/other.pdf">Other agency</a><div class="conteudo-pagina-full"><div class="entry"><section><h2>Programa</h2><a href="https://rondonia.ro.gov.br/wp-content/uploads/edital.pdf">Visualizar Edital</a><a href="https://rondonia.ro.gov.br/wp-content/uploads/aviso.pdf">Aviso de cancelamento</a></section></div></div>'
    groups,unassigned=panels(html,'https://rondonia.ro.gov.br/fapero/publicacoes/2026-2/')
    assert len(groups)==1 and not unassigned
    assert [d['kind'] for d in groups[0]['documents']]==['edital','outro']

@pytest.mark.parametrize('url',['https://rondonia.ro.gov.br/wp-content/uploads/%2e%2e/a.pdf','https://other.example/wp-content/uploads/a.pdf','https://rondonia.ro.gov.br/wp-content/uploads/a.pdf?redirect=1'])
def test_document_boundary(url):
    with pytest.raises(ValueError):document_url(url)
