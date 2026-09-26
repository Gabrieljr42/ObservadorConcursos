import pytest
from app.tenderproof.registration_effects import preview_registration_effects


def region(role='Analista em Comércio Exterior'):
    return {'id':'ocr-region-fixture','document_sha256':'a'*64,'page_number':2,'boundary_words_excluded':0,'text':f'''PORTARIA CONJUNTA SAD/FACEPE Nº 250 DO DIA 15 DE AGOSTO DE 2027
Considerando o edital de seleção pública simplificada, regido pela Portaria Conjunta SAD/FACEPE nº 205, do dia 23 de julho de 2027,
Art. 1º Anular as inscrições exclusivamente para a função de {role}, realizadas no período de 29/07/2027 a 12/08/2027;
Art. 2º reabrir o período de inscrições exclusivamente para a função de {role};
Art. 3º Estabelecer o novo cronograma de atividades exclusivamente para a função de {role}, conforme a seguir:
Evento Data/Período Local
Inscrições 16/08/2027 até às 18h30min de 30/08/2027 https://example.invalid
Art.4º Esta portaria conjunta entra em vigor na data da sua publicação.
'''}


@pytest.mark.parametrize('role',['Analista em Comércio Exterior','Engenheiro Civil'])
def test_reopening_keeps_scope_cancelled_period_and_dynamic_dates(role):
    r=region(role);effect=preview_registration_effects('facepe_selection',r)[0]
    assert effect['scope']=={'kind':'function','name':role,'exclusive':True}
    assert effect['act']['number']=='250' and effect['original_act']['number']=='205'
    assert effect['annulled_period']=={'start':'2027-07-29','end':'2027-08-12'}
    assert effect['new_period']=={'start':'2027-08-16','end':'2027-08-30','end_time':'18:30'}
    assert effect['review_required']
    for e in effect['evidence']:
        assert r['text'][e['start']:e['end']]==e['snippet']
        assert e['region_id']==r['id'] and e['page_number']==2 and e['document_sha256']=='a'*64


@pytest.mark.parametrize('old,new',[
    ('exclusivamente','também'),('30/08/2027','31/02/2027'),('18h30','24h30'),
    ('16/08/2027','01/07/2027'),('a função de Analista em Comércio Exterior;','a função de Engenheiro Civil;'),
    ('Inscrições 16/08/2027','Pagamento 16/08/2027'),('SAD/FACEPE','SAD/FUNASE'),
])
def test_conflicting_scope_invalid_dates_or_other_events_cannot_be_reopening(old,new):
    r=region();r['text']=r['text'].replace(old,new)
    assert preview_registration_effects('facepe_selection',r)==[]


def test_multiple_periods_adjacent_acts_cut_words_and_other_source_rejected():
    r=region()
    assert not preview_registration_effects('other_source',r)
    assert not preview_registration_effects('facepe_selection',{**r,'boundary_words_excluded':1})
    for extra in ['\nInscrições 17/08/2027 até às 18h30min de 31/08/2027',
                  '\nPORTARIA CONJUNTA SAD/OUTRO Nº 99', '\nNº 2.642-Autorizar cessão']:
        assert not preview_registration_effects('facepe_selection',{**r,'text':r['text']+extra})
