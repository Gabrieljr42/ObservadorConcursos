import json
import pytest
from app.tenderproof.fundect_pages import HOST,parse_api,documents

def test_proposal_update_is_not_original_and_annex_context_is_retained():
    html='<p>Anexo I - <a href="'+HOST+'/wp-content/uploads/2026/01/projeto.docx">Projeto</a></p><p><a href="'+HOST+'/wp-content/uploads/2026/01/chamada.pdf">23/01/2026 - Chamada 1/2026</a></p>'
    post={'id':12,'permalink':HOST+'/informativos/consultas/chamada-1/','projeto':'Chamada 1','observacao_html':html,'proposta':HOST+'/wp-content/uploads/2026/02/update.pdf','leitura':'Prorrogação'}
    row=parse_api(json.dumps({'posts':[post]}))[0]
    assert [d['kind']for d in row['documents']]==['anexo','edital']
    assert row['pending_links'][0]['title']=='Prorrogação'
    with pytest.raises(ValueError):parse_api(json.dumps({'posts':[post,post]}))

def test_result_label_keeps_edital_filename_out_of_original_selection():
    html='<a href="'+HOST+'/wp-content/uploads/2026/01/Edital.pdf">Homologação do resultado final</a>'
    assert documents(html,HOST+'/chamada/')['documents'][0]['kind']=='outro'

def test_original_and_annex_in_same_paragraph_keep_separate_roles():
    html='<p><a href="'+HOST+'/wp-content/uploads/2026/01/chamada.pdf">Chamada 14/2026</a> Anexo I - <a href="'+HOST+'/wp-content/uploads/2026/01/plano.docx">Plano</a></p>'
    assert [d['kind']for d in documents(html,HOST+'/chamada/')['documents']]==['edital','anexo']
