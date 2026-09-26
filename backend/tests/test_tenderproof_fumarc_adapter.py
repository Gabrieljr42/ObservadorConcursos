import json
from datetime import datetime, timezone
import pytest
from app.tenderproof.fumarc_adapter import FumarcAdapter
from app.tenderproof.fumarc_detail import detail_api_url
from app.tenderproof.fumarc_publications import publication_url


def evidence():
    now = datetime(2026, 9, 8, tzinfo=timezone.utc)
    rows = [{'Id': n, 'ConcursoId': 88, 'Title': title, 'TipoPublicacao': 'Arquivo',
             'PermitirDownload': True, 'Arquivo': {'Url': f'https://www.fumarc.com.br/Documentos%20Compartilhados/Novo/{n}.pdf'}}
            for n, title in enumerate(('Edital 01/2026', 'Errata 01', 'Edital consolidado', 'Resultado final', 'Anexo I'), 1)]
    return {'source': 'fumarc_open', 'contest_id': 88, 'resources': [
        {'url': detail_api_url(88, now), 'body': {'d': {'results': [{'Id': 88, 'Title': 'Concurso novo'}]}}},
        {'url': publication_url(88, now), 'body': {'d': {'results': rows}}}]}


def test_classifies_original_update_consolidated_result_and_annex():
    adapter = FumarcAdapter()
    candidate = adapter.candidate_from_url('https://www.fumarc.com.br/SitePages/Home.aspx?concurso=88')
    docs = adapter.documents(json.dumps(evidence()), candidate)
    assert [d.kind for d in docs] == ['edital', 'retificacao', 'consolidado', 'resultado', 'anexo']
    assert adapter.choose_document(docs).doc_id == 'fumarc-88-1'


@pytest.mark.parametrize('mutation', ['missing', 'extra', 'wrong_contest', 'wrong_document', 'disabled'])
def test_preserved_resource_association_is_rechecked(mutation):
    adapter = FumarcAdapter()
    candidate = adapter.candidate_from_url('https://www.fumarc.com.br/SitePages/Home.aspx?concurso=88')
    data = evidence()
    if mutation == 'missing': data['resources'].pop()
    if mutation == 'extra': data['resources'].append(data['resources'][-1])
    if mutation == 'wrong_contest': data['contest_id'] = 89
    if mutation == 'wrong_document': data['resources'][1]['body']['d']['results'][0]['ConcursoId'] = 89
    if mutation == 'disabled':
        data['resources'][1]['body']['d']['results'][0]['PermitirDownload'] = False
        assert len(adapter.documents(json.dumps(data), candidate)) == 4
        return
    with pytest.raises(ValueError): adapter.documents(json.dumps(data), candidate)


def test_supplementary_selection_requires_unique_job_table():
    from app.tenderproof.contracts import DocumentCandidate
    adapter = FumarcAdapter()
    original = DocumentCandidate(doc_id='original', title='Edital', kind='edital', url_requested='https://example.org/original.pdf')
    annex = DocumentCandidate(doc_id='annex', title='Anexo I — Quadro de cargos e vagas', kind='anexo', url_requested='https://example.org/jobs.pdf')
    assert adapter.supplementary_documents([original, annex], original) == [annex]
    other = annex.model_copy(update={'doc_id':'another', 'url_requested':'https://example.org/another.pdf'})
    with pytest.raises(ValueError): adapter.supplementary_documents([original, annex, other], original)


def test_additional_download_cannot_switch_candidate_or_add_unobserved_file():
    from app.tenderproof.acquisition import AcquisitionService
    from app.tenderproof.contracts import DocumentCandidate
    adapter = FumarcAdapter()
    c = adapter.candidate_from_url('https://www.fumarc.com.br/SitePages/Home.aspx?concurso=88')
    document = DocumentCandidate(doc_id='annex', title='Anexo', kind='anexo', url_requested='https://www.fumarc.com.br/Documentos%20Compartilhados/Novo/1.pdf')
    acquisition = AcquisitionService()
    acquisition.last_candidate = (c.source,c.external_id,c.detail_url_observed)
    acquisition.last_documents = [document]
    wrong = adapter.candidate_from_url('https://www.fumarc.com.br/SitePages/Home.aspx?concurso=89')
    with pytest.raises(ValueError): acquisition.fetch_document(None,candidate=wrong,document=document)
    with pytest.raises(ValueError): acquisition.fetch_document(None,candidate=c,document=document.model_copy(update={'doc_id':'injected'}))
