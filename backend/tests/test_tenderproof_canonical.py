"""Synthetic PDFs and disposable databases: canonical creation acceptance."""
import pytest
from fastapi import HTTPException
from sqlalchemy import select
from app.models import Concurso, ConcursoVersion
from app.tenderproof import publication as pub
from app.tenderproof.publication_models import CanonicalIdentity, PublicationOutbox
from test_tenderproof_publication import env, count, apply


def new_proposal(env):
    db, _, user, contest, run, store = env
    db.delete(contest)
    db.commit()
    return pub.create_proposal(db, run=run, user=user, store=store)


def approve(env, p):
    db, _, user, _, _, store = env
    return pub.approve_proposal(db, proposal_id=p['id'], proposal_hash=p['proposal_hash'],
                                fields=p['eligible_fields'], user=user, store=store)


def test_create_retry_version_outbox_and_archive(env):
    db, _, user, _, run, store = env
    p = new_proposal(env)
    assert p['action'] == 'create' and p['concurso_id'] is None
    assert p['creation_metadata'] == {'banca': 'IBGP', 'link_edital': run.artifact.url_final}
    assert pub.create_proposal(db, run=run, user=user, store=store)['id'] == p['id']
    result = apply(env, approve(env, p))
    assert result['state'] == 'applied'
    assert apply(env, p)['version_id'] == result['version_id']
    assert count(db, Concurso) == count(db, ConcursoVersion) == count(db, PublicationOutbox) == 1
    assert count(db, CanonicalIdentity) == 2
    target = db.get(Concurso, result['concurso_id'])
    assert target.orgao and target.titulo and target.edital_numero
    assert target.salario_min is None
    assert db.get(ConcursoVersion, result['version_id']).change_type == 'created'
    rollback = pub.rollback_proposal(db, proposal_id=p['id'], reason='cadastro indevido na fixture', user=user)
    db.refresh(target)
    assert rollback['state'] == 'rolled_back' and target.status == 'arquivado'
    assert count(db, Concurso) == 1 and count(db, ConcursoVersion) == 2


def test_new_requires_minimum_approval(env):
    db, _, user, _, _, store = env
    p = new_proposal(env)
    with pytest.raises(HTTPException) as exc:
        pub.approve_proposal(db, proposal_id=p['id'], proposal_hash=p['proposal_hash'], fields=['titulo'], user=user, store=store)
    assert exc.value.status_code == 422
    assert count(db, Concurso) == 0


def test_racing_new_proposals_require_recomparison(env):
    db, _, user, _, run, store = env
    first = approve(env, new_proposal(env))
    other = run.model_copy(deep=True)
    other.run_id = 'second-observation'
    second = approve(env, pub.create_proposal(db, run=other, user=user, store=store))
    apply(env, first)
    with pytest.raises(HTTPException) as exc:
        apply(env, second)
    assert exc.value.status_code == 409
    assert count(db, Concurso) == count(db, ConcursoVersion) == 1


def test_new_transaction_failure_leaves_no_contest(env, monkeypatch):
    db, *_ = env
    p = approve(env, new_proposal(env))
    def fail(*args, **kwargs):
        raise RuntimeError('synthetic transaction failure')
    monkeypatch.setattr(pub, '_version', fail)
    with pytest.raises(RuntimeError):
        apply(env, p)
    assert count(db, Concurso) == count(db, CanonicalIdentity) == count(db, PublicationOutbox) == 0


def test_cross_source_requires_explicit_review_and_matching_notice(env):
    db, _, user, target, run, store = env
    # A second configured alias represents a distinct acquisition origin. Shared
    # documentary identity must not silently merge it with the legacy contest.
    from app.models import Source
    source = Source(name='IBGP alias fixture', base_url='https://novo.ibgpconcursos.com.br', source_type=run.source)
    db.add(source)
    db.commit()
    with pytest.raises(HTTPException) as exc:
        pub.create_proposal(db, run=run, source_id=source.id, user=user, store=store)
    assert exc.value.status_code == 409
    p = pub.create_proposal(db, run=run, concurso_id=target.id, source_id=source.id, user=user, store=store)
    assert p['identity']['reason'] == 'reviewed_organization_notice'
    result = apply(env, approve(env, p))
    assert result['concurso_id'] == target.id and count(db, Concurso) == 1

def test_parallel_new_proposals_from_distinct_sources_one_contest(env, monkeypatch):
    monkeypatch.setenv("TENDERPROOF_PROCESSING_CONCURRENCY", "2")
    from concurrent.futures import ThreadPoolExecutor
    import threading
    from app.models import Source, User
    db, factory, user, _, run, store = env
    p = approve(env, new_proposal(env))
    other_source = Source(name='Alias fixture', source_type=run.source, base_url='https://novo.ibgpconcursos.com.br')
    db.add(other_source)
    db.commit()
    second = run.model_copy(deep=True)
    second.run_id = 'parallel-alias'
    q = approve(env, pub.create_proposal(db, run=second, source_id=other_source.id, user=user, store=store))
    db.rollback()
    barrier = threading.Barrier(2)
    def worker(proposal):
        with factory() as session:
            reviewer = session.get(User, 1)
            barrier.wait(timeout=10)
            try:
                return pub.apply_proposal(session, proposal_id=proposal['id'], proposal_hash=proposal['proposal_hash'], user=reviewer, store=store)['state']
            except HTTPException as exc:
                return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, [p,q]))
    assert sorted(map(str, results)) == ['409', 'applied']
    assert count(db, Concurso) == count(db, ConcursoVersion) == count(db, PublicationOutbox) == 1


