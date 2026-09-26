import pytest
from app.tenderproof.fapesb_reda_adapter import FapesbRedaAdapter,LISTING

def tab(year,number=1):
    return f'<section id="reda-tab-{year}"><h4>PROCESSO SELETIVO SIMPLIFICADO – EDITAL Nº {number:02}/{year} – FAPESB</h4><a href="https://www.fapesb.ba.gov.br/wp-content/uploads/{year}/08/original.pdf">Edital de abertura</a><a href="https://www.fapesb.ba.gov.br/wp-content/uploads/{year}/08/errata.pdf">Errata</a></section>'

def test_all_published_years_and_numbers_without_frozen_file():
    a=FapesbRedaAdapter();html=tab(2026)+tab(2027,3);cs=a.parse_listing(html,LISTING).candidates
    assert len(cs)==2
    for c in cs:
        assert a.candidate_from_url(c.detail_url_observed).external_id==c.external_id
        assert [d.kind for d in a.documents(html,c)]==['edital','retificacao']

def test_old_original_cannot_match_changed_live_original():
    a=FapesbRedaAdapter();html=tab(2026);c=a.parse_listing(html,LISTING).candidates[0]
    with pytest.raises(ValueError):a.documents(html.replace('original.pdf','replacement.pdf'),c)

def test_mismatched_year_and_duplicate_tabs_rejected():
    a=FapesbRedaAdapter()
    for html in [tab(2026).replace('01/2026','01/2027'),tab(2026)+tab(2026)]:
        with pytest.raises(ValueError):a.parse_listing(html,LISTING)

def test_external_annex_is_pending_not_discarded():
    a=FapesbRedaAdapter();html=tab(2026).replace('</section>','<a href="https://outside.example/a.pdf">Anexo</a></section>');page=a.parse_listing(html,LISTING)
    assert page.truncated
    with pytest.raises(ValueError):a.documents(html,page.candidates[0])


def test_role_lists_and_errata_keep_their_published_section():
    html=tab(2027).replace('</section>', '''
    <p><strong>LISTAS DOS CANDIDATOS NEGROS</strong></p>
    <ul><li><a href="/wp-content/uploads/2027/08/negros.pdf">Administração</a></li></ul>
    <hr><strong>RESULTADO FINAL E HOMOLOGAÇÃO</strong>
    <ul><li><a href="/wp-content/uploads/2027/08/final.pdf">Administração</a></li>
    <li><p><strong><a href="/wp-content/uploads/2027/08/correction.pdf">Errata</a></strong></p></li></ul>
    </section>''')
    a=FapesbRedaAdapter();c=a.parse_listing(html,LISTING).candidates[0];docs=a.documents(html,c)
    by_url={d.url_requested:d for d in docs}
    assert by_url['https://www.fapesb.ba.gov.br/wp-content/uploads/2027/08/negros.pdf'].title=='LISTAS DOS CANDIDATOS NEGROS — Administração'
    assert by_url['https://www.fapesb.ba.gov.br/wp-content/uploads/2027/08/final.pdf'].title=='RESULTADO FINAL E HOMOLOGAÇÃO — Administração'
    correction=by_url['https://www.fapesb.ba.gov.br/wp-content/uploads/2027/08/correction.pdf']
    assert correction.title=='RESULTADO FINAL E HOMOLOGAÇÃO — Errata'
    assert correction.kind=='retificacao'
    assert a.choose_document(docs).title=='Edital de abertura'


def test_context_does_not_cross_separator_or_borrow_previous_list():
    html=tab(2028).replace('</section>', '''
    <strong>RESULTADO FINAL</strong><ul><li><a href="/wp-content/uploads/2028/08/result.pdf">Lista</a></li></ul>
    <hr><ul><li><a href="/wp-content/uploads/2028/08/unlabelled.pdf">Convocação</a></li></ul>
    <ul><li><a href="/wp-content/uploads/2028/08/another.pdf">Anexo</a></li></ul>
    </section>''')
    a=FapesbRedaAdapter();c=a.parse_listing(html,LISTING).candidates[0]
    docs=a.documents(html,c)
    assert docs[-2].title=='Convocação'
    assert docs[-1].title=='Anexo'
