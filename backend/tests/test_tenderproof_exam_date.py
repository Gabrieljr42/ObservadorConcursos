import hashlib
import pytest
from app.tenderproof.contracts import PageText, FieldState
from app.tenderproof.fields import extract_fields
from test_tenderproof_evidence import _candidate, _artifact


def field(text):
    return next(f for f in extract_fields(candidate=_candidate(),artifact=_artifact(),
        pages=[PageText(artifact_id='art-ev',page_number=15,text=text)]) if f.field_name=='prova_data')


def test_date_first_timetable_keeps_original_evidence():
    text='16 de novembro de 2026 Divulgação do local de prova\n29 de novembro de 2026 Aplicação da prova objetiva;\nDivulgação do gabarito preliminar às 22h.'
    f=field(text)
    assert f.value=='2026-11-29' and f.state==FieldState.SUPPORTED
    assert f.original_value=='29 de novembro de 2026'
    assert f.evidence[0].snippet in text and f.evidence[0].page_number==15


@pytest.mark.parametrize('text',[
    '29/11/2026 Divulgação do local de aplicação da prova objetiva',
    '29/11/2026 Recurso contra aplicação da prova objetiva',
    '29/11/2026 Aplicação da prova prática',
    '29/11/2026 Aplicação da prova objetiva para o cargo de Médico',
])
def test_other_events_and_scoped_dates_do_not_become_a_global_exam_date(text):
    assert field(text).state!=FieldState.SUPPORTED


def test_multiple_dates_remain_conflicting():
    f=field('29/11/2026 Aplicação da prova objetiva\n30/11/2026 Aplicação da prova objetiva')
    assert f.state==FieldState.CONFLICT and f.value is None and len(f.evidence)==2


def test_invalid_published_date_is_not_absent():
    assert field('31/02/2026 Aplicação da prova objetiva').state==FieldState.FAILED


from test_tenderproof_publication import env, proposal, apply, PDF_PAGE_1
from app.tenderproof.demo_pdf import make_text_pdf
from app.tenderproof.pdf_text import extract_pages


def test_exam_date_revalidates_publishes_and_versions(env):
    db,_,_,contest,run,store=env
    content=make_text_pdf([PDF_PAGE_1,'29/11/2026 Aplicação da prova objetiva'])
    run.artifact.sha256=hashlib.sha256(content).hexdigest()
    run.artifact.byte_len=len(content)
    store.save_artifact_file(run.artifact,content)
    pages,*_=extract_pages(content,artifact_id=run.artifact.artifact_id)
    run.fields=extract_fields(candidate=run.candidates[0],artifact=run.artifact,pages=pages)
    p=proposal(env,fields=('prova_data',))
    result=apply(env,p)
    db.refresh(contest)
    assert contest.prova_data.date().isoformat()=='2026-11-29'
    assert 'prova_data' in result['result']['diff']
    assert apply(env,p)['version_id']==result['version_id']
