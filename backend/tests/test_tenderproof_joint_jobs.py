import pytest
from app.tenderproof.contracts import PageText, FieldState
from app.tenderproof.fields import _evidence
from app.tenderproof.joint_jobs import extract_joint_jobs
from test_tenderproof_evidence import _artifact

PROFILE = '''2 DOS CARGOS DE ANALISTA E DE ANALISTA SUBSTITUTO
REQUISITO: diploma de curso superior e experiência de dois anos.
DESCRIÇÃO SUMÁRIA DAS ATIVIDADES: executar análises.
SUBSÍDIO: R$ 12.345,67 (doze mil reais).
3 DOS REQUISITOS BÁSICOS PARA A INVESTIDURA NO CARGO
4 DAS VAGAS'''
TABLE = '''Cargos
Vagas para ampla concorrência
Vagas reservadas para candidatos com deficiência
Vagas reservadas para candidatos negros
Vagas reservadas para candidatos indígenas
Vagas reservadas para candidatos quilombolas
Total
Analista e Analista Substituto
10 + CR 2 + CR 3 + CR 1 + CR 1 + CR 17 + CR
CR = cadastro de reserva.
4.1 DA LOTAÇÃO'''
FEE = '''6 DAS INSCRIÇÕES PRELIMINARES NO CONCURSO PÚBLICO
6.1 TAXA: R$ 210,00.
6.2 Outras informações.'''


def run(texts=None):
    pages=[PageText(artifact_id='art-ev',page_number=i,text=t) for i,t in enumerate(texts or [PROFILE,TABLE,FEE],1)]
    return extract_joint_jobs(_artifact(),pages,_evidence)


def test_joint_total_is_not_duplicated_and_fee_never_becomes_salary():
    field=run()
    assert field.state == FieldState.SUPPORTED
    assert len(field.value)==1
    job=field.value[0]
    assert job['nome']=='Analista e Analista Substituto'
    assert job['vagas_imediatas']==17 and job['cadastro_reserva'] is True
    assert job['remuneracao']=='12345.67' and job['taxa_inscricao']=='210.00'
    assert job['jornada'] is None
    assert {e.page_number for e in field.evidence}=={1,2,3}


@pytest.mark.parametrize('index,old,new',[
    (1,'17 + CR','18 + CR'),(1,'Analista e Analista Substituto','Técnico'),
    (1,'indígenas','outra categoria'),(1,'CR = cadastro de reserva.',''),
    (1,'4.1 DA LOTAÇÃO','Segunda linha de cargo'),
    (0,'SUBSÍDIO:','TAXA:'),(0,'REQUISITO:','OUTRO:'),
    (2,'6.1 TAXA:', '7.1 TAXA:'),
    (2,'6.2 Outras informações.','6.2 TAXA: R$ 300,00.'),
    (2,'6.2 Outras informações.','JORNADA: 40 horas semanais.'),
])
def test_incomplete_or_conflicting_meaning_is_pending(index,old,new):
    texts=[PROFILE,TABLE,FEE];texts[index]=texts[index].replace(old,new)
    field=run(texts)
    assert field.state==FieldState.FAILED and field.value is None


def test_damaged_or_duplicate_pages_do_not_supply_jobs():
    pages=[PageText(artifact_id='art-ev',page_number=i,text=t) for i,t in enumerate([PROFILE,TABLE,FEE],1)]
    pages[1].truncated=True
    assert extract_joint_jobs(_artifact(),pages,_evidence).state==FieldState.FAILED
    pages[1].truncated=False;pages[2].page_number=2
    assert extract_joint_jobs(_artifact(),pages,_evidence).state==FieldState.FAILED
