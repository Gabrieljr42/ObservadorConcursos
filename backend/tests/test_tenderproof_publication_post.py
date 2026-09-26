"""POST document access: controlled publication fixtures and real preserved bytes."""
import hashlib
import json

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.auth import create_access_token
from app.database import get_db
from app.models import Concurso, Source
from app.tenderproof import publication as pub
from app.tenderproof.contracts import DocumentAcquisitionRequest
from app.tenderproof.publication_models import PublicationProposal
from app.tenderproof.source_adapters import get_source_adapter
from test_tenderproof_document_post import observed, FIX
from test_tenderproof_publication import env


@pytest.fixture
def controlled_post(env, monkeypatch):
    """Synthetic canonical baseline/PDF; no claim of live POST on IBGP."""
    run = env[4]
    run.document.acquisition_request = DocumentAcquisitionRequest(body='177,0')
    adapter = get_source_adapter(run.source)
    def validate(document, candidate):
        if document.acquisition_request is None or document.acquisition_request.body != '177,0':
            raise ValueError('controlled POST fixture contract')
    monkeypatch.setattr(adapter, 'validate_document_request', validate, raising=False)
    env[5].put_run(run)
    return env


@pytest.mark.parametrize('creating', [True, False])
def test_post_create_and_update_review_offer_authenticated_pdf_and_official_page(controlled_post, creating):
    db, _, user, contest, run, store = controlled_post
    if creating:
        db.delete(contest)
        db.commit()
    proposal = pub.create_proposal(db, run=run, user=user, store=store)
    page = run.candidates[0].detail_url_observed
    access = proposal['document_access']
    assert access['official_page_url'] == page
    assert access['artifact_download_path'] == f'/tenderproof/runs/{run.run_id}/artifacts/{run.artifact.artifact_id}'
    assert access['requires_authentication'] and access['sha256'] == run.artifact.sha256
    if creating:
        assert proposal['creation_metadata']['link_edital'] == page
        assert page != run.document.url_requested
    approved = pub.approve_proposal(db, proposal_id=proposal['id'], proposal_hash=proposal['proposal_hash'],
                                   fields=proposal['eligible_fields'], user=user, store=store)
    result = pub.apply_proposal(db, proposal_id=approved['id'], proposal_hash=approved['proposal_hash'], user=user, store=store)
    assert result['document_access'] == access
    assert result['state'] == 'applied'
    if creating:
        assert db.get(Concurso, result['concurso_id']).link_edital == page
    assert pub.apply_proposal(db, proposal_id=approved['id'], proposal_hash=approved['proposal_hash'], user=user, store=store)['version_id'] == result['version_id']


def test_old_post_creation_endpoint_requires_new_review(controlled_post):
    db, _, user, contest, run, store = controlled_post
    db.delete(contest)
    db.commit()
    current = pub.create_proposal(db, run=run, user=user, store=store)
    old = db.get(PublicationProposal, current['id'])
    payload = json.loads(json.dumps(old.payload))
    payload['creation_metadata']['link_edital'] = run.artifact.url_final
    old.payload = payload
    old.proposal_hash = pub._hash(payload)
    old.id = 'tpp-' + pub._hash([user.id, run.run_id, None, old.proposal_hash])[:32]
    db.commit()
    view = pub.get_proposal(db, old.id, user)
    assert view['stale'] and view['blockers']
    with pytest.raises(HTTPException) as exc:
        pub.approve_proposal(db, proposal_id=old.id, proposal_hash=old.proposal_hash,
                            fields=view['eligible_fields'], user=user, store=store)
    assert exc.value.status_code == 409
    new = pub.create_proposal(db, run=run, user=user, store=store)
    assert new['id'] != old.id and not new['stale']
    assert new['creation_metadata']['link_edital'] == run.candidates[0].detail_url_observed


@pytest.mark.parametrize('mutation', ['body', 'missing', 'document_id'])
def test_publication_revalidates_real_fapeg_request_before_pdf_processing(env, observed, monkeypatch, mutation):
    adapter, candidate, document, _ = observed
    db, _, _, contest, run, store = env
    source = db.get(Source, contest.source_id)
    source.source_type = adapter.source
    contest.external_id = candidate.external_id
    contest.link_pagina = candidate.detail_url_observed
    run.source = adapter.source
    run.candidates = [candidate]
    run.selected_candidate_id = candidate.candidate_id
    run.document = document.model_copy(deep=True)
    run.artifact.url_requested = run.artifact.url_final = document.url_requested
    if mutation == 'body':
        run.document.acquisition_request.body = '181,0'
    elif mutation == 'missing':
        run.document.acquisition_request = None
    else:
        run.document.doc_id = 'fapeg-exportarEditalPdf-195'
    monkeypatch.setattr(store, 'load_artifact_bytes', lambda *args: pytest.fail('invalid request reached PDF processing'))
    with pytest.raises(HTTPException) as exc:
        pub._revalidate(run, contest, source, store)
    assert exc.value.status_code == 422


def test_preserved_real_post_pdf_requires_jwt_and_exact_owner(env, observed, monkeypatch):
    from app.tenderproof import router as routes
    adapter, candidate, document, _ = observed
    db, _, user, _, run, store = env
    row = json.loads((FIX / 'pdf-retry-manifest.json').read_text(encoding='utf-8'))['documents'][0]
    raw = (FIX / row['file']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == row['sha256']
    run.source = adapter.source
    run.candidates = [candidate]
    run.selected_candidate_id = candidate.candidate_id
    run.document = document
    run.artifact = run.artifact.model_copy(update={'artifact_id': 'preserved-fapeg-177', 'byte_len': len(raw),
        'sha256': row['sha256'], 'url_requested': document.url_requested, 'url_final': document.url_requested,
        'storage_path': None})
    store.save_artifact_file(run.artifact, raw)
    store.put_run(run)
    monkeypatch.setattr(routes, 'get_store', lambda: store)
    app = FastAPI()
    app.include_router(routes.router)
    app.dependency_overrides[get_db] = lambda: db
    access = pub._document_access(run)
    def auth(owner):
        return {'Authorization': f'Bearer {create_access_token(str(owner))}'}
    with TestClient(app) as client:
        assert client.get(access['artifact_download_path']).status_code == 401
        assert client.get(access['artifact_download_path'], headers=auth(2)).status_code == 404
        response = client.get(access['artifact_download_path'], headers=auth(user.id))
        assert response.status_code == 200 and response.content == raw
        assert hashlib.sha256(response.content).hexdigest() == access['sha256']
        assert client.get(access['artifact_download_path'].replace('preserved-fapeg-177', 'wrong-artifact'), headers=auth(user.id)).status_code == 404
