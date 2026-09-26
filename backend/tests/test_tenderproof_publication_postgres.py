"""Opt-in PostgreSQL acceptance, using a private generated schema per case.

Start a NEW postgres:17-alpine container on random loopback port, fixture user,
database tenderproof_acceptance, no user data mounts. Set the URL only for this
pytest process. Default test collection skips this module. Cleanup belongs to
the operator who created that container; tests never touch existing containers.
"""
import os
import pytest
from sqlalchemy import inspect

from test_tenderproof_publication import (
    env,
    test_apply_twice_one_version_correct_diff_and_no_precommit_notifications,
    test_reprocessed_same_values_metadata_do_not_create_version,
    test_unknown_conflict_and_salary_scope_preserve_existing,
    test_stale_baseline_and_recomparison,
    test_failure_rolls_back_canonical_version_outbox_and_claim,
    test_outbox_failure_retry_atomic_and_deduplicated,
    test_rollback_audit_preserves_history_and_blocks_later_changes,
    test_rollback_rejects_later_canonical_change,
    test_real_jwt_authorization_and_owner_isolation,
    test_concurrent_duplicate_requests_persist_one_application,
    test_concurrent_outbox_drain_creates_one_internal_notification,
    test_rollback_preserves_delivered_notifications_and_has_distinct_reversal,
    test_unchanged_traditional_crawl_after_merge_creates_no_version,
)
from app.models import ConcursoPublication, ConcursoVersion
from app.tenderproof.publication import (approve_normalized_link_proposal,
    apply_normalized_link_proposal, create_normalized_link_proposal)
from app.tenderproof.publication_models import PublicationOutbox, PublicationProposal, ensure_publication_schema

pytestmark = pytest.mark.skipif(not os.getenv("TENDERPROOF_TEST_POSTGRES_URL"), reason="Explicit disposable PostgreSQL URL required")


def test_postgres_additive_migration_from_canonical_tables(env):
    db, _, _, _, _, _ = env
    engine = db.get_bind()
    assert engine.dialect.name == "postgresql"
    db.rollback()
    PublicationOutbox.__table__.drop(engine)
    PublicationProposal.__table__.drop(engine)
    assert "tenderproof_publication_proposals" not in inspect(engine).get_table_names()
    ensure_publication_schema(engine)
    ensure_publication_schema(engine)
    assert "tenderproof_publication_proposals" in inspect(engine).get_table_names()
    assert "tenderproof_publication_outbox" in inspect(engine).get_table_names()


def test_postgres_normalized_apply_returning_is_atomic(env):
    db, _, user, contest, _, _ = env
    contest.link_edital = "https://example.test/edital.pdf"
    contest.edital_numero = "01/2026"
    db.commit()
    plan = create_normalized_link_proposal(db, concurso_ids=[contest.id], user=user)
    approve_normalized_link_proposal(db, proposal_id=plan["id"], proposal_hash=plan["proposal_hash"],
                                     fields=["publications"], user=user)
    result = apply_normalized_link_proposal(db, proposal_id=plan["id"], proposal_hash=plan["proposal_hash"], user=user)
    assert len(result["applied"]) == 1
    assert db.query(ConcursoPublication).count() == 1
    assert db.query(ConcursoVersion).filter(ConcursoVersion.change_type == "document_added").count() == 1
    assert db.query(PublicationOutbox).count() == 1
