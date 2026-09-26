import pytest
from app.tenderproof.fapeam_detail import parse_detail, validate_document_url

URL='https://www.fapeam.am.gov.br/editais/selecao-futura/'
PDF='https://www.fapeam.am.gov.br/wp-content/uploads/2031/03/edital.pdf'
UPDATE=PDF.replace('edital.pdf','decisao.pdf')


def page():
    return f'''<link rel="canonical" href="{URL}">
    <article class="post-type-editais" id="post-872">
    <h1 class="page-title">Seleção futura</h1><div class="article-body">
    <div class="download-documento-box"><a href="{PDF}">Baixar Arquivo do Edital</a></div>
    <p>Inscrições: item <a href="{UPDATE}">alterado pela decisão</a>.</p>
    <a href="{UPDATE}">Segunda referência ao mesmo arquivo</a>
    </div></article><aside><a href="{PDF.replace('edital.pdf','unrelated.pdf')}">Outro programa</a></aside>'''


def test_article_identity_excludes_sidebar_and_preserves_unassessed_amendment():
    parsed=parse_detail(page(),url=URL,external_id='872')
    assert len(parsed['documents'])==2
    original,update=parsed['documents']
    assert original['url']==PDF and original['kind']=='edital'
    assert update['url']==UPDATE and update['kind']=='requires_review'
    assert len(update['labels_observed'])==2
    assert update['context_observed']==['Inscrições: item alterado pela decisão .']
    assert update['effect_status']=='not_assessed'
    assert not parsed['scope_complete'] and not parsed['document_coverage_complete']


@pytest.mark.parametrize('changed',[
    lambda s:s.replace('post-872','post-873'),
    lambda s:s.replace('rel="canonical"','rel="other"'),
    lambda s:s.replace(f'href="{URL}"',f'href="{URL}other/"'),
    lambda s:s.replace('class="article-body"','class="sidebar"'),
    lambda s:s+f'<link rel="canonical" href="{URL}">',
    lambda s:s+'<article class="post-type-editais" id="post-873"></article>',
])
def test_identity_or_principal_ambiguity_is_not_empty_success(changed):
    with pytest.raises(ValueError):parse_detail(changed(page()),url=URL,external_id='872')


@pytest.mark.parametrize('target',[
    'http://www.fapeam.am.gov.br/wp-content/uploads/2031/03/a.pdf',
    'https://evil.test/wp-content/uploads/2031/03/a.pdf',
    PDF+'?redirect=1',PDF+'#other',
    PDF.replace('/03/','/99/'),PDF.replace('edital.pdf','a%2Fb.pdf'),
    PDF.replace('edital.pdf','a%5Cb.pdf'),PDF.replace('edital.pdf','a%00b.pdf'),
])
def test_document_destinations_are_bounded(target):
    with pytest.raises(ValueError):validate_document_url(target)
    with pytest.raises(ValueError):parse_detail(page().replace(PDF,target),url=URL,external_id='872')


def test_relative_official_pdf_is_resolved_and_external_reference_is_not_downloadable():
    result=parse_detail(page().replace(PDF,'/wp-content/uploads/2031/03/edital.pdf'),url=URL,external_id='872')
    assert result['documents'][0]['url']==PDF
    result=parse_detail(page().replace(UPDATE,'https://evil.test/update.pdf'),url=URL,external_id='872')
    assert len(result['documents'])==1
    assert result['external_references'][0]['url_observed']=='https://evil.test/update.pdf'
    assert result['external_references'][0]['acquisition_status']=='not_acquired'
    assert not result['document_coverage_complete']


def test_article_without_pdf_button_preserves_html_and_never_promotes_update_to_original():
    html=page().replace('class="download-documento-box"','class="other"')
    parsed=parse_detail(html,url=URL,external_id='872')
    assert parsed['principal_status']=='no_primary_pdf_link_observed'
    assert parsed['body_text_observed']
    assert all(d['kind']=='requires_review' for d in parsed['documents'])
    assert not parsed['document_coverage_complete']


def test_official_bare_host_reference_keeps_observed_url_and_is_not_external():
    bare=UPDATE.replace('www.fapeam','fapeam')
    parsed=parse_detail(page().replace(UPDATE,bare),url=URL,external_id='872')
    assert parsed['documents'][1]['url']==bare
    assert parsed['documents'][1]['kind']=='requires_review'
    assert parsed['external_references']==[]
    for target in [bare.replace('fapeam.am.gov.br','sub.fapeam.am.gov.br'),
                   bare.replace('fapeam.am.gov.br','fapeam.am.gov.br.evil.test'),
                   bare.replace('fapeam.am.gov.br','fapeam.am.gov.br:443')]:
        with pytest.raises(ValueError):validate_document_url(target)
