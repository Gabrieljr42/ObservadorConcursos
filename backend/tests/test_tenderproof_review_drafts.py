import pytest
from fastapi import HTTPException
from app.tenderproof import review_cases as review
from test_tenderproof_publication import env
from test_tenderproof_review_cases import setup_case
from test_tenderproof_document_review_gate import checkpoint, manifest, EXTRA


def test_partial_draft_restores_without_approval_and_prevents_lost_updates(env):
    queue,case,_=setup_case(env);run=env[4]
    draft=[{'sha256':run.artifact.sha256,'page':1,'reason':'Ainda conferindo'}]
    saved=review.save_draft(queue,run,case['id'],case['revision_hash'],0,draft)
    assert saved['draft_revision']==1
    restored=review.current(queue,run)
    assert restored['draft']==draft and restored['approved_at'] is None
    assert queue.review_for_run(run)['pending']
    with pytest.raises(HTTPException) as exc:
        review.save_draft(queue,run,case['id'],case['revision_hash'],0,[])
    assert exc.value.status_code==409
    assert review.current(queue,run)['draft']==draft
    review.save_draft(queue,run,case['id'],case['revision_hash'],1,[])
    assert review.current(queue,run)['draft']==[]


def test_drafts_reject_foreign_document_page_and_owner(env):
    queue,case,_=setup_case(env);run=env[4]
    for drafts in [[{'sha256':'a'*64}], [{'sha256':run.artifact.sha256,'page':999}],
        [{'sha256':run.artifact.sha256}]*2]:
        with pytest.raises(HTTPException) as exc:
            review.save_draft(queue,run,case['id'],case['revision_hash'],0,drafts)
        assert exc.value.status_code==422
    with pytest.raises(HTTPException) as exc:
        review.save_draft(queue,run.model_copy(update={'owner_user_id':2}),case['id'],case['revision_hash'],0,[])
    assert exc.value.status_code==404


def test_approved_or_outdated_case_cannot_be_modified(env, monkeypatch):
    queue,case,decisions=setup_case(env);run=env[4]
    original=review.METHOD_VERSION
    monkeypatch.setattr(review,'METHOD_VERSION','different')
    with pytest.raises(HTTPException):
        review.save_draft(queue,run,case['id'],case['revision_hash'],0,[])
    monkeypatch.setattr(review,'METHOD_VERSION',original)
    review.approve(queue,env[5],run,case['id'],case['revision_hash'],decisions)
    with pytest.raises(HTTPException):
        review.save_draft(queue,run,case['id'],case['revision_hash'],0,[])
    assert review.read(queue,case['id'],run.owner_user_id)['decisions']==decisions


def test_new_manifest_preserves_old_draft_without_reusing_it(env):
    queue,case,_=setup_case(env);run=env[4]
    draft=[{'sha256':run.artifact.sha256,'reason':'Conferência em andamento'}]
    review.save_draft(queue,run,case['id'],case['revision_hash'],0,draft)
    checkpoint(env,manifest(env)+[EXTRA,dict(EXTRA,url=EXTRA['url']+'?new=1')],now=4000)
    assert review.current(queue,run) is None
    with pytest.raises(HTTPException):
        review.save_draft(queue,run,case['id'],case['revision_hash'],1,[])
    assert review.read(queue,case['id'],run.owner_user_id)['draft']==draft
