import pytest
from app.tenderproof.fapepi_pages import ROOT, parse_listing, parse_detail


def test_listing_reads_all_groups_deduplicates_and_preserves_uncertain_coverage():
    group = '<ul class="display-posts-listing"><li><a class="title" href="/edital/novo_2028/">Edital novo</a></li></ul>'
    result = parse_listing(group + group)
    assert len(result['items']) == 1 and len(result['items'][0]['titles']) == 2
    assert not result['coverage_complete']
    with pytest.raises(ValueError): parse_listing(group.replace('/edital/novo_2028/', 'https://evil.test/edital/novo/'))


def test_detail_binds_canonical_and_distinguishes_amendment_external_and_original():
    url = ROOT + '/edital/novo/'
    html = f'<link rel="canonical" href="{url}"><main class="type-edital"><h1 class="entry-title">Novo</h1><div class="page-content">'
    for name, path in [('EDITAL 01/2028','edital.pdf'), ('EDITAL RETIFICADO','v2.pdf'), ('ANEXO I','anexo.docx')]:
        html += f'<a href="{ROOT}/wp-content/uploads/2028/01/{path}">{name}</a>'
    html += '<a href="https://external.test/chamada">Chamada externa</a></div></main>'
    result = parse_detail(html, url)
    assert [d['kind'] for d in result['documents']] == ['edital','consolidado','anexo']
    assert len(result['pending_links']) == 1 and not result['manifest_complete']
    with pytest.raises(ValueError): parse_detail(html, ROOT+'/edital/outro/')
