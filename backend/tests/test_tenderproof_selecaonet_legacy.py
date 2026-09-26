import pytest

from app.tenderproof.source_adapters import get_source_adapter
from app.tenderproof.security import DestinationBlocked


@pytest.mark.parametrize('host', ['anexos-r2.selecao.net.br', 'anexos.cdn.selecao.net.br'])
def test_legacy_and_current_cdn_keep_result_classification(host):
    adapter = get_source_adapter('abcp_open')
    candidate = adapter.candidate_from_url('https://abcp.selecao.net.br/informacoes/987654/')
    url = f'https://{host}/uploads/567/concursos/987654/anexos/resultado.pdf'
    docs = adapter.documents(f'<a href="{url}">EDITAL DE RESULTADO FINAL E HOMOLOGAÇÃO</a>', candidate)
    assert len(docs) == 1
    assert docs[0].kind == 'resultado'
    assert docs[0].url_requested == url


@pytest.mark.parametrize('url', [
    'https://anexos.cdn.selecao.net.br/uploads/568/concursos/987654/anexos/a.pdf',
    'https://anexos.cdn.selecao.net.br/uploads/567/concursos/987655/anexos/a.pdf',
    'https://anexos.cdn.selecao.net.br/uploads/567/concursos/987654/anexos/a.pdf?x=1',
    'https://anexos.cdn.selecao.net.br.evil.test/uploads/567/concursos/987654/anexos/a.pdf',
])
def test_legacy_cdn_rejects_other_identity_and_destination(url):
    adapter = get_source_adapter('abcp_open')
    candidate = adapter.candidate_from_url('https://abcp.selecao.net.br/informacoes/987654/')
    with pytest.raises((ValueError, DestinationBlocked)):
        adapter.validate_document_url(url, candidate)
