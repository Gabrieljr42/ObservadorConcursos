import pytest
from app.tenderproof.contracts import PageText, FieldState
from app.tenderproof.prose_jobs import extract_prose_jobs
from app.tenderproof.fields import extract_fields
from test_tenderproof_evidence import _candidate, _artifact


PROFILES='''2 DOS CARGOS
2.1 CARGO 11: ANALISTA – ÁREA: INFORMÁTICA
REQUISITOS: diploma em Computação.
ATRIBUIÇÕES: desenvolver sistemas.
REMUNERAÇÃO: R$ 8.123,45.
CARGA HORÁRIA: 30 horas semanais.
2.2 CARGO 27: ANALISTA – ÁREA: ECONOMIA
REQUISITO: diploma em Economia e registro.
ATRIBUIÇÕES: elaborar estudos.
REMUNERAÇÃO: R$ 6.234,56.
CARGA HORÁRIA: 40 horas semanais.
3 DOS REQUISITOS BÁSICOS
'''
MATRIX='''Cargo/Área
Vagas imediatas
Cadastro de Reserva
(excluídas as vagas
imediatas)
Total
(incluídas
as vagas
imediatas) AC PCD PPIQ Total AC PCD PPIQ Total
Cargo 27: Analista – Área: Economia 2 * 1 3 1 1 1 3 6
Cargo 11: Analista – Área: Informática 1 * * 1 2 1 1 4 5
*Não há vaga para o provimento imediato, mantendo-se o cadastro de reserva.
'''
FEE='6 DAS INSCRIÇÕES NO CONCURSO PÚBLICO\n6.1 TAXA: R$ 175,00.\n'


def pages(profiles=PROFILES,matrix=MATRIX,fee=FEE):
    return [PageText(artifact_id='art-ev',page_number=i+1,text=t)
            for i,t in enumerate([profiles,matrix,fee])]


def test_profiles_join_reordered_rows_by_id_and_name_with_page_evidence():
    p=pages(); jobs,ev,error=extract_prose_jobs(p)
    assert error is None
    assert [(j['vagas_imediatas'],j['remuneracao'],j['taxa_inscricao'],j['jornada']) for j in jobs]==[
        (1,'8123.45','175.00','30 horas semanais'),(3,'6234.56','175.00','40 horas semanais')]
    assert jobs[1]['requisitos']=='diploma em Economia e registro.'
    assert all(j['cadastro_reserva'] for j in jobs)
    assert {page.page_number for page,_ in ev}=={1,2,3}
    assert all(snippet in page.text for page,snippet in ev)
    c=_candidate().model_copy(update={'source':'cebraspe_open'})
    f=next(f for f in extract_fields(candidate=c,artifact=_artifact(),pages=p) if f.field_name=='cargos')
    assert f.state==FieldState.SUPPORTED and f.value==jobs


@pytest.mark.parametrize('part,old,new', [
    ('matrix','1 * * 1 2 1 1 4 5','1 * * 9 2 1 1 4 5'),
    ('matrix','Cargo 27:','Cargo 28:'),
    ('matrix','Área: Economia','Área: Contabilidade'),
    ('matrix','AC PCD PPIQ Total','AC PPIQ PCD Total'),
    ('matrix','*Não há vaga','*Há vaga'),
    ('profiles','REMUNERAÇÃO: R$ 6.234,56.',''),
    ('profiles','3 DOS REQUISITOS BÁSICOS',''),
    ('profiles','2.2 CARGO 27:','2.2 CARGO 11:'),
    ('fee','6.1 TAXA:','6.1 TAXA POR CARGO:'),
])
def test_incomplete_or_mismatched_data_remains_unpublishable(part,old,new):
    args={'profiles':PROFILES,'matrix':MATRIX,'fee':FEE}
    args[part]=args[part].replace(old,new)
    jobs,_,error=extract_prose_jobs(pages(**args))
    assert error and not jobs


def test_second_fee_and_missing_physical_page_are_rejected():
    assert extract_prose_jobs(pages(fee=FEE+'Outra TAXA: R$ 50,00.'))[2]
    p=pages();p[1].page_number=4
    assert extract_prose_jobs(p)[2]


def test_profile_split_between_pages_keeps_both_evidences():
    split=PROFILES.index('REMUNERAÇÃO:')
    p=[PageText(artifact_id='art-ev',page_number=i+1,text=t) for i,t in enumerate(
        [PROFILES[:split],PROFILES[split:],MATRIX,FEE])]
    jobs,ev,error=extract_prose_jobs(p)
    assert len(jobs)==2 and not error
    assert {page.page_number for page,_ in ev}=={1,2,3,4}
