import pytest
from app.tenderproof.funcap_panels import parse_panels


def group(year,file):
    return f'<div class="bloco-ano-edital" id="bloco-ano-{year}"><table><tr class="linha-titulo-edital"><td><h4>Edital {year}</h4><a href="http://montenegro.funcap.ce.gov.br/sugba/index.php?cnpj=00078007000126&amp;id_solicitacao=8">Consulta</a></td></tr><tr class="linha-documento-edital"><td><a href="../edital/{file}.pdf">Edital {year}</a></td><td>01/02/{year}</td></tr></table></div>'


def test_reused_solicitation_does_not_merge_annual_documents_or_confirm_empty():
    html='<div class="editais-conteudo"><div class="box"><div class="title"><h5>Editais Abertos</h5></div></div><div class="box"><div class="title"><h5>Editais Encerrados</h5></div>'+group(2025,11)+group(2026,22)+'</div></div>'
    d=parse_panels(html)
    assert len(d['panels'])==2 and all(p['solicitation_id_reused'] for p in d['panels'])
    assert d['panels'][0]['documents'][0]['url'].endswith('/11.pdf')
    assert d['panels'][1]['documents'][0]['url'].endswith('/22.pdf')
    assert not d['sections'][0]['empty_confirmed'] and not d['coverage_complete']
    with pytest.raises(ValueError):parse_panels(html.replace('../edital/11.pdf','https://foreign.test/edital/11.pdf'))
    with pytest.raises(ValueError):parse_panels(html.replace('01/02/2025','31/02/2025'))
