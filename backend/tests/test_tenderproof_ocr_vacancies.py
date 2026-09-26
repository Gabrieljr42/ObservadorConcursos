from copy import deepcopy
import pytest
from app.tenderproof.ocr_regions import region_from_page
from app.tenderproof.ocr_vacancies import preview_vacancies


def fixture(scale=1):
    words=[]
    def add(text,x,y,w=40):
        words.append({'text':text,'bbox':[int(v*scale) for v in (x,y,w,12)]})
    for text,x in [('FUNÇÃO',100),('CARGA',340),('REGIME',410),('CIDADE',480),('VCG',550),('PCD',620),('TOTAL',690)]:
        add(text,x,100)
    for y,name,hours,vcg,pcd,total in [(150,'Enfermeiro','36h','4','1','5'),(200,'Técnico Laboratorial','20h','2','-','2')]:
        add(name,20,y,240); add(hours,310,y,25); add('semanais',340,y)
        add('Diarista',410,y); add('Olinda',480,y)
        add(vcg,560,y,10); add(pcd,630,y,10); add(total,700,y,10)
    add('TOTAL',20,250); add('6',560,250,10);add('1',630,250,10);add('7',700,250,10)
    page={'page_number':7,'extraction_method':'ocr_tesseract','ocr':{
        'image_width':int(1000*scale),'image_height':int(1000*scale),'words':words}}
    return page


def extract(page):
    return preview_vacancies(page,region_from_page(page,'a'*64,[0,0,10000,10000]))


@pytest.mark.parametrize('scale',[1,2,3])
def test_dynamic_rows_and_coordinates_preserve_quotas_and_missing_fields(scale):
    page=fixture(scale); result=extract(page)
    assert result['total_vagas']==7 and result['total_pcd']==1
    first,second=result['rows']
    assert first['nome']=='Enfermeiro' and first['jornada']=='36 horas semanais'
    assert second['nome']=='Técnico Laboratorial' and second['jornada']=='20 horas semanais'
    assert first['vagas_imediatas']==5 and first['vagas_ampla_concorrencia']==4 and first['vagas_pcd']==1
    assert second['vagas_pcd']==0 and second['cadastro_reserva'] is None
    assert first['remuneracao'] is None and 'requisitos' in first['pending_fields']
    assert all(page['ocr']['words'][i] for i in first['evidence']['word_indices'])
    assert first['evidence']['page_number']==7


@pytest.mark.parametrize('change',['sum','quota','missing_header','duplicate_header','other_table','no_weekly'])
def test_ambiguous_incomplete_and_inconsistent_tables_rejected(change):
    page=fixture(); words=page['ocr']['words']
    if change=='sum': words[-1]['text']='8'
    elif change=='quota': words[-2]['text']='2'
    elif change=='missing_header': words[5]['text']='OUTRO'
    elif change=='duplicate_header': words.append(deepcopy(words[0]))
    elif change=='other_table': words[0]['text']='CANDIDATO'
    elif change=='no_weekly': words[:]=[w for w in words if w['text']!='semanais']
    assert extract(page) is None


def test_unreadable_quota_is_not_invented_from_subtraction():
    page=fixture()
    page['ocr']['words']=[w for w in page['ocr']['words'] if not(w['bbox'][0]==630 and w['bbox'][1]==150)]
    result=extract(page)
    assert result['rows'][0]['vagas_pcd'] is None
    assert 'vagas_pcd' in result['rows'][0]['pending_fields']
