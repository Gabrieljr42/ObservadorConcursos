import json
import pytest

from app.tenderproof.faped_parser import parse_personnel


def link(name='Edital', file='new.pdf'):
    return f"<a href='files/uploads/document/{file}'><div class='file-block'><span>{name}</span><br>Publicado em 08/09/2026 13:20</div></a>"


def listing(identity=876):
    return f'''<div class="accordion-item"><div class="accordion-header"><h5 class="title">PROCESSO SELETIVO SIMPLIFICADO 04/2026</h5></div>
    <div class="accordion-body">Abertura: 08/09/2026<div id="docfor{identity}">{link()}</div></div></div>'''


def append(identity, fragment):
    return f"<script>app.id('docfor{identity}').innerHTML += {json.dumps(fragment)};</script>"


def test_literal_append_documents_stay_with_dynamic_selection_identity():
    html = listing() + append(876, link('Resultado', 'result.pdf')) + append(999, link('Outra seleção', 'foreign.pdf'))
    row = parse_personnel(html)[0]
    assert row['identity'] == '876'
    assert [d['title'] for d in row['documents']] == ['Edital', 'Resultado']
    assert row['documents'][1]['published_at_local'] == '2026-09-08T13:20:00'


@pytest.mark.parametrize('script', [
    "app.id('docfor876').innerHTML += buildDocuments();",
    "app.id('docfor876').innerHTML += \"text\"; otherCall();",
])
def test_computed_or_extra_statements_cannot_be_treated_as_observed_documents(script):
    with pytest.raises(ValueError): parse_personnel(listing() + '<script>' + script + '</script>')


@pytest.mark.parametrize('change', [
    lambda h: h.replace('new.pdf', '../../private.pdf'),
    lambda h: h.replace('files/uploads/document/new.pdf', 'https://other.test/new.pdf'),
    lambda h: h.replace('08/09/2026 13:20', '31/02/2026 13:20'),
    lambda h: h.replace('id="docfor876"', 'id="missing"'),
    lambda h: h.replace('PROCESSO SELETIVO SIMPLIFICADO', 'SELEÇÃO DE FORNECEDORES'),
])
def test_incomplete_unsafe_or_procurement_rows_are_rejected(change):
    with pytest.raises(ValueError): parse_personnel(change(listing()))


def test_missing_repeated_and_cross_selection_documents_fail_closed():
    with pytest.raises(ValueError): parse_personnel('<p>Indisponível</p>')
    with pytest.raises(ValueError): parse_personnel(listing() + listing())
    with pytest.raises(ValueError): parse_personnel(listing() + append(876, link()))
