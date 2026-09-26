import copy
import json
import pytest
from fastapi import HTTPException
from app.models import User
from app.tenderproof import amendment
from test_tenderproof_publication import env
from test_tenderproof_amendment import _proposal


FIELDS = ['inscricao_inicio', 'inscricao_fim', 'prova_data']


def test_publisher_permission_required(env):
    db, user, contest, run, store, queue, case, proposal = _proposal(env)
    with pytest.raises(HTTPException) as exc:
        amendment.approve_proposal(db, proposal_id=proposal['id'], proposal_hash=proposal['proposal_hash'],
            fields=FIELDS, user=db.get(User, 3), queue=queue, store=store)
    assert exc.value.status_code == 403


def test_changed_preserved_bytes_cannot_be_approved(env, monkeypatch):
    db, user, contest, run, store, queue, case, proposal = _proposal(env)
    original = store.load_artifact_bytes
    monkeypatch.setattr(store, 'load_artifact_bytes', lambda artifact:
        b'not the approved PDF' if artifact.sha256 == proposal['amendment_document']['sha256'] else original(artifact))
    with pytest.raises(HTTPException) as exc:
        amendment.approve_proposal(db, proposal_id=proposal['id'], proposal_hash=proposal['proposal_hash'],
            fields=FIELDS, user=user, queue=queue, store=store)
    assert exc.value.status_code == 409
    assert queue.review_for_run(run)['pending']


def test_new_manifest_keeps_review_pending(env):
    db, user, contest, run, store, queue, case, proposal = _proposal(env)
    with queue._db(write=True) as qdb:
        qdb.execute("UPDATE document_review_state SET manifest=?", (json.dumps(case['revision']['manifest'] +
            [{'url': 'https://example.test/new.pdf', 'title': 'New notice', 'kind': 'retificacao'}]),))
    with pytest.raises(HTTPException) as exc:
        amendment.approve_proposal(db, proposal_id=proposal['id'], proposal_hash=proposal['proposal_hash'],
            fields=FIELDS, user=user, queue=queue, store=store)
    assert exc.value.status_code == 409


def test_partial_approval_cannot_clear_full_amendment(env):
    db, user, contest, run, store, queue, case, proposal = _proposal(env)
    with pytest.raises(HTTPException):
        amendment.approve_proposal(db, proposal_id=proposal['id'], proposal_hash=proposal['proposal_hash'],
            fields=['inscricao_fim'], user=user, queue=queue, store=store)
    assert queue.review_for_run(run)['pending']


def test_changed_catalogue_rejects_application(env):
    db, user, contest, run, store, queue, case, proposal = _proposal(env)
    amendment.approve_proposal(db, proposal_id=proposal['id'], proposal_hash=proposal['proposal_hash'],
        fields=FIELDS, user=user, queue=queue, store=store)
    contest.titulo = 'Concurrent reviewed title'
    db.commit()
    with pytest.raises(HTTPException) as exc:
        amendment.apply_proposal(db, proposal_id=proposal['id'], proposal_hash=proposal['proposal_hash'],
            user=user, queue=queue, store=store)
    assert exc.value.status_code == 409
    assert queue.review_for_run(run)['pending']


def test_notice_number_is_not_a_substring(env):
    db, _, user, contest, run, store = env
    with pytest.raises(HTTPException):
        amendment._assert_identity_text({'sha256': 'a'*64}, {'a'*64: {'pages': {
            1: 'PREFEITURA MUNICIPAL DE EXEMPLO. CONCURSO PÚBLICO 101/2026. EDITAL DE PRORROGAÇÃO.'}}}, contest)


def test_invented_snippet_rejected(env):
    db, user, contest, run, store, queue, case, proposal = _proposal(env)
    changes = copy.deepcopy(proposal['changes'])
    changes['inscricao_fim']['provenance'][0]['snippet'] = 'A fabricated deadline statement never printed in the PDF'
    with pytest.raises(HTTPException):
        amendment.create_proposal(db, concurso_id=contest.id, user=user, base_document=proposal['base_document'],
            amendment_document=proposal['amendment_document'], changes=changes, reason=proposal['reason'],
            authorization=proposal['authorization'], run=run, queue=queue, store=store, review_case_id=case['id'])
