"""Official HTML fixtures and explicitly controlled negative perturbations."""
import hashlib
import json
from pathlib import Path
import pytest
from bs4 import UnicodeDammit
from app.tenderproof.batch30_edital_adapters import BATCH30_EDITAL_ADAPTERS
from app.tenderproof.source_adapters import SourcePageBlocked

ROOT=Path(__file__).parent/'fixtures/tenderproof_batch30_edital'
MANIFEST=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))


def html(source, kind='listing'):
    row=next(r for r in MANIFEST['pages'] if r['source']==source and r['kind']==kind)
    raw=(ROOT/row['file']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==row['sha256']
    return row['url'],UnicodeDammit(raw,is_html=True).unicode_markup


@pytest.mark.parametrize('adapter',BATCH30_EDITAL_ADAPTERS,ids=lambda a:a.source)
def test_official_listing_detail_identity_and_partial_coverage(adapter):
    url,body=html(adapter.source)
    page=adapter.parse_listing(body,url,1000)
    assert len(page.candidates)==({'aguia_open':28,'idecan_open':5}[adapter.source])
    assert not page.terminal_evidence
    detail_url,detail=html(adapter.source,'detail')
    candidate=next(c for c in page.candidates if c.detail_url_observed==detail_url)
    adapter.confirm_identity(candidate,detail,detail_url)
    with pytest.raises(ValueError):
        adapter.confirm_identity(candidate.model_copy(update={'external_id':'999999'}),detail,detail_url)
    docs=adapter.documents(detail,candidate)
    if adapter.source=='aguia_open':
        selected=adapter.choose_document(docs)
        assert selected.title=='EDITAL DE ABERTURA'
        assert '/edital/1/43/' in selected.url_requested
        assert not any('termos.pdf' in d.url_requested or 'politicas.pdf' in d.url_requested for d in docs)
        with pytest.raises(ValueError):
            adapter.validate_document_url(selected.url_requested.replace('/43/','/42/'),candidate)
    else:
        assert 'Nenhum arquivo postado' in detail
        assert docs==[]
        with pytest.raises(ValueError,match='nenhum documento'):
            adapter.choose_document(docs)


@pytest.mark.parametrize('adapter',BATCH30_EDITAL_ADAPTERS,ids=lambda a:a.source)
def test_limits_empty_and_challenges_never_claim_complete(adapter):
    url,body=html(adapter.source)
    limited=adapter.parse_listing(body,url,1)
    assert limited.truncated and not limited.terminal_evidence
    empty=adapter.parse_listing('<main>Nenhum concurso encontrado</main>',url)
    assert not empty.empty_evidence and not empty.terminal_evidence
    with pytest.raises(SourcePageBlocked):
        adapter.parse_listing('<main>Just a moment</main>',url)


@pytest.mark.parametrize('label',['EDITAL DAS INSCRIÇÕES DEFERIDAS','EDITAL DA AVALIAÇÃO DE TÍTULOS','EDITAL DE ABERTURA RETIFICADO','EDITAL DE CONVOCAÇÃO'])
def test_aguia_nonopening_notice_is_not_promoted(label):
    adapter=BATCH30_EDITAL_ADAPTERS[0]
    url,body=html(adapter.source)
    detail_url,detail=html(adapter.source,'detail')
    candidate=next(c for c in adapter.parse_listing(body,url,1000).candidates if c.detail_url_observed==detail_url)
    controlled=detail.replace('EDITAL DE ABERTURA',label)
    with pytest.raises(ValueError):
        adapter.choose_document(adapter.documents(controlled,candidate))
