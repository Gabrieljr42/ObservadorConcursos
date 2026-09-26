"""Registration clauses and counterexamples from observed document structures."""
import pytest
from app.tenderproof.contracts import PageText, FieldState
from app.tenderproof.fields import extract_fields
from test_tenderproof_evidence import _candidate, _artifact


def dates(text):
    fields = extract_fields(candidate=_candidate(), artifact=_artifact(),
        pages=[PageText(artifact_id='art-ev', page_number=3, text=text, char_count=len(text))])
    return [f for f in fields if f.field_name in ('inscricao_inicio', 'inscricao_fim')]


@pytest.mark.parametrize('clause,start,end', [
    ('As inscrições deverão ser realizadas exclusivamente via internet, na página de acompanhamento do certame\nno site: www.access.org.br, a partir das 14h00min do dia 31 de agosto de 2026 até às 23h59min do dia 8 de\noutubro de 2026.', '2026-08-31', '2026-10-08'),
    ('As inscrições poderão ser realizadas a partir do dia 25/08/2026 até as 15h59 do dia 08/09/2026.', '2026-08-25', '2026-09-08'),
    ('As inscrições serão efetuadas exclusivamente via internet no endereço eletrônico\nhttps://portal.fenix.selecao.site/, no período compreendido entre as 10h00min do dia 21 de agosto de 2026 até\nas 10h00min do dia 04 de setembro de 2026, observando o horário de Brasília-DF.', '2026-08-21', '2026-09-04'),
    ('Inscrições estarão abertas de 1º de março de 2027 até 9/4/2027.', '2027-03-01', '2027-04-09'),
    ('Período de inscrições:\ndas 16 horas do dia 23 de julho de 2026 às 16 horas do dia 24 de agosto de 2026.', '2026-07-23', '2026-08-24'),
    ('Período de solicitação de inscrições\n15/5 a 19/6/2026\nDas 10 horas do primeiro dia às 18 horas do último dia', '2026-05-15', '2026-06-19'),
    ('Período de inscrições:\n2/8 até 3/9/2028', '2028-08-02', '2028-09-03'),
    ('8h do dia 14 de setembro de 2026 às \n16h do dia 14 de outubro de 2026 Período de inscrições ', '2026-09-14', '2026-10-14'),
    ('2/12/2028 a 3/1/2029 Período de inscrições', '2028-12-02', '2029-01-03'),
    ('Período de solicitação de inscrição e de solicitação\nde isenção de taxa de inscrição\n24/8 a 22/9/2022\nÚltimo dia para pagamento 13/10/2022', '2022-08-24', '2022-09-22'),
])
def test_registration_dates_preserve_original_text(clause,start,end):
    result=dates(clause)
    assert [f.value for f in result]==[start,end]
    for field in result:
        assert field.state==FieldState.SUPPORTED
        assert field.original_value in clause
        assert field.evidence[0].snippet in clause
        assert field.evidence[0].page_number==3


@pytest.mark.parametrize('text', [
    'Para isenção, as inscrições serão realizadas de 1 de março de 2027 até 5 de março de 2027.',
    'As inscrições serão realizadas de 1 de março de 2027. O pagamento será aceito até 5 de março de 2027.',
    'As inscrições poderão ser realizadas de 31 de fevereiro de 2027 até 5 de março de 2027.',
    'As inscrições serão realizadas em 1 de março de 2027. A divulgação está prevista para 5 de março de 2027.',
    'Período de inscrições: 23 de julho de 2026. Prova em 24 de agosto de 2026.',
    'Período de inscrições: 23 de julho de 2026. Pagamento até 24 de agosto de 2026.',
    'Período de solicitação de isenção de taxa de inscrição\n15/5 a 19/6/2026',
    'Período de pagamento das inscrições\n15/5 a 19/6/2026',
    'Período de inscrições\n31/2 a 19/6/2026',
    'Período de inscrições\n15/12 a 19/1/2026',
    'Período de inscrições\nProva objetiva\n15/5 a 19/6/2026',
    '2/12/2028 a 3/1/2029 Período de inscrições para isenção',
    '2/12/2028 a 3/1/2029 Prazo de pagamento\nPeríodo de inscrições',
    '2/12/2028 a\nProva objetiva\n3/1/2029 Período de inscrições',
    '31 de fevereiro de 2028 a 3 de março de 2028 Período de inscrições',
])
def test_unrelated_or_invalid_dates_never_become_supported(text):
    assert all(f.state!=FieldState.SUPPORTED for f in dates(text))


