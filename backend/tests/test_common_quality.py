from bs4 import BeautifulSoup

from app.connectors.common import extract_city_uf, extract_pdf_link
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
