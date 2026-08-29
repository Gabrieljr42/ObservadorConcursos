from app.connectors.dedicated.national import FEPESEConnector, QuadrixConnector


def test_quadrix_uses_current_open_feed_only():
    connector = QuadrixConnector()
    assert connector.list_url.endswith('/index/abertos/')


def test_fepese_discovers_current_canonical_subdomains(monkeypatch):
    html = '''
    <a href="https://2026cpcelesc.fepese.org.br">Concurso Público Celesc 2026</a>
    <a href="https://2026pseducasj.fepese.org.br">Processo Seletivo Magistério 2026</a>
    <a href="https://2026residencia.fepese.org.br">Residência Médica 2026</a>
    <a href="https://fepese.org.br/institucional">Institucional</a>
    '''
    connector = FEPESEConnector()
    monkeypatch.setattr(connector, '_fetch_html', lambda _: html)
    candidates = connector._fetch_candidates()
    assert [item.detail_url for item in candidates] == [
        'https://2026cpcelesc.fepese.org.br',
        'https://2026pseducasj.fepese.org.br',
    ]
