import pytest
from app.tenderproof.fapac_pages import panels,EDITAIS,document_url
from app.tenderproof.fapac_adapter import eligible

def test_edition_boundary_and_republication_whole_paragraph():
    base='https://fapac.ac.gov.br/wp-content/uploads/'
    html='<article><div class="czr-wp-the-content"><p><a href="'+base+'old.pdf">Edital 2024</a></p><p>EDITAIS 2026</p><p><a href="'+base+'new.pdf">Edital 2026</a></p><p><a href="'+base+'fix.pdf">E</a><a href="'+base+'fix.pdf">DITAL 2026</a> Republicado por Incorreção</p><p><a href="'+base+'a.docx">Anexo I</a></p></div></article>'
    groups,_=panels(html,EDITAIS)
    assert len(groups)==2
    assert [d['kind'] for d in groups[1]['documents']]==['edital','retificacao','anexo']
    assert len(eligible(html,EDITAIS)[0])==2

def test_ambiguous_originals_withheld_and_external_annex_preserved():
    base='https://fapac.ac.gov.br/wp-content/uploads/'
    html='<article><div class="czr-wp-the-content"><p><a href="'+base+'a.pdf">Edital 1</a></p><p><a href="'+base+'b.pdf">Edital 2</a></p><p><a href="https://external.example/anexo.docx">Anexo</a></p></div></article>'
    groups,pending,_=eligible(html,EDITAIS)
    assert not groups and pending
    assert panels(html,EDITAIS)[0][0]['pending_links'][0]['url']=='https://external.example/anexo.docx'

@pytest.mark.parametrize('url',['https://other.example/wp-content/uploads/a.pdf','https://fapac.ac.gov.br/wp-content/uploads/%2e%2e/a.pdf','https://fapac.ac.gov.br/wp-content/uploads/a.pdf?redirect=1'])
def test_document_boundary(url):
    with pytest.raises(ValueError):document_url(url)
