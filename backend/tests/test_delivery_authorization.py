import pytest
from fastapi import HTTPException
from app.models import ConcursoVersion
from app.tenderproof import publication as pub
from test_tenderproof_publication import env


AUTH = {'actor_kind': 'delegated_automation', 'human_read': False,
        'delegation_reference': 'user-instruction-fixture', 'delegation_sha256': 'b' * 64}


def test_delegated_authorization_is_hashed_and_saved_in_version(env):
    db, _, user, contest, run, store = env
    proposal = pub.create_proposal(db, run=run, concurso_id=contest.id, user=user, store=store, authorization=AUTH)
    assert proposal['authorization']['human_read'] is False
    with pytest.raises(HTTPException) as error:
        pub.approve_proposal(db, proposal_id=proposal['id'], proposal_hash=proposal['proposal_hash'],
                             fields=['inscricao_fim'], user=user, store=store,
                             authorization={**AUTH, 'delegation_sha256': 'c' * 64})
    assert error.value.status_code == 409
    pub.approve_proposal(db, proposal_id=proposal['id'], proposal_hash=proposal['proposal_hash'],
                         fields=['inscricao_fim'], user=user, store=store, authorization=AUTH)
    result = pub.apply_proposal(db, proposal_id=proposal['id'], proposal_hash=proposal['proposal_hash'], user=user, store=store)
    version = db.get(ConcursoVersion, result['version_id'])
    assert version.raw_data_snapshot['tenderproof']['authorization']['actor_kind'] == 'delegated_automation'
    assert version.raw_data_snapshot['tenderproof']['authorization']['human_read'] is False


def test_old_base_run_cannot_propose_reverting_amended_date(env):
    db, _, user, contest, run, store = env
    contest.raw_data = {'tenderproof': {'amendments': [{'proposal_id': 'applied-fixture'}]}}
    db.add(ConcursoVersion(concurso_id=contest.id, content_hash=contest.content_hash,
                          change_type='amendment', changed_fields={'inscricao_fim': {'old': '2026-04-20', 'new': '2026-04-19'}}))
    db.commit()
    proposal = pub.create_proposal(db, run=run, concurso_id=contest.id, user=user, store=store)
    assert 'inscricao_fim' not in proposal['eligible_fields']
    assert 'retificação' in proposal['blocked_fields']['inscricao_fim']


def test_automation_cannot_claim_human_reading(env):
    db, _, user, contest, run, store = env
    with pytest.raises(HTTPException) as error:
        pub.create_proposal(db, run=run, concurso_id=contest.id, user=user, store=store,
                            authorization={**AUTH, 'human_read': True})
    assert error.value.status_code == 422
