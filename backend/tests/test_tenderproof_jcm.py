import httpx
import pytest

from app.tenderproof.http_driver import BoundedHTTPDriver
from app.tenderproof.source_adapters import get_source_adapter
from app.tenderproof.security import DestinationBlocked, TenderProofSettings


def test_jcm_discovers_new_ids_and_observed_active_tab_with_accents(monkeypatch):
    monkeypatch.setattr('app.tenderproof.http_driver._public_dns', lambda host: None)
    a = get_source_adapter('jcm_open')
    html = '''<h3><a href="/informacoes/91234/">Câmara de Conceição</a></h3>
    <a href="/index/1/">Em andamento</a><a href="/index/3/">Finalizado</a>'''
    client = httpx.Client(transport=httpx.MockTransport(lambda req:
        httpx.Response(200, content=html.encode('iso-8859-1'))))
    driver = BoundedHTTPDriver(a.source, TenderProofSettings(allowlist_hosts=a.allowed_hosts), client=client)
    try:
        page = a.parse_listing(driver.open_listing(a.listing_urls[0]), a.listing_urls[0])
        assert page.candidates[0].external_id == '91234'
        assert page.candidates[0].title_observed == 'Câmara de Conceição'
        assert page.next_urls == ['https://concursos.concursosjcm.com.br/index/1/',
                                  'https://concursos.concursosjcm.com.br/index/3/']
        assert page.terminal_evidence is None
    finally:
        driver.close()


def test_jcm_documents_are_bound_to_contest_and_tenant():
    a = get_source_adapter('jcm_open')
    c = a.candidate_from_url('https://concursos.concursosjcm.com.br/informacoes/91234/')
    url = 'https://anexos-r2.selecao.net.br/uploads/17/concursos/91234/anexos/new-file.pdf'
    docs = a.documents(f'<a href="{url}">Edital 03/07/2029</a>', c)
    assert len(docs) == 1 and docs[0].kind == 'edital'
    for wrong in (url.replace('/17/', '/18/'), url.replace('/91234/', '/91235/'), url+'?x=1'):
        with pytest.raises((ValueError, DestinationBlocked)):
            a.validate_document_url(wrong, c)


def test_jcm_updated_notice_and_amendment_keep_review_required():
    a = get_source_adapter('jcm_open')
    c = a.candidate_from_url('https://concursos.concursosjcm.com.br/informacoes/91234/')
    prefix = 'https://anexos-r2.selecao.net.br/uploads/17/concursos/91234/anexos/'
    docs = a.documents(f'<a href="{prefix}main.pdf">Edital - Retificado 19/06/2029</a>'
                       f'<a href="{prefix}change.pdf">Retificação 03 ao Edital 20/06/2029</a>', c)
    assert [d.kind for d in docs] == ['consolidado', 'retificacao']
    assert a.choose_document(docs).kind == 'consolidado'


def test_jcm_observed_pagination_and_empty_tabs():
    a = get_source_adapter('jcm_open')
    url = 'https://concursos.concursosjcm.com.br/index/3/'
    page = a.parse_listing('<a href="?&ord=&dir=&pg=25&q=&pp=10">Última</a>', url)
    assert page.next_urls == [url+'?&ord=&dir=&pg=25&q=&pp=10']
    for query in ('?pg=2', '?ord=&dir=&pg=0&q=&pp=10',
                  '?ord=&dir=&pg=2&q=busca&pp=10', '?ord=&dir=&pg=2&q=&pp=100',
                  '?ord=&dir=&pg=2&pg=3&q=&pp=10'):
        with pytest.raises(ValueError): a.validate_listing_url(url+query)
    for tab in ('4', '5'):
        empty = a.parse_listing('<p class="nenhum">Nenhum item cadastrado.</p>',
                               url.replace('/3/', f'/{tab}/'))
        assert empty.empty_evidence == 'Nenhum item cadastrado.'
        assert empty.terminal_evidence