def test_nullable_migration_preserves_applied_ledger(env):
    from alembic.operations import Operations
    from alembic.migration import MigrationContext
    from sqlalchemy import inspect, Integer
    from app.tenderproof.publication_models import PublicationProposal, ensure_publication_schema
    from test_tenderproof_publication import proposal
    db, _, _, _, _, _ = env
    p = apply(env, proposal(env))
    engine = db.get_bind()
    db.close()
    with engine.begin() as connection:
        operations = Operations(MigrationContext.configure(connection))
        with operations.batch_alter_table(PublicationProposal.__tablename__) as batch:
            batch.alter_column('concurso_id', existing_type=Integer(), nullable=False)
    ensure_publication_schema(engine)
    ensure_publication_schema(engine)
    assert next(c for c in inspect(engine).get_columns(PublicationProposal.__tablename__) if c['name'] == 'concurso_id')['nullable']
    assert db.get(PublicationProposal, p['id']).version_id == p['version_id']
    assert count(db, PublicationOutbox) == 1

def access_run(env):
    from datetime import datetime
    import hashlib
    from app.models import Source
    from app.tenderproof.demo_pdf import make_text_pdf
    from app.tenderproof.mock_demo import PDF_PAGE_1
    from app.tenderproof.contracts import Artifact, DocumentCandidate
    from app.tenderproof.source_adapters import get_source_adapter
    from app.tenderproof.pdf_text import extract_pages
    from app.tenderproof.fields import extract_fields
    db, _, _, _, run, store = env
    source = Source(name='ACCESS synthetic fixture', source_type='access_open', base_url='https://access.selecao.net.br')
    db.add(source)
    db.commit()
    adapter = get_source_adapter('access_open')
    candidate = adapter.candidate_from_url('https://access.selecao.net.br/informacoes/42/', 'Concurso Prefeitura Municipal de Exemplo MG')
    document_url = 'https://anexos-r2.selecao.net.br/uploads/422/concursos/42/anexos/edital.pdf'
    content = make_text_pdf([PDF_PAGE_1.replace('concurso.jsp?cod=42', candidate.detail_url_observed)])
    artifact = Artifact(artifact_id='access-synthetic', sha256=hashlib.sha256(content).hexdigest(), byte_len=len(content),
                        url_requested=document_url, url_final=document_url, downloaded_at=datetime.utcnow())
    store.save_artifact_file(artifact, content)
    result = run.model_copy(deep=True)
    result.run_id = 'access-synthetic-run'
    result.source = 'access_open'
    result.candidates = [candidate]
    result.selected_candidate_id = candidate.candidate_id
    result.artifact = artifact
    result.document = DocumentCandidate(doc_id='access-doc', title='Edital de abertura', kind='edital', url_requested=document_url)
    pages, *_ = extract_pages(content, artifact_id=artifact.artifact_id)
    result.fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    return result, source


def test_access_pdf_creates_then_ibgp_associates_explicitly(env):
    db, _, user, old, ibgp, store = env
    run, source = access_run(env)
    db.delete(old)
    db.commit()
    p = pub.create_proposal(db, run=run, user=user, store=store)
    result = apply(env, approve(env, p))
    assert result['action'] == 'create'
    assert result['identity']['source_id'] == source.id
    with pytest.raises(HTTPException) as exc:
        pub.create_proposal(db, run=ibgp, user=user, store=store)
    assert exc.value.status_code == 409
    update = pub.create_proposal(db, run=ibgp, concurso_id=result['concurso_id'], user=user, store=store)
    applied = apply(env, approve(env, update))
    assert applied['concurso_id'] == result['concurso_id']
    assert count(db, Concurso) == 1
    target = db.get(Concurso, result['concurso_id'])
    assert target.source_id == source.id


def test_access_other_tenant_document_rejected(env):
    db, _, user, _, _, store = env
    run, _ = access_run(env)
    run.artifact.url_final = run.artifact.url_final.replace('/422/', '/567/')
    with pytest.raises(HTTPException) as exc:
        pub.create_proposal(db, run=run, user=user, store=store)
    assert exc.value.status_code == 422


def test_consolidated_document_does_not_bypass_revalidation(env):
    db, _, user, target, run, store = env
    run.document.title = 'Edital consolidado'
    with pytest.raises(HTTPException) as exc:
        pub.create_proposal(db, run=run, concurso_id=target.id, user=user, store=store)
    assert exc.value.status_code == 422

def test_creation_metadata_change_requires_new_review(env):
    from app.models import Source
    db, _, _, _, _, _ = env
    p = approve(env, new_proposal(env))
    source = db.get(Source, p['identity']['source_id'])
    source.name = 'Changed source after review'
    db.commit()
    with pytest.raises(HTTPException) as exc:
        apply(env, p)
    assert exc.value.status_code == 409
    assert count(db, Concurso) == count(db, ConcursoVersion) == 0
