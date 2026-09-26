import pytest
import httpx
from app.tenderproof.idib_adapter import IdibAdapter
from app.tenderproof.http_driver import BoundedHTTPDriver

URL='https://concurso.idib.org.br/Concurso.aspx?ID=365'
DOC='https://concurso.idib.org.br/ConcursoDownloadArquivo.aspx?ID2=1&ID=edital.pdf'


def test_listing_discovers_dynamic_ids_excludes_completed_and_enforces_limit():
    a=IdibAdapter()
    html='<span id="LBL_ConcursoAberto"><a href="/Concurso.aspx?ID=987">Concurso Prefeitura de Exemplo</a></span><span id="LBL_ConcursoAndamento"><a href="/Concurso.aspx?ID=654">Concurso Prefeitura de Outra Cidade</a></span><span id="LBL_ConcursoConcluido"><a href="/Concurso.aspx?ID=123">Realizado</a></span>'
    p=a.parse_listing(html,a.listing_urls[0]);assert {c.external_id for c in p.candidates}=={'987','654'}
    assert a.parse_listing(html,a.listing_urls[0],1).truncated
    assert p.terminal_evidence is None


def test_missing_section_is_not_empty():
    with pytest.raises(ValueError):IdibAdapter().parse_listing('<html></html>',IdibAdapter().listing_urls[0])


def test_document_types_and_header_reference():
    a=IdibAdapter();c=a.candidate_from_url(URL)
    docs=a.documents(f'<a href="{DOC}">EDITAL Nº 01/2026</a><a href="{DOC.replace("edital.pdf","aditivo.pdf")}">ADITIVO AO EDITAL</a>',c)
    assert [d.kind for d in docs]==['edital','retificacao']
    assert a.document_request_headers(DOC,c)=={'Referer':URL}


@pytest.mark.parametrize('suffix',['ID2=1&ID=../edital.pdf','ID2=2&ID=edital.pdf','ID2=1&ID=edital.pdf&token=1'])
def test_invalid_download_query_refused(suffix):
    a=IdibAdapter()
    with pytest.raises(ValueError):a.validate_document_url(DOC.split('?')[0]+'?'+suffix,a.candidate_from_url(URL))


def test_driver_decodes_utf8_and_sends_exact_observed_referer(monkeypatch):
    from app.tenderproof import http_driver
    monkeypatch.setattr(http_driver,'_public_dns',lambda host:None)
    def handler(request):
        if str(request.url)==URL:return httpx.Response(200,content='<meta charset="iso-8859-1">Inscrições'.encode('utf-8'))
        assert request.headers['Referer']==URL
        return httpx.Response(200,content=b'%PDF-1.4\nbytes')
    d=BoundedHTTPDriver('idib_open',client=httpx.Client(transport=httpx.MockTransport(handler)))
    try:
        assert 'Inscrições' in d.open_detail(URL)
        assert d.download(DOC,max_bytes=1000).content.startswith(b'%PDF-')
    finally:d.close()
