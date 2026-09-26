"""Dated official captures; changed inputs below are synthetic negative tests."""
from pathlib import Path
import json
import pytest
from app.tenderproof.batch30_institutional_adapters import UFUAdapter
from app.tenderproof.contracts import DiscoveredCandidate
from app.tenderproof.security import DestinationBlocked

ROOT=Path(__file__).parent/'fixtures/tenderproof_batch30_institutional'


def sample():
    adapter=UFUAdapter()
    listing=(ROOT/'ufu-ta-listing.html').read_text(encoding='utf-8')
    url='https://www.portalselecao.ufu.br/servicos/Edital/listar/concurso_ta'
    page=adapter.parse_listing(listing,url)
    candidate=next(c for c in page.candidates if c.external_id=='1781')
    detail=(ROOT/'ufu-ta-detail.html').read_text(encoding='utf-8')
    return adapter,listing,url,page,candidate,detail


def test_ufu_staff_scope_and_bounded_large_official_listing():
    adapter,_,_,page,_,_=sample()
    assert len(page.candidates)==19 and not page.terminal_evidence
    large=(ROOT/'ufu-listing.html').read_text(encoding='utf-8')
    page=adapter.parse_listing(large,adapter.listing_urls[0],5)
    assert len(page.candidates)==5 and page.truncated and not page.terminal_evidence
    assert all('Declaração' not in c.title_observed and c.title_observed!='DIRPS' for c in page.candidates)
    for title in ('Vestibular 2026','Bolsa de Iniciação Científica','Outros DIRPS','Aplicação de Provas - Pós e Docentes'):
        assert not adapter.in_scope(title,'')


def test_ufu_principal_differs_from_dou_and_retifications():
    adapter,_,_,_,candidate,detail=sample()
    adapter.confirm_identity(candidate,detail,candidate.detail_url_observed)
    docs=adapter.documents(detail,candidate)
    assert len(docs)==6
    chosen=adapter.choose_document(docs)
    assert chosen.title=='Edital de Processo'
    assert chosen.url_requested.endswith('/ac1aacca91030c5cdb835cad7f32b4c6')
    assert len([d for d in docs if d.kind=='edital'])==1
    with pytest.raises(ValueError):adapter.choose_document([chosen,chosen.model_copy(update={'doc_id':'other','url_requested':chosen.url_requested[:-1]+'7'})])


def test_ufu_synthetic_identity_mismatch_and_missing_share():
    adapter,_,_,_,candidate,detail=sample()
    with pytest.raises(ValueError):adapter.confirm_identity(candidate.model_copy(update={'external_id':'9999'}),detail,candidate.detail_url_observed)
    with pytest.raises(ValueError):adapter.confirm_identity(candidate.model_copy(update={'title_observed':'Concurso Polícia Militar Ceará 999/2030'}),detail,candidate.detail_url_observed)
    with pytest.raises(ValueError):adapter.confirm_identity(candidate,detail.replace('data-href=', 'data-missing='),candidate.detail_url_observed)
    with pytest.raises(ValueError):adapter.confirm_identity(candidate,detail.replace('/cronograma/1781','/cronograma/1782'),candidate.detail_url_observed)


def test_ufu_synthetic_destination_and_empty_guards():
    adapter,_,url,_,candidate,detail=sample()
    doc=adapter.choose_document(adapter.documents(detail,candidate))
    for bad in [doc.url_requested+'?next=1',doc.url_requested.replace('www.portalselecao.ufu.br','127.0.0.1'),doc.url_requested.replace('/ArquivoAdministrativo/','/Private/')]:
        with pytest.raises((ValueError,DestinationBlocked)):adapter.validate_document_url(bad,candidate)
    page=adapter.parse_listing('<main>Nenhum item</main>',url)
    assert not page.empty_evidence and not page.terminal_evidence
    with pytest.raises(ValueError):adapter.parse_listing('<main>Verify you are human</main>',url)


def test_ufu_observed_complementary_notices_require_joint_review():
    report_path=Path(__file__).resolve().parents[2]/'docs/tenderproof-batch30-ufu-live.json'
    report=json.loads(report_path.read_text(encoding='utf-8'))
    adapter=UFUAdapter()
    for attempt in report['cycles'][0]['attempts']:
        candidate=DiscoveredCandidate.model_validate(attempt['candidate'])
        detail=(ROOT/attempt['captures'][0]['file']).read_text(encoding='utf-8')
        docs=adapter.documents(detail,candidate)
        assert len([d for d in docs if d.kind=='edital'])==2
        with pytest.raises(ValueError,match='revisão documental conjunta'):
            adapter.choose_document(docs)
        # Missing one component cannot make the remaining one self-sufficient.
        with pytest.raises(ValueError,match='revisão documental conjunta'):
            adapter.choose_document([next(d for d in docs if d.kind=='edital')])
