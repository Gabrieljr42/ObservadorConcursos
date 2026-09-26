import pytest
from app.tenderproof.contracts import PageText
from app.tenderproof.jcm_job_tables import extract_jcm_tables

HEADER = '''Denominação Vagas Requisitos Mínimos / Escolaridade
Venci- mento (BASE) R$ Carga Horária Semanal Taxa de Inscrição R$
Provas Ampla Concorrência PcD Tipo Nº de Questões Pontos Por Questão Por Prova
'''
ROW = '''Agente de
Atendimento 4 – Ensino Médio Completo 3.200,00 30 h 75,00 Português
Matemática
10 20 4,0 3,0 40,0 60,0
'''
END = '''_____
– = Não há reserva imediata de vaga PcD em razão do quantitativo ofertado.
'''


def parse(text, **kwargs):
    return extract_jcm_tables([PageText(artifact_id='a',page_number=9,text=text,**kwargs)])


def test_complete_table_keeps_salary_fee_and_requirements_per_job():
    second = ROW.replace('Atendimento 4 –', 'Apoio 1 2').replace('3.200,00','2.400,00').replace('75,00','45,00')
    rows, failures = parse(HEADER+ROW+second+END)
    assert not failures
    assert [r[0]['nome'] for r in rows] == ['Agente de Atendimento', 'Agente de Apoio']
    assert [r[0]['vagas_imediatas'] for r in rows] == [4,3]
    assert [r[0]['remuneracao'] for r in rows] == ['3200.00','2400.00']
    assert [r[0]['taxa_inscricao'] for r in rows] == ['75.00','45.00']
    assert all(r[0]['cadastro_reserva'] is None for r in rows)
    assert all(r[2] in r[1].text and r[3] in r[1].text for r in rows)


@pytest.mark.parametrize('text',[
    HEADER+ROW+'Outra linha não interpretada\n'+END,
    HEADER+ROW,
    HEADER+ROW+END.replace('Não há reserva imediata','Legenda desconhecida'),
    HEADER+ROW.replace('40,0 60,0','45,0 60,0')+END,
    HEADER+ROW.replace('75,00','75,00 BENEFÍCIO 500,00')+END,
    HEADER+ROW+ROW+END,
    HEADER.replace('Taxa de Inscrição','Benefícios')+ROW+END,
])
def test_unsupported_or_incomplete_tables_remain_implementation_work(text):
    _, failures = parse(text)
    assert failures


def test_truncated_page_cannot_support_complete_jobs():
    assert parse(HEADER+ROW+END,truncated=True)[1]


@pytest.mark.parametrize('requirement', [
    'Alfabetizado 02 anos de experiência',
    'Formação em Ensino Superior em Pedagogia ou Psicologia',
    'Curso Superior em Odontologia Registro no conselho de Classe - CRO',
    'Superior em Medicina Registro no CRM',
    'Ser Alfabetizado, possuir CNH categoria D e preencher os requisitos do art. 145',
    'Ensino Superior em contabilidade Experiência de no mínimo 6 (seis) meses',
])
@pytest.mark.parametrize('extra_exam', ['Prática Apto / Inapto\n', 'Títulos - - 10,0\n'])
def test_requirements_and_extra_exams_stay_in_their_own_job(requirement, extra_exam):
    first = ROW.replace('Ensino Médio Completo', requirement) + extra_exam
    second = ROW.replace('Atendimento', 'Apoio').replace('3.200,00', '8.750,00')
    rows, failures = parse(HEADER+first+second+END)
    assert not failures and len(rows)==2
    assert rows[0][0]['requisitos']==requirement
    assert [r[0]['remuneracao'] for r in rows]==['3200.00','8750.00']
    assert rows[1][0]['nome']=='Agente de Apoio'


def test_missing_money_must_not_borrow_values_from_next_job():
    broken = 'Agente de Atendimento 4 – Ensino Médio Completo\n'
    second = ROW.replace('Atendimento', 'Apoio')
    rows, failures = parse(HEADER+broken+second+END)
    assert failures and not rows


def test_shared_cells_require_an_explicit_layout_contract():
    partial = 'Agente Comunitário de Saúde (*) 1 –\n'
    assert parse(HEADER+ROW+partial+END)[1]
