from app.connectors.base import CandidateItem
from app.connectors.dedicated.national import (
    CesgranrioConnector,
    FCCConnector,
    FEPESEConnector,
    GenericDedicatedBancaConnector,
    QuadrixConnector,
)


def test_quadrix_uses_current_open_feed_only():
    connector = QuadrixConnector()
    assert connector.list_url.endswith('/index/abertos/')


def test_fcc_candidate_limit_covers_current_official_listing():
    assert FCCConnector.max_candidates >= 37


def test_fcc_excludes_cfp_certification_entries_from_personnel_scope(monkeypatch):
    connector = FCCConnector()
    monkeypatch.setattr(
        GenericDedicatedBancaConnector,
        '_fetch_candidates',
        lambda self: [
            CandidateItem(None, 'https://www.concursosfcc.com.br/concursos/plane226/index.html'),
            CandidateItem(None, 'https://www.concursosfcc.com.br/concursos/pompi126/index.html'),
        ],
    )

    candidates = connector._fetch_candidates()

    assert [candidate.detail_url for candidate in candidates] == [
        'https://www.concursosfcc.com.br/concursos/pompi126/index.html',
    ]
    assert connector.run_data.diagnostics_payload['rejection_counts'] == {'non_personnel': 1}


def test_cesgranrio_compact_registration_range_is_not_inverted(monkeypatch):
    import app.connectors.dedicated.national as national

    connector = CesgranrioConnector()
    monkeypatch.setattr(
        national,
        'extract_pdf_fields_if_possible',
        lambda *args, **kwargs: (
            {'ok': False, 'url': None, 'error': None, 'pages': None, 'text_hash': None},
            {
                'cargo': None, 'area': None, 'cidade': None, 'uf': None, 'vagas': None,
                'salario_min': None, 'salario_max': None, 'escolaridade': None,
                'taxa': None, 'prova_data': None, 'raw_pdf_fields': {},
            },
            None,
            None,
        ),
    )

    parsed = connector._parse_detail(
        CandidateItem(
            title_hint='Concurso Transpetro 2026',
            detail_url='https://www.cesgranrio.org.br/concurso/transpetro-2026/',
            status_hint='Em andamento',
        ),
        '<html><body><h1>Concurso Transpetro 2026</h1>'
        '<p>281 vagas</p><p>29/11/2026</p><p>INSCRIÇÕES</p>'
        '<p>12/08 a 14/09/2026</p><p>Taxa de inscrição</p>'
        '<p>Médio: R$ 81,50</p><p>Superior: R$ 117,00</p></body></html>',
        client=None,
    )

    assert parsed is not None
    assert parsed['inscricao_inicio'].isoformat().startswith('2026-08-12')
    assert parsed['inscricao_fim'].isoformat().startswith('2026-09-14')
    assert parsed['taxa'] == 81.5


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
