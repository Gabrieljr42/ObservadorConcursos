import pytest
from app.tenderproof.fapeap_adapter import FapeapAdapter,ROOT,document_url

def test_program_document_roles_and_original():
    a=FapeapAdapter();url=ROOT+'pagina/programas/profix';c=a.candidate_from_url(url)
    html='<h1>PROFIX</h1><table>'+''.join('<tr><td>'+label+'</td><td><a href="https://matrix.amapa.gov.br//storage/submenus/66/files/'+file+'">Baixar</a></td></tr>' for label,file in [('EDITAL PROFIX','original.pdf'),('ANEXO I','annex.docx'),('Retificação do cronograma','amendment.pdf'),('Resultado do edital','result.pdf')])+'</table>'
    docs=a.documents(html,c)
    assert [d.kind for d in docs]==['edital','anexo','retificacao','outro']
    assert a.choose_document(docs).url_requested.endswith('/original.pdf')

@pytest.mark.parametrize('url',['https://matrix.amapa.gov.br//storage/','https://matrix.amapa.gov.br//storage/submenus/67/files/file.pdf','https://matrix.amapa.gov.br//storage/submenus/66/files/%252e%252e.pdf','https://matrix.amapa.gov.br//storage/submenus/66/files/file.pdf?x=1'])
def test_document_boundary_and_broken_links(url):
    with pytest.raises(ValueError):document_url(url)
