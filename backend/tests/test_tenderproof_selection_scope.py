from types import SimpleNamespace
import pytest
from app.tenderproof.contracts import PageText
from app.tenderproof.selection_scope import document_scope

HEADER = 'EDITAL Nº 42/2033\nProcesso nº 999\nCHAMADA PÚBLICA PARA CONCESSÃO DE BOLSAS\nDE PESQUISA REGIONAL\nO Governo publica as regras.'
CLAUSE = '18.3 A assinatura do TCCB não caracteriza qualquer vínculo empregatício.'
ARTIFACT = SimpleNamespace(artifact_id='original', sha256='a'*64)


@pytest.mark.parametrize('method', ['pdf_text','ocr_tesseract'])
def test_scope_requires_documentary_contract_and_retains_exact_proof(method):
    pages=[PageText(artifact_id='original',page_number=1,text=HEADER,extraction_method=method),PageText(artifact_id='original',page_number=4,text=CLAUSE,extraction_method=method)]
    result=document_scope('fapern_selection',ARTIFACT,pages)
    assert result['classification']=='research_scholarship' and result['review_required']
    assert result['evidence'][1]['snippet'].endswith('DE PESQUISA REGIONAL')
    for evidence in result['evidence']:
        page=next(p for p in pages if p.page_number==evidence['page_number'])
        assert page.text[evidence['start']:evidence['end']]==evidence['snippet']
        assert evidence['document_sha256']==ARTIFACT.sha256
        assert evidence['extraction_method']==method


@pytest.mark.parametrize('header,clause', [
    (HEADER, ''),
    (HEADER.replace('BOLSAS','EMPREGOS'),CLAUSE),
    ('EDITAL Nº 42/2033\nBenefício bolsa de estudos para servidores.',CLAUSE),
    (HEADER+'\nEDITAL Nº 43/2033\nOUTRO ATO',CLAUSE),
    (HEADER, CLAUSE.replace('não caracteriza','caracteriza')),
    (HEADER, CLAUSE+'\n'+CLAUSE),
])
def test_weak_mixed_or_contradictory_signals_do_not_classify(header,clause):
    assert document_scope('fapern_selection',ARTIFACT,[PageText(artifact_id='original',page_number=1,text=header),PageText(artifact_id='original',page_number=4,text=clause)]) is None


def test_contract_is_not_assumed_for_other_sources_or_later_annexes():
    pages=[PageText(artifact_id='original',page_number=1,text=HEADER),PageText(artifact_id='original',page_number=4,text=CLAUSE)]
    assert document_scope('facepe_selection',ARTIFACT,pages) is None
    pages[0].page_number=2
    assert document_scope('fapern_selection',ARTIFACT,pages) is None
