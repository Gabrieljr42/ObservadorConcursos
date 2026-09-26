import pytest
from app.tenderproof.funcap_adapter import FuncapAdapter
from app.tenderproof.funcap_panels import LISTING
from tests.test_tenderproof_funcap_panels import group


def test_original_url_separates_reused_ids_and_revalidation_rejects_changed_manifest():
    html='<div class="editais-conteudo"><div class="box"><div class="title"><h5>Encerrados</h5></div>'+group(2025,11)+group(2026,22)+'</div></div>'
    adapter=FuncapAdapter();page=adapter.parse_listing(html,LISTING)
    assert len(page.candidates)==2
    first,second=page.candidates
    assert first.candidate_id!=second.candidate_id
    assert adapter.choose_document(adapter.documents(html,first)).url_requested.endswith('/11.pdf')
    assert adapter.choose_document(adapter.documents(html,second)).url_requested.endswith('/22.pdf')
    with pytest.raises(ValueError):adapter.confirm_identity(first,html.replace('11.pdf','33.pdf'),first.detail_url_observed)
    duplicate=html.replace('22.pdf','11.pdf')
    result=adapter.parse_listing(duplicate,LISTING)
    assert not result.candidates and result.truncated
