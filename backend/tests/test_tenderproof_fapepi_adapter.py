import pytest
from app.tenderproof.fapepi_adapter import FapepiAdapter
from app.tenderproof.fapepi_pages import ROOT, LISTING


def test_new_call_identity_original_and_pending_external_reference():
    a = FapepiAdapter()
    url = ROOT+'/edital/futura-2030/'
    listing = '<ul class="display-posts-listing"><li><a class="title" href="'+url+'">Nova</a></li></ul>'
    candidate = a.parse_listing(listing, LISTING).candidates[0]
    html = f'<link rel="canonical" href="{url}"><main class="type-edital"><h1 class="entry-title">Nova</h1><div class="page-content"><a href="{ROOT}/wp-content/uploads/2030/01/novo.pdf">Edital 01/2030</a></div></main>'
    a.confirm_identity(candidate, html, url)
    assert a.choose_document(a.documents(html, candidate)).kind == 'edital'
    with pytest.raises(ValueError): a.documents(html.replace('</div>','<a href="https://external.test/file">Documento</a></div>'),candidate)
    with pytest.raises(ValueError): a.confirm_identity(candidate,html,url.replace('futura','diferente'))
