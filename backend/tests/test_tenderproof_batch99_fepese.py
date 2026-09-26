import json
from pathlib import Path
import pytest
from bs4 import BeautifulSoup
from app.tenderproof.batch99_fepese_adapter import FepeseAdapter
from app.tenderproof.contracts import DocumentCandidate
from app.tenderproof.security import DestinationBlocked
OWN=Path(__file__).parent/'fixtures/tenderproof_batch99_own'
FIX=Path(__file__).parent/'fixtures/tenderproof_batch99_fepese'


def test_sap_observed_legacy_host_and_six_addenda():
    a=FepeseAdapter();c=a.candidate_from_url('https://sap.fepese.org.br')
    tab=BeautifulSoup((FIX/'sap-tab.html').read_bytes(),'lxml')
    docs=a.documents('<section id="fepese-document-tab">'+str(tab)+'</section>',c)
    assert len(docs)==7
    assert sum(d.kind=='retificacao' for d in docs)==6
    assert sum(d.kind=='edital' for d in docs)==1
    assert c.external_id=='sap'
    with pytest.raises((ValueError,DestinationBlocked)):
        a.candidate_from_url('https://uninspected.fepese.org.br')

def captured(root,manifest,kind=None):
    rows=json.loads((root/manifest).read_text(encoding='utf-8'))['pages']
    row=next(r for r in rows if r['source']=='fepese_open' and (kind is None or r['kind']==kind))
    return row['url'],(root/row['file']).read_text(encoding=row['encoding'])

def pairs():
    result=[]
    for root,manifest,kind,tabroot,tabmanifest,tabkind in [(OWN,'observed-details-manifest.json','detail0',OWN,'observed-components-manifest.json','document-tab0'),(OWN,'observed-samples-manifest.json','detail1',FIX,'manifest.json',None),(FIX,'third-manifest.json',None,FIX,'third-tab-manifest.json',None)]:
        # Locate existing parent manifests by observed kind instead of guessing.
        if root==OWN:
            manifest=next(p.name for p in OWN.glob('*manifest.json') if any(r.get('source')=='fepese_open' and r.get('kind')==kind for r in json.loads(p.read_text(encoding='utf-8')).get('pages',[])))
        if tabroot==OWN:
            tabmanifest=next(p.name for p in OWN.glob('*manifest.json') if any(r.get('source')=='fepese_open' and r.get('kind')==tabkind for r in json.loads(p.read_text(encoding='utf-8')).get('pages',[])))
        yield captured(root,manifest,kind),captured(tabroot,tabmanifest,tabkind)

def test_three_real_manifests_acquire_consolidated_without_calling_it_original():
    a=FepeseAdapter();listing=(OWN/'fepese_open-listing0.html').read_text(encoding='utf-8')
    page=a.parse_listing(listing,a.listing_urls[0],100)
    assert len(page.candidates)==13 and not page.terminal_evidence
    assert not any('fora dos subdomínios' in d for d in page.diagnostics)
    assert a.parse_listing(listing,a.listing_urls[0],1).truncated
    for (url,home),(taburl,tab) in pairs():
        c=next(c for c in page.candidates if c.detail_url_observed==url)
        assert a.detail_resource_urls(home,url)==[taburl]
        composed=a.compose_detail(home,url,[{'url':taburl,'body':tab}])
        a.confirm_identity(c,composed,url)
        docs=a.documents(composed,c)
        assert len(docs)>=2 and not any(d.kind=='edital' for d in docs)
        assert any(d.title.startswith('Edital') and '_TR01.pdf' in d.url_requested for d in docs)
        chosen=a.choose_document(docs)
        assert chosen.kind == 'consolidado'
        assert 'revisão antes da publicação' in chosen.reason_chosen
        assert any(d.kind == 'retificacao' for d in docs)
        with pytest.raises(ValueError):a.documents(home,c)

def test_source_resource_cross_identity_and_empty():
    a=FepeseAdapter();(url,home),(taburl,tab)=next(pairs());c=a.candidate_from_url(url)
    with pytest.raises(ValueError):a.validate_detail_resource_url(taburl.replace('2026pseducasj','2026seletivocomcap'),c)
    with pytest.raises(ValueError):a.compose_detail(home,url,[{'url':taburl,'body':tab.replace('2026 - Munic','2099 - Other')}])
    with pytest.raises(ValueError):a.compose_detail(home,url,[])
    with pytest.raises((ValueError,DestinationBlocked)):a.validate_detail_url('https://attacker.fepese.org.br/')
    p=a.parse_listing('<p>Sem elementos</p>',a.listing_urls[0]);assert not p.empty_evidence
    with pytest.raises(ValueError):a.parse_listing('x'*(2*1024*1024+1),a.listing_urls[0])


def test_controlled_original_ambiguous_and_wrong_document():
    a=FepeseAdapter();(url,home),(taburl,tab)=next(pairs());c=a.candidate_from_url(url)
    # Controlled parser counterexample only; this unretified URL is not captured
    # or requested, and is never included in the live evidence.
    controlled=tab.replace('_TR01.pdf','_Original.pdf')
    docs=a.documents(a.compose_detail(home,url,[{'url':taburl,'body':controlled}]),c)
    chosen=a.choose_document(docs)
    assert chosen.kind=='edital'
    with pytest.raises(ValueError):a.choose_document(docs+[DocumentCandidate(doc_id='ambiguous',title='Edital 006/2026',url_requested=chosen.url_requested+'&other=1',kind='edital')])
    with pytest.raises(ValueError):a.validate_document_url(chosen.url_requested.replace('2026pseducasj','2026cpcelesc'),c)
    with pytest.raises(ValueError):a.validate_document_url(chosen.url_requested+'&arquivo=other.pdf',c)
    with pytest.raises(ValueError):a.validate_detail_resource_url(taburl.replace('edital=1','edital=0'),c)


@pytest.mark.parametrize('url', [
    'https://2027nova.fepese.org.br.attacker.com/',
    'https://2027nova.attacker.fepese.org.br/',
    'https://2027nova.fepese.org.br:8443/',
    'https://user:pass@2027nova.fepese.org.br/',
    'http://2027nova.fepese.org.br/',
    'https://2027nova.fepese.org.br/../',
])
def test_discovery_family_keeps_destination_boundaries(url):
    with pytest.raises((ValueError, DestinationBlocked)):
        FepeseAdapter().validate_detail_url(url)


def test_new_contest_and_observed_tab_identifiers_are_not_frozen():
    a=FepeseAdapter()
    url='https://2027novoconcurso.fepese.org.br/'
    c=a.candidate_from_url(url, 'Prefeitura de Teste')
    tab=url+'?go=edital&mn='+'a'*32+'&edital=2'
    home=f'<title>Prefeitura de Teste</title><a href="{tab}">Edital</a>'
    assert a.detail_resource_urls(home,url)==[tab]
    a.validate_detail_resource_url(tab,c)
    with pytest.raises(ValueError):
        a.compose_detail(home,url,[{'url':tab.replace('edital=2','edital=3'),'body':'<title>Prefeitura de Teste</title>'}])
