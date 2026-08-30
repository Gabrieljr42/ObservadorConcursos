from bs4 import BeautifulSoup

from app.connectors.common import extract_city_uf, extract_pdf_link, parse_date_interval
from app.publications import parse_publications_from_dom


def test_city_uf_rejects_invalid_uf_and_narrative_fragment():
    assert extract_city_uf('conclusão da avaliação e - OU') == (None, None)
    assert extract_city_uf('Prefeitura Municipal de Carbonita/MG') == ('Carbonita', 'MG')
    assert extract_city_uf(
        'Concurso Público - Prefeitura Municipal de Papanduva - SC Prefeitura Municipal de Papanduva/SC'
    ) == ('Papanduva', 'SC')
    assert extract_city_uf('Vagas para: Americana/SP, Bauru/SP') == ('Americana', 'SP')


def test_pdf_link_prefers_opening_notice_and_rejects_noise():
    soup = BeautifulSoup('''<a href="/comunicado.pdf">Comunicado</a>
      <a href="/cronograma.pdf">Cronograma</a>
      <a href="/edital-abertura.pdf">Edital de Abertura</a>''', 'html.parser')
    assert extract_pdf_link(soup, 'https://example.test/edital') == 'https://example.test/edital-abertura.pdf'


def test_publications_dom_preserves_real_links_and_dates():
    soup = BeautifulSoup('''<section><h2>Publicações</h2>
      <div><a href="/docs/edital.pdf">Edital de Abertura</a><span>23/07/2026</span></div>
      <div><a href="/docs/gabarito.pdf">Gabarito Preliminar</a><span>01/08/2026</span></div>
    </section>''', 'html.parser')
    pubs = parse_publications_from_dom(soup, 'https://example.test/concursos/1', source='test')
    assert len(pubs) == 2
    assert pubs[0]['link'] == 'https://example.test/docs/edital.pdf'
    assert pubs[0]['publication_date'].startswith('2026-07-23')


def test_publications_dom_deduplicates_links_and_rejects_registration_noise():
    soup = BeautifulSoup('''<section><h2>Publicações</h2>
      <a href="/docs/edital.pdf">Edital</a>
      <a href="/docs/edital.pdf">Edital de Abertura 01/2026</a>
      <a href="/inscricao">Inscrição online - Edital 01/2026</a>
      <a href="/docs/resultado.pdf">Resultado Final</a>
    </section>''', 'html.parser')

    pubs = parse_publications_from_dom(soup, 'https://example.test/concursos/1', source='test')

    assert [pub['title'] for pub in pubs] == ['Edital de Abertura 01/2026', 'Resultado Final']


def test_date_interval_prefers_registration_period_over_prior_law_date():
    text = (
        'Nos termos da Lei Complementar nº 036, de 17 de março de 1995. '
        'Somente será admitida inscrição via Internet, no período de '
        '22 de julho de 2026 a 27 de agosto de 2026.'
    )

    start, end = parse_date_interval(text)

    assert start.isoformat().startswith('2026-07-22')
    assert end.isoformat().startswith('2026-08-27')


def test_date_interval_supports_shared_year_in_portal_range():
    start, end = parse_date_interval('INSCRIÇÕES ABERTAS DE 17 DE AGOSTO A 08 DE OUTUBRO DE 2026')

    assert start.isoformat().startswith('2026-08-17')
    assert end.isoformat().startswith('2026-10-08')


def test_date_interval_discards_legacy_unknown_date_sentinel():
    start, end = parse_date_interval('Período de Inscrições: 03/02/2020 - 00:00:00 a 01/01/0001 - 23:59:59')

    assert start.isoformat().startswith('2020-02-03')
    assert end is None
