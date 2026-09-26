import json
from pathlib import Path
import pytest
from app.tenderproof.batch99_fepese_adapter import FepeseAdapter
from app.tenderproof.contracts import PageText
from app.tenderproof.validation import validate_identity,document_identity_ids

HEADINGS=json.loads((Path(__file__).parent/'fixtures/tenderproof_batch99_fepese/concordia-headings.json').read_text(encoding='utf-8'))
LABELS={1:'Concurso Público – Educação – Edital 001/2025',
        2:'Concurso Público – Administração – Edital 002/2025',
        3:'Concurso Público – IPRECON – Edital 001/2025'}


def candidate(i):
    c=FepeseAdapter().candidate_from_url(f'https://2025cpconcordia.fepese.org.br/?go=home&edital={i}',
                                        '2025 – Prefeitura Municipal de Concórdia')
    return c.model_copy(update={'selection_label_observed':LABELS[i]})


def pages(i,text=None):
    text=HEADINGS[i-1]['text'] if text is None else text
    return [PageText(artifact_id='official-heading',page_number=1,text=text,char_count=len(text))]


@pytest.mark.parametrize('selection',[1,2,3])
@pytest.mark.parametrize('document',[1,2,3])
def test_real_mastheads_reject_every_cross_selection_pdf(selection,document):
    c=candidate(selection);p=pages(document)
    result=validate_identity(candidate=c,pages=p,document_title='Edital',document_url='https://2025cpconcordia.fepese.org.br')
    assert result.status.value==('valid' if selection==document else 'wrong_contest')
    assert (document_identity_ids(FepeseAdapter(),c,p)=={c.external_id})==(selection==document)


@pytest.mark.parametrize('label',[None,'Concurso Público – Edital 001/2025','Concurso Público – Educação – Edital 002/2025'])
def test_label_requires_distinctive_scope_and_matching_number(label):
    c=candidate(1).model_copy(update={'selection_label_observed':label})
    assert document_identity_ids(FepeseAdapter(),c,pages(1))!={c.external_id}


def test_later_scope_mention_cannot_rescue_wrong_masthead():
    c=candidate(1)
    text=HEADINGS[2]['text']+'\nEducação Edital 001/2025'
    assert document_identity_ids(FepeseAdapter(),c,pages(3,text))!={c.external_id}


def test_different_host_in_pdf_cannot_be_rescued_by_title():
    c=candidate(1)
    text=HEADINGS[0]['text'].replace('2025cpconcordia','2025other')
    assert document_identity_ids(FepeseAdapter(),c,pages(1,text))!={c.external_id}
