import pytest
from app.tenderproof.contracts import TARGET_FIELDS, PageText, ExtractedField, FieldState
from app.tenderproof.fields import extract_fields
from app.tenderproof.compare import compare
from test_tenderproof_publication import env


@pytest.mark.parametrize('texts',[[],[''],[' \n\t','\u00a0']])
def test_unreadable_document_is_extraction_failure_not_unpublished(env,texts):
    run=env[4]
    fields=extract_fields(candidate=run.candidates[0],artifact=run.artifact,
        pages=[PageText(artifact_id=run.artifact.artifact_id,page_number=i+1,text=text) for i,text in enumerate(texts)])
    assert {f.field_name for f in fields}==set(TARGET_FIELDS)
    assert all(f.state==FieldState.FAILED and f.value is None and not f.evidence for f in fields)
    result=compare(baseline_collected_at=None,baseline_origin='fixture',baseline={'orgao':'Órgão previamente cadastrado'},fields=fields)
    organization=next(f for f in result.fields if f.field_name=='orgao')
    assert organization.baseline_value=='Órgão previamente cadastrado'
    assert 'não significa' in organization.explanation and organization.tenderproof_state==FieldState.FAILED


def test_readable_text_and_conflicting_values_keep_distinct_states(env):
    run=env[4]
    fields=extract_fields(candidate=run.candidates[0],artifact=run.artifact,
        pages=[PageText(artifact_id=run.artifact.artifact_id,page_number=1,text='Sem cronograma de inscrição neste trecho.')])
    assert next(f for f in fields if f.field_name=='inscricao_fim').state==FieldState.UNKNOWN
    result=compare(baseline_collected_at=None,baseline_origin='fixture',baseline={},fields=[ExtractedField(field_name='inscricao_fim',state=FieldState.CONFLICT)])
    assert 'conflitantes' in next(f for f in result.fields if f.field_name=='inscricao_fim').explanation

