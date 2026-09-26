import json
import pytest
from app.tenderproof.fapdf_pages import LISTING,document_url,panels
from app.tenderproof.fapdf_adapter import FapdfAdapter

def test_nested_panels_do_not_duplicate_calls_and_context_keeps_amendment():
    html='''<div class="journal-content-article"><button aria-controls="parent">Programa</button><div id="parent"><button aria-controls="child">Servidores</button><div id="child"><p><a href="/documents/d/fap/original-pdf">EDITAL 01</a></p><p><a href="/documents/d/fap/new-pdf">EDITAL 01</a> 1ª RETIFICAÇÃO</p><p><a href="/documents/d/fap/edital-result-pdf">Resultado do edital</a></p></div></div></div>'''
    groups,unassigned=panels(html,LISTING+'editais-fapdf-20261')
    assert len(groups)==1 and not unassigned
    assert [d['kind'] for d in groups[0]['documents']]==['edital','consolidado','outro']

def test_identity_survives_liferay_dom_id_change():
    a=FapdfAdapter();url=LISTING+'editais-fapdf-20261'
    menu=f'<li><a href="{LISTING}category/editais">Editais</a><ul><li><a href="{url}">2026</a></li></ul></li>'
    def proof(suffix):
        return json.dumps({'format':'fapdf/1','url':url,'menu':menu,'html':f'<div class="journal-content-article"><button aria-controls="{suffix}">Servidores</button><div id="{suffix}"><a href="/documents/d/fap/original-pdf">EDITAL 01</a></div></div>'})
    c=a.parse_listing(proof('first'),url).candidates[0]
    assert a.parse_listing(proof('second'),url).candidates[0].candidate_id==c.candidate_id
    a.confirm_identity(c,proof('second'),c.detail_url_observed)
    assert a.choose_document(a.documents(proof('second'),c)).kind=='edital'

@pytest.mark.parametrize('url',[LISTING+'documents/../secret.pdf',LISTING+'documents/%252e%252e/secret.pdf','https://evil.example/documents/x.pdf',LISTING+'documents/x.pdf?redirect=1'])
def test_document_boundary(url):
    with pytest.raises(ValueError):document_url(url)
