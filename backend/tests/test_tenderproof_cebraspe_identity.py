import pytest
from app.tenderproof.contracts import PageText,FieldState
from app.tenderproof.cebraspe_identity import masthead
from app.tenderproof.fields import extract_fields
from app.tenderproof.source_adapters import get_source_adapter
from test_tenderproof_evidence import _artifact


TEXT='''FUNDAÇÃO DE PESQUISA DO ESTADO EXEMPLO (ABC)
CONCURSO PÚBLICO PARA PROVIMENTO DE VAGAS
EDITAL Nº 7 – ABC, DE 2 DE JUNHO DE 2029
Inscrições: https://www.cebraspe.org.br/concursos/abc_29.
'''


def candidate():
    return get_source_adapter('cebraspe_open').candidate_from_url(
        'https://apis.cebraspe.org.br/cebraspe/eventos/ABC_29','AB C 29')


def pages(text=TEXT):
    return [PageText(artifact_id='art-ev',page_number=1,text=text)]


def test_acronym_full_header_year_and_event_url_corroborate_together():
    c=candidate();p=pages();h=masthead(c,p)
    assert h['orgao']=='FUNDAÇÃO DE PESQUISA DO ESTADO EXEMPLO'
    fields={f.field_name:f for f in extract_fields(candidate=c,artifact=_artifact(),pages=p)}
    for name in ('titulo','orgao'):
        assert fields[name].state==FieldState.SUPPORTED
        assert fields[name].evidence[0].snippet in TEXT
    assert fields['titulo'].original_value==h['snippet']
    assert get_source_adapter(c.source).document_identity_ids(c,p)=={'ABC_29'}


@pytest.mark.parametrize('old,new', [
    ('abc_29','xyz_29'),('abc_29','abc_28'),('(ABC)','(XYZ)'),
    ('– ABC,','– XYZ,'),('2029','2030'),
    ('cebraspe.org.br','evil.test'),('CONCURSO PÚBLICO','PROCESSO ESCOLAR'),
])
def test_identity_mismatch_never_supplies_title_or_issuer(old,new):
    assert masthead(candidate(),pages(TEXT.replace(old,new))) is None


def test_missing_url_other_explicit_id_and_wrong_candidate_title_are_rejected():
    assert masthead(candidate(),pages(TEXT.split('Inscrições:')[0])) is None
    assert masthead(candidate(),pages(TEXT+'https://www.cebraspe.org.br/concursos/xyz_29/')) is None
    assert masthead(candidate().model_copy(update={'title_observed':'XYZ 29'}),pages()) is None


def test_other_explicit_id_is_not_case_normalized_into_expected_contest():
    a=get_source_adapter('cebraspe_open')
    assert a.document_identity_ids(candidate(),pages(TEXT.replace('abc_29','xyz_29')))=={'xyz_29'}


MINISTRY='''1
MINISTÉRIO PÚBLICO DO ESTADO DE MINAS GERAIS
XIV CONCURSO PÚBLICO PARA O PROVIMENTO DE VAGAS
NO CARGO DE PROMOTOR
EDITAL Nº 3 – MPMG PROMOTOR, DE 4 DE MAIO DE 2031
Informações: https://www.cebraspe.org.br/concursos/mp_mg_31_promotor.
'''

def ministry_candidate():
    return get_source_adapter('cebraspe_open').candidate_from_url(
        'https://apis.cebraspe.org.br/cebraspe/eventos/MP_MG_31_PROMOTOR','MP MG 31 PROMOTOR')

def test_multi_part_event_code_requires_matching_notice_year_and_role():
    result=masthead(ministry_candidate(),pages(MINISTRY))
    assert result['orgao']=='MINISTÉRIO PÚBLICO DO ESTADO DE MINAS GERAIS'
    assert result['snippet'] in MINISTRY

@pytest.mark.parametrize('old,new',[
    ('MPMG PROMOTOR','MPPA PROMOTOR'),('MPMG PROMOTOR','MPMG TECNICO'),
    ('2031','2030'),('mp_mg_31_promotor','mp_mg_31_tecnico'),
    ('XIV CONCURSO PÚBLICO PARA','LISTA DE APROVADOS'),
])
def test_ministry_event_mismatch_cannot_confirm_issuer(old,new):
    assert masthead(ministry_candidate(),pages(MINISTRY.replace(old,new))) is None

def test_shared_job_section_reports_pending_association_with_evidence():
    text='2 DOS CARGOS DE PROMOTOR E DE PROMOTOR SUBSTITUTO\nREQUISITO: curso de Direito.\nSUBSÍDIO: R$ 9.000,00.'
    fields=extract_fields(candidate=ministry_candidate(),artifact=_artifact(),pages=pages(text))
    job=next(f for f in fields if f.field_name=='cargos')
    assert job.state==FieldState.FAILED and job.value is None
    assert job.evidence[0].snippet in text
