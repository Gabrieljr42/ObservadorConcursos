from copy import deepcopy
import pytest
from app.tenderproof.ocr_regions import region_from_page
from app.tenderproof.ocr_role_details import preview_role_details


def fixture():
    words=[]
    def add(text,x,y,width=35):
        words.append({'text':text,'bbox':[x,y,width,12]})
    add('12.',10,30,20);add('Enfermeiro',40,30,100)
    for text,x,width in [('Requisitos',10,90),('de',110,20),('ingresso:',140,80),('Remuneração:',610,120)]:
        add(text,x,80,width)
    for text,x,width in [('a)',10,20),('Diploma',40,70),('em',120,20),('Enfermagem',150,100),
                         ('reconhecido',260,100),('pelo',370,35),('MEC.',420,40),('R$',610,25),('6.780,90',650,80)]:
        add(text,x,130,width)
    for text,x,width in [('Registro',10,70),('regular',90,65),('no',165,20),('conselho',195,80),
                         ('profissional.',285,110),('(seis',600,40),('mil)',650,40)]:
        add(text,x,150,width)
    for text,x,width in [('Jornada',10,70),('de',90,20),('Trabalho:',120,80),('36',210,20),('horas',240,45),('semanais.',295,80)]:
        add(text,x,190,width)
    page={'page_number':3,'extraction_method':'ocr_tesseract','ocr':{'image_width':1000,'image_height':1000,'words':words}}
    return page


def extract(page,tables=()):
    region=region_from_page(page,'a'*64,[0,0,10000,10000])
    return preview_role_details(page,region,tables)


def table(hours='36 horas semanais',name='Enfermeiro'):
    return {'rows':[{'nome':name,'jornada':hours,'vagas_imediatas':5,'cidade':'Olinda','evidence':{'region_id':'table'}}]}


def test_separate_cells_dynamic_salary_and_exact_role_link():
    result=extract(fixture(),[table()])
    assert result['nome']=='Enfermeiro' and result['remuneracao']=='6780.90'
    assert result['requisitos']=='a) Diploma em Enfermagem reconhecido pelo MEC. Registro regular no conselho profissional.'
    assert result['jornada']=='36 horas semanais' and result['association_status']=='matched'
    assert result['evidence']['remuneracao']['page_number']==3
    assert result['vacancy_evidence']==[{'region_id':'table'}]
    assert set(result['evidence']['remuneracao']['word_indices']).isdisjoint(result['evidence']['requisitos']['word_indices'])


@pytest.mark.parametrize('tables,status',[
    ([], 'missing_vacancy_row'),([table(name='Enfermeiro Intensivista')], 'missing_vacancy_row'),
    ([table(hours='40 horas semanais')], 'conflicting_vacancy_row'),
    ([table(),table(hours='40 horas semanais')], 'conflicting_vacancy_row'),
    ([table(),table()], 'matched'),
])
def test_cannot_silently_associate_other_role_or_workload(tables,status):
    assert extract(fixture(),tables)['association_status']==status


@pytest.mark.parametrize('change',['fee_label','duplicate_role','second_currency','missing_weekly','missing_header','cropped'])
def test_conflicting_headers_multiple_amounts_and_partial_regions_rejected(change):
    page=fixture();words=page['ocr']['words']
    if change=='fee_label': next(w for w in words if w['text']=='Remuneração:')['text']='Taxa:'
    elif change=='duplicate_role': words.append({'text':'Outro Cargo','bbox':[10,50,120,12]})
    elif change=='second_currency': words.append({'text':'R$','bbox':[800,130,25,12]})
    elif change=='missing_weekly': words[:]=[w for w in words if w['text']!='semanais.']
    elif change=='missing_header': words[:]=[w for w in words if w['text']!='Requisitos']
    region=region_from_page(page,'a'*64,[0,0,10000,10000])
    if change=='cropped': region['boundary_words_excluded']=1
    assert preview_role_details(page,region) is None


def test_duplicate_role_inside_same_table_requires_review():
    t=table();t['rows'].append(deepcopy(t['rows'][0]))
    assert extract(fixture(),[t]) is None