def test_differing_registration_clauses_preserve_both_evidences():
    text=('As inscrições serão realizadas de 1 de março de 2027 até 5 de março de 2027.\n'
          'As inscrições serão realizadas de 1 de março de 2027 até 6 de março de 2027.')
    for field in dates(text):
        assert field.state==FieldState.CONFLICT and field.value is None
        assert len(field.evidence)==2


def test_compact_row_conflicts_with_different_full_dates():
    text=('Período de solicitação de inscrições\n15/5 a 19/6/2026\n'
          'As inscrições serão realizadas de 15/5/2026 até 20/6/2026.')
    assert all(f.state==FieldState.CONFLICT and len(f.evidence)==2 for f in dates(text))


def test_date_first_row_preserves_conflicts_with_direct_clause():
    text = ('2/12/2028 a 3/1/2029 Período de inscrições\n'
            'As inscrições serão realizadas de 2/12/2028 até 4/1/2029.')
    assert all(f.state == FieldState.CONFLICT and len(f.evidence) == 2 for f in dates(text))


@pytest.mark.parametrize('flag,value',[('truncated',True),('error','page extraction failed')])
def test_damaged_registration_page_cannot_supply_supported_dates(flag,value):
    page=PageText(artifact_id='art-ev',page_number=3,text='Período de inscrições\n15/5 a 19/6/2026')
    page=page.model_copy(update={flag:value})
    result=extract_fields(candidate=_candidate(),artifact=_artifact(),pages=[page])
    assert all(f.state==FieldState.FAILED for f in result if f.field_name.startswith('inscricao_'))


def test_invalid_published_row_cannot_be_hidden_by_a_valid_period():
    text='Período de inscrições\n31/2 a 19/6/2026\nPeríodo de inscrições\n15/5 a 19/6/2026'
    assert all(f.state==FieldState.FAILED and len(f.evidence)==2 for f in dates(text))


@pytest.mark.parametrize('text,expected',[
    ('Aplicação da prova objetiva 15/1/2023','2023-01-15'),
    ('Divulgação dos locais de aplicação da prova objetiva 15/1/2023',None),
    ('Aplicação das provas discursivas 15 e 16/4/2023',None),
    ('Aplicação da prova objetiva 31/2/2023',None),
    ('Aplicação da prova objetiva 15/1/2023\n16/1/2023 Aplicação da prova objetiva',None),
])
def test_exam_event_first_is_exact_and_preserves_conflicts(text,expected):
    result=extract_fields(candidate=_candidate(),artifact=_artifact(),
        pages=[PageText(artifact_id='art-ev',page_number=3,text=text)])
    field=next(f for f in result if f.field_name=='prova_data')
    assert field.value==expected
    assert (field.state==FieldState.SUPPORTED)==bool(expected)


def test_published_prose_job_profiles_are_an_implementation_gap():
    text='2.1 CARGO 1: ANALISTA\nREQUISITOS: curso superior.\nREMUNERAÇÃO: R$ 5.000,00.'
    fields=extract_fields(candidate=_candidate(),artifact=_artifact(),
        pages=[PageText(artifact_id='art-ev',page_number=2,text=text)])
    jobs=next(f for f in fields if f.field_name=='cargos')
    assert jobs.state==FieldState.FAILED and jobs.value is None
    assert 'perfis de cargos em texto' in jobs.reason


@pytest.mark.parametrize('heading', ['CONCURSO PÚBLICO', 'PROCESSO SELETIVO', 'EDITAL'])
def test_issuer_does_not_include_adjacent_selection_heading(heading):
    text = f'MUNICÍPIO DE CUNHA PORÃ {heading} • EDITAL 001/2026'
    fields = extract_fields(candidate=_candidate(), artifact=_artifact(),
        pages=[PageText(artifact_id='art-ev', page_number=1, text=text, char_count=len(text))])
    issuer = next(f for f in fields if f.field_name == 'orgao')
    assert issuer.value == 'Município De Cunha Porã'
    assert issuer.state == FieldState.SUPPORTED
    assert issuer.evidence[0].snippet in text
