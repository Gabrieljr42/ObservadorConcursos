import pytest
from app.tenderproof.fapes_documents import document_manifest


def panel(labels):
    return {'panel_id': '91', 'title': 'Edital 5/2036', 'documents': [
        {'title': label, 'url': 'https://fapes.es.gov.br/Media/fapes/'+str(i)+'.pdf', 'format': 'pdf'}
        for i, label in enumerate(labels)]}


def test_versions_and_results_do_not_replace_original():
    m = document_manifest(panel(['Edital 5/2036 (2ª alteração)', 'Resultado do Edital 5/2036',
        'Edital 5/2036', 'Anexo III', 'Errata 01', 'Prorrogação das inscrições']))
    assert [d['kind'] for d in m['documents']] == ['consolidado','outro','edital','anexo','retificacao','prorrogacao']
    assert m['original_url'].endswith('/2.pdf') and m['scope_review_required']


def test_multiple_originals_require_review_and_annual_panel_is_not_a_contest():
    assert document_manifest(panel(['Edital 5/2036','Edital 8/2036']))['original_review_required']
    p = panel(['Edital 5/2036']);p['title'] = 'Resultado Editais 2036'
    with pytest.raises(ValueError):document_manifest(p)


def test_international_call_label_and_duplicate_call_titles_remain_distinct():
    m=document_manifest(panel(['1ª CHAMADA CONJUNTA 2036', 'Diretrizes da FAPES', 'Publicação CONFAP']))
    assert m['original_url'].endswith('/0.pdf')
    assert document_manifest(panel(['CHAMADA 2036','CHAMADA 2036']))['original_review_required']
def test_specific_guidelines_with_same_call_title_are_not_second_original():
    from app.tenderproof.fapes_documents import document_manifest
    panel = {'panel_id': '999', 'title': 'Chamada nova', 'documents': [
        {'title':'CHAMADA NOVA', 'url':'https://fapes.es.gov.br/Media/fapes/local.pdf', 'format':'pdf', 'description':'Diretrizes específicas da Fapes'},
        {'title':'CHAMADA NOVA', 'url':'https://fapes.es.gov.br/Media/fapes/call.pdf', 'format':'pdf', 'description':'Call announcement'},
    ]}
    result = document_manifest(panel)
    assert result['original_url'].endswith('/call.pdf')
    assert result['documents'][0]['document_role'] == 'specific_guidelines'
    assert result['scope_review_required'] is True
