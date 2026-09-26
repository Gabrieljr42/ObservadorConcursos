from app.tenderproof.contracts import PageText, FieldState
from app.tenderproof.fields import extract_fields
from app.tenderproof.job_tables import ordered_job_tables
from test_tenderproof_evidence import _candidate, _artifact

HEADER='Cargo Vagas Vencimentos Carga Horária Escolaridade e Exigências Taxa de\ninscrição\n'
ROW='MOTORISTA 1 + CR R$ 2.108,74\n40h semanais . Regime com\nhorário flexível conforme\nescala e necessidade do\nserviço.\nEnsino Fundamental Completo e\nCNH categoria D ou superior R$ 50,00\n'


def page(text):
    return PageText(artifact_id='art-ev',page_number=1,text=text,char_count=len(text))


def test_explicit_columns_distinguish_salary_fee_and_vacancies():
    text=HEADER+ROW+'3. DAS INSCRIÇÕES\n'
    fields=extract_fields(candidate=_candidate(),artifact=_artifact(),pages=[page(text)])
    jobs=next(f for f in fields if f.field_name=='cargos')
    assert jobs.state==FieldState.SUPPORTED
    assert jobs.value[0]['remuneracao']=='2108.74'
    assert jobs.value[0]['taxa_inscricao']=='50.00'
    assert jobs.value[0]['vagas_imediatas']==1 and jobs.value[0]['cadastro_reserva']
    assert 'CNH categoria D' in jobs.value[0]['requisitos']
    assert 'horário flexível' in jobs.value[0]['jornada']
    assert all(e.snippet in text for e in jobs.evidence)


def test_two_jobs_keep_separate_amounts():
    text=HEADER+ROW+ROW.replace('MOTORISTA','VIGIA').replace('1 + CR','CR').replace('2.108,74','1.950,00')+'3. DAS INSCRIÇÕES\n'
    rows,unresolved=ordered_job_tables([page(text)])
    assert not unresolved
    assert [(r[0]['nome'],r[0]['remuneracao'],r[0]['vagas_imediatas']) for r in rows]==[('MOTORISTA','2108.74',1),('VIGIA','1950.00',0)]


def test_unparsed_table_is_pending_implementation_not_absence():
    text=HEADER+ROW+'OUTRA LINHA NÃO INTERPRETADA\n3. DAS INSCRIÇÕES\n'
    fields=extract_fields(candidate=_candidate(),artifact=_artifact(),pages=[page(text)])
    jobs=next(f for f in fields if f.field_name=='cargos')
    assert jobs.state==FieldState.FAILED and jobs.value is None
    assert 'publicada' in jobs.reason


def test_different_column_order_and_missing_end_are_not_guessed():
    assert ordered_job_tables([page(HEADER.replace('Vencimentos','Taxa')+ROW)])[0]==[]
    rows,unresolved=ordered_job_tables([page(HEADER+ROW)])
    assert not rows and unresolved
