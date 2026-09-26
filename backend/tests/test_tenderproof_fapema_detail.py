import pytest
from app.tenderproof.fapema_detail import parse_detail,viewer_document,role
from app.tenderproof.fapema_listing import HOST


URL=HOST+'/edital-futuro/'
FILE=HOST+'/wp-content/uploads/2030/01/novo.pdf'
VIEWER=HOST+'/wp-content/plugins/pdfjs-viewer-shortcode/pdfjs/web/viewer.php?file='+FILE


def fixture(label='01/01 - EDITAL'):
    return f'<link rel="canonical" href="{URL}"><article id="main"><h1 class="h-entry__p-name">Novo</h1><section class="h-entry__e-content"><p>COMUNICADO: recursos prorrogados até 15/02.</p><div class="accordion"><a href="#">{label}</a><a href="{VIEWER}">Tela Cheia</a><iframe src="{VIEWER}"></iframe></div></section></article>'


def test_pdfjs_duplicate_display_preserves_one_document_and_html_notice():
    parsed=parse_detail(fixture(),URL)
    assert len(parsed['documents'])==1
    assert parsed['documents'][0]['url']==FILE and parsed['documents'][0]['kind']=='edital'
    assert parsed['html_effect_review_required'] and parsed['html_notices']
    assert parsed['manifest_complete']
    with pytest.raises(ValueError):parse_detail(fixture(),HOST+'/outro/')


@pytest.mark.parametrize('url',[VIEWER+'&file='+FILE,VIEWER.replace(FILE,'https://evil.test/arquivo.pdf'),VIEWER.replace(FILE,HOST+'/wp-content/uploads/%252e%252e/arquivo.pdf')])
def test_unsafe_or_ambiguous_viewer_file_refused(url):
    with pytest.raises(ValueError):viewer_document(url)


def test_missing_panel_label_and_external_documents_are_pending():
    parsed=parse_detail(fixture().replace('href="#"','href="#missing"'),URL)
    assert parsed['pending_links'] and not parsed['manifest_complete']
    parsed=parse_detail(fixture().replace(VIEWER,'https://external.test/file.pdf'),URL)
    assert parsed['pending_links'] and not parsed['documents']
    assert role('03/08 - 3ª CHAMADA DE EXCEDENTES')=='outro'
    assert role('01/02 - EDITAL RETIFICADO')=='consolidado'


def test_closed_wrapper_does_not_lose_next_editorial_label():
    second=VIEWER.replace('novo.pdf','resultado.pdf')
    html=fixture().replace('</section>',f'<a href="#">02/02 - RESULTADO FINAL</a><a href="{second}">Tela Cheia</a><iframe src="{second}"></iframe></section>')
    parsed=parse_detail(html,URL)
    assert len(parsed['documents'])==2
    assert parsed['documents'][1]['title']=='02/02 - RESULTADO FINAL'
    assert parsed['documents'][1]['kind']=='outro'
    assert len(parsed['documents'][1]['observed_links'])==2
