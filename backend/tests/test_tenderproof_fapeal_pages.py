import pytest
from app.tenderproof.fapeal_pages import HOST,discover_categories,parse_listing,parse_detail

def test_observed_typo_category_and_explicit_empty_are_preserved():
    html='<main><div class="widget_nav_menu"><a href="'+HOST+'/category/editais/204/">2024</a></div></main>'
    assert discover_categories(html)=={HOST+'/category/editais/204/':'2024'}
    data=parse_listing('<main id="main"><section class="no-results"><h2 class="page-title">Nada encontrado</h2></section></main>',HOST+'/category/editais/204/')
    assert data['empty_evidence']=='Nada encontrado' and not data['coverage_complete']

def test_result_label_overrides_edital_filename_and_external_links_remain_pending():
    url=HOST+'/2026/05/teste/'
    html='<link rel="canonical" href="'+url+'"><main><article class="type-post"><h1 class="entry-title">Edital</h1><div class="entry-content"><a href="'+HOST+'/wp-content/uploads/2026/05/Edital.pdf">Resultado final</a><a href="https://external.test/file.pdf">Chamada</a></div></article></main>'
    data=parse_detail(html,url)
    assert data['documents'][0]['kind']=='outro'
    assert len(data['pending_links'])==1
    with pytest.raises(ValueError):parse_detail(html,url.replace('teste','outro'))
