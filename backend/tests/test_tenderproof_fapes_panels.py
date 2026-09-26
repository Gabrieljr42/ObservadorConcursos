import pytest
from app.tenderproof.fapes_panels import parse_file_panels, discover_sections


def panel(number,title,url='/Media/fapes/Editais/novo.pdf'):
 return f'''<li class="panel"><div class="panel-heading" id="heading-{number}"><span class="paneltitle-value">{title}</span></div>
 <div id="collapse-{number}" aria-labelledby="heading-{number}"><table class="table-downloads"><tbody><tr>
 <th class="coluna-1"><a href="{url}">Edital {title}</a><span class="caption-value">Descrição {title}</span></th>
 <th><span class="dataatualizacao-value">08/09/2026</span></th></tr></tbody></table></div></li>'''


def test_panels_preserve_document_association_and_dynamic_ids():
 rows=parse_file_panels('<ul class="galeriade-arquivos">'+panel(778,'Primeira')+panel(990,'Segunda','/Media/fapes/Editais/outra.pdf')+'</ul>')
 assert [r['panel_id'] for r in rows]==['778','990']
 assert rows[1]['documents'][0]['title']=='Edital Segunda'
 assert rows[1]['documents'][0]['description']=='Descrição Segunda'
 assert rows[0]['documents'][0]['updated_at']=='2026-09-08'


@pytest.mark.parametrize('change',[
 lambda html:html.replace('aria-labelledby="heading-778"','aria-labelledby="heading-999"'),
 lambda html:html.replace('/Media/fapes/Editais/novo.pdf','https://foreign.test/file.pdf'),
 lambda html:html.replace('/Media/fapes/Editais/novo.pdf','/Media/fapes/../secret.pdf'),
 lambda html:html.replace('08/09/2026','31/02/2026'),
 lambda html:html.replace('class="dataatualizacao-value"','class="missing"'),
])
def test_unknown_structure_or_unsafe_document_cannot_be_silently_skipped(change):
 html='<ul class="galeriade-arquivos">'+panel(778,'Primeira')+'</ul>'
 with pytest.raises(ValueError):parse_file_panels(change(html))


@pytest.mark.parametrize('extension',['doc','docx'])
def test_word_annex_is_preserved_and_identified_without_pretending_it_is_pdf(extension):
 rows=parse_file_panels('<ul class="galeriade-arquivos">'+panel(21,'Anexo','/Media/fapes/Editais/formulario.'+extension)+'</ul>')
 assert rows[0]['documents'][0]['format']==extension
 assert rows[0]['documents'][0]['title']=='Edital Anexo'


def test_repeated_url_preserves_both_published_rows_and_their_metadata():
 html='<ul class="galeriade-arquivos">'+panel(21,'Anexo')+'</ul>'
 row=html[html.index('<tr>'):html.index('</tr>')+5]
 html=html.replace('</tbody>',row.replace('Edital Anexo','Republicação do anexo')+'</tbody>')
 docs=parse_file_panels(html)[0]['documents']
 assert len(docs)==2 and docs[0]['url']==docs[1]['url']
 assert docs[1]['title']=='Republicação do anexo'
 assert docs[0]['duplicate_url_in_panel'] is False
 assert docs[1]['duplicate_url_in_panel'] is True


@pytest.mark.parametrize('path',['/Media/fapes/Editais/file.exe',
 '/Media/fapes/%252e%252e/private.docx','/Media/fapes/../private.docx',
 'https://foreign.test/Media/fapes/file.docx'])
def test_other_or_unsafe_attachment_paths_remain_rejected(path):
 with pytest.raises(ValueError):
  parse_file_panels('<ul class="galeriade-arquivos">'+panel(21,'Anexo',path)+'</ul>')


def test_menu_discovers_new_section_paths_without_keyword_assumptions():
 html='<li class="dropdown"><a>Editais</a><ul><li class="dropdown"><a>Abertos&nbsp;</a><ul class="dropdown-menu"><li><a href="/nova-area">Área nova</a></li></ul></li></ul></li>'
 html += '<li class="dropdown"><a>Teletrabalho</a><a href="/teletrabalho">Encerrados</a></li>'
 assert discover_sections(html)==['https://fapes.es.gov.br/nova-area']
 with pytest.raises(ValueError):discover_sections(html.replace('/nova-area','https://foreign.test/nova'))
 with pytest.raises(ValueError):discover_sections('<p>Menu indisponível</p>')
