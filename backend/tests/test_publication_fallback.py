from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import pytest

from app.database import Base
from app.database import get_db
from app.auth import create_access_token
from app.models import Concurso, ConcursoPublication, ConcursoVersion, Source, User
from app.schemas import ConcursoPublicationOut
from app.tenderproof.publication_models import PublicationOutbox
from app.services import CrawlService
from app.connectors.base import CrawlResult, CrawlRunData
from app.tenderproof.publication import (approve_normalized_link_proposal,
                                         create_normalized_link_proposal,
                                         apply_normalized_link_proposal,
                                         create_normalized_link_repair_proposal,
                                         approve_normalized_link_repair_proposal,
                                         apply_normalized_link_repair_proposal)


def _db():
    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _item():
    return {
        'external_id': 'fallback-1', 'banca': 'Banca teste',
        'orgao': 'Prefeitura teste', 'titulo': 'Concurso Prefeitura teste',
        'modalidade': 'Concurso Público', 'cargo': 'Analista',
        'area': 'administrativa', 'cidade': 'Teste', 'uf': 'MG',
        'status': 'Inscrições abertas', 'vagas': 1, 'salario_min': None,
        'salario_max': None, 'escolaridade': 'Superior', 'taxa': None,
        'prova_data': None, 'edital_numero': '01/2026',
        'edital_data': datetime(2026, 8, 1, tzinfo=timezone.utc),
        'inscricao_inicio': None, 'inscricao_fim': None,
        'link_pagina': 'https://example.test/concursos/fallback-1',
        'link_edital': 'https://example.test/editais/01-2026.pdf',
        'link_inscricao': None, 'resumo': 'Teste', 'raw_data': {},
        'content_hash': 'contest-fallback-1', 'fetched_at': None,
    }


def test_link_edital_is_exposed_as_idempotent_publication_with_provenance():
    db = _db()
    try:
        source = Source(name='Teste', base_url='https://example.test',
                        list_url='https://example.test/list', source_type='test')
        db.add(source)
        db.flush()
        concurso = Concurso(source_id=source.id, **_item())
        db.add(concurso)
        db.flush()

        service = CrawlService(db)
        first = service._sync_publications(concurso, _item())
        second = service._sync_publications(concurso, _item())
        db.flush()

        rows = db.execute(select(ConcursoPublication)).scalars().all()
        assert len(first) == 1
        assert second == []
        assert len(rows) == 1
        assert rows[0].concurso_id == concurso.id
        assert concurso.titulo == 'Concurso Prefeitura teste'
        assert concurso.cargo == 'Analista'
        assert rows[0].link == 'https://example.test/editais/01-2026.pdf'
        assert rows[0].publication_type == 'edital'
        assert rows[0].raw_data['source'] == 'concurso.link_edital'
        assert rows[0].raw_data['provenance']['field'] == 'link_edital'
    finally:
        db.close()


def test_link_edital_fallback_rejects_missing_or_non_http_links():
    db = _db()
    try:
        source = Source(name='Teste', base_url='https://example.test',
                        list_url='https://example.test/list', source_type='test')
        db.add(source)
        db.flush()
        item = _item()
        item['link_edital'] = 'javascript:download()'
        concurso = Concurso(source_id=source.id, **item)
        db.add(concurso)
        db.flush()
        assert CrawlService(db)._sync_publications(concurso, item) == []
    finally:
        db.close()


def test_same_link_converges_fallback_to_later_real_observation():
    db = _db()
    try:
        source = Source(name='Teste', base_url='https://example.test',
                        list_url='https://example.test/list', source_type='test')
        db.add(source)
        db.flush()
        concurso = Concurso(source_id=source.id, **_item())
        db.add(concurso)
        db.flush()
        service = CrawlService(db)
        assert len(service._sync_publications(concurso, _item())) == 1
        later = _item()
        later['raw_data'] = {'publications': [{
            'title': 'Título posterior', 'publication_type': 'edital',
            'publication_date': '2026-08-02T00:00:00+00:00',
            'link': later['link_edital'], 'content_hash': 'different-hash',
        }]}
        enriched = service._sync_publications(concurso, later)
        db.flush()
        rows = db.execute(select(ConcursoPublication)).scalars().all()
        assert len(enriched) == 1
        assert len(rows) == 1
        assert rows[0].title == 'Título posterior'
        assert rows[0].raw_data.get('provenance') is None
    finally:
        db.close()


def test_normalized_link_apply_rejects_snapshot_changed_before_apply(monkeypatch):
    monkeypatch.setenv('TENDERPROOF_PUBLISHER_USER_IDS', '7')
    monkeypatch.setenv('TENDERPROOF_PUBLICATION_ENABLED', 'true')
    db = _db()
    try:
        user = User(id=7, name='Reviewer', email='reviewer@example.test', password_hash='x')
        source = Source(name='Teste', base_url='https://example.test',
                        list_url='https://example.test/list', source_type='test')
        db.add_all([user, source])
        db.flush()
        concurso = Concurso(source_id=source.id, **_item())
        db.add(concurso)
        db.commit()
        authorization = {'actor_kind': 'human_reviewer', 'human_read': False,
                         'reference': 'T007-review', 'reference_sha256': 'a' * 64}
        plan = create_normalized_link_proposal(db, concurso_ids=[concurso.id], user=user,
                                               authorization=authorization)
        approve_normalized_link_proposal(db, proposal_id=plan['id'], proposal_hash=plan['proposal_hash'],
                                         fields=['publications'], user=user,
                                         authorization=authorization)
        concurso.titulo = 'Alterado depois do dry-run'
        db.commit()
        try:
            apply_normalized_link_proposal(db, proposal_id=plan['id'], proposal_hash=plan['proposal_hash'], user=user)
        except HTTPException as exc:
            assert exc.status_code == 409
        else:
            raise AssertionError('snapshot alterado deveria bloquear aplicação')
    finally:
        db.close()


def test_normalized_link_proposal_get_and_fallback_contract(monkeypatch):
    monkeypatch.setenv('TENDERPROOF_PUBLISHER_USER_IDS', '7')
    monkeypatch.setenv('TENDERPROOF_PUBLICATION_ENABLED', 'true')
    db = _db()
    try:
        user = User(id=7, name='Reviewer', email='reviewer@example.test', password_hash='x')
        source = Source(name='Teste', base_url='https://example.test', list_url='https://example.test/list', source_type='test')
        db.add_all([user, source]); db.flush()
        concurso = Concurso(source_id=source.id, **_item()); db.add(concurso); db.flush(); db.commit()
        plan = create_normalized_link_proposal(db, concurso_ids=[concurso.id], user=user)
        view = __import__('app.tenderproof.publication', fromlist=['get_proposal']).get_proposal(db, plan['id'], user)
        assert view['action'] == 'normalized_link_reference'
        assert view['targets'][0]['concurso_id'] == concurso.id
        assert view['stale'] is False
        assert CrawlService(db)._sync_publications(concurso, _item())
        row = db.scalar(select(ConcursoPublication).where(ConcursoPublication.concurso_id == concurso.id))
        assert ConcursoPublicationOut.model_validate(row).reference_only is True
    finally:
        db.close()


def test_normalized_link_proposal_http_get_is_not_run_dependent(monkeypatch):
    monkeypatch.setenv('TENDERPROOF_PUBLISHER_USER_IDS', '7')
    db = _db()
    try:
        user = User(id=7, name='Reviewer', email='reviewer@example.test', password_hash='x')
        source = Source(name='Teste', base_url='https://example.test', list_url='https://example.test/list', source_type='test')
        db.add_all([user, source]); db.flush()
        concurso = Concurso(source_id=source.id, **_item()); db.add(concurso); db.commit()
        plan = create_normalized_link_proposal(db, concurso_ids=[concurso.id], user=user)
        from app.tenderproof.publication_router import router
        app = FastAPI(); app.include_router(router)
        app.dependency_overrides[get_db] = lambda: db
        response = TestClient(app).get('/tenderproof/publications/proposals/' + plan['id'],
                                       headers={'Authorization': 'Bearer ' + create_access_token(user.id)})
        assert response.status_code == 200, response.text
        assert response.json()['action'] == 'normalized_link_reference'
    finally:
        db.close()


def test_normalized_link_apply_is_atomic_and_replay_idempotent(monkeypatch):
    monkeypatch.setenv('TENDERPROOF_PUBLISHER_USER_IDS', '7')
    monkeypatch.setenv('TENDERPROOF_PUBLICATION_ENABLED', 'true')
    db = _db()
    try:
        user = User(id=7, name='Reviewer', email='reviewer@example.test', password_hash='x')
        source = Source(name='Teste', base_url='https://example.test',
                        list_url='https://example.test/list', source_type='test')
        db.add_all([user, source]); db.flush()
        concurso = Concurso(source_id=source.id, **_item())
        db.add(concurso); db.commit()
        plan = create_normalized_link_proposal(db, concurso_ids=[concurso.id], user=user)
        assert db.execute(select(ConcursoPublication)).scalars().all() == []
        approve_normalized_link_proposal(db, proposal_id=plan['id'], proposal_hash=plan['proposal_hash'],
                                         fields=['publications'], user=user)
        first = apply_normalized_link_proposal(db, proposal_id=plan['id'], proposal_hash=plan['proposal_hash'], user=user)
        assert len(first['applied']) == 1
        assert len(db.execute(select(ConcursoPublication)).scalars().all()) == 1
        assert len(db.execute(select(ConcursoVersion)).scalars().all()) == 1
        assert len(db.execute(select(PublicationOutbox)).scalars().all()) == 1
        second = apply_normalized_link_proposal(db, proposal_id=plan['id'], proposal_hash=plan['proposal_hash'], user=user)
        assert second == first
        assert len(db.execute(select(ConcursoVersion)).scalars().all()) == 1
        assert len(db.execute(select(PublicationOutbox)).scalars().all()) == 1
    finally:
        db.close()


def test_normalized_link_apply_reconciles_preexisting_fallback(monkeypatch):
    """The 32-row failure mode is an existing fallback without its event."""
    monkeypatch.setenv('TENDERPROOF_PUBLISHER_USER_IDS', '7')
    monkeypatch.setenv('TENDERPROOF_PUBLICATION_ENABLED', 'true')
    db = _db()
    try:
        user = User(id=7, name='Reviewer', email='reviewer@example.test', password_hash='x')
        source = Source(name='Teste', base_url='https://example.test',
                        list_url='https://example.test/list', source_type='test')
        db.add_all([user, source]); db.flush()
        concurso = Concurso(source_id=source.id, **_item()); db.add(concurso); db.flush()
        # Simulate the crawler committing the fallback before the proposal.
        assert len(CrawlService(db)._sync_publications(concurso, _item())) == 1
        db.commit()
        plan = create_normalized_link_proposal(db, concurso_ids=[concurso.id], user=user)
        approve_normalized_link_proposal(db, proposal_id=plan['id'], proposal_hash=plan['proposal_hash'],
                                         fields=['publications'], user=user)
        result = apply_normalized_link_proposal(db, proposal_id=plan['id'], proposal_hash=plan['proposal_hash'], user=user)
        assert result['state'] == 'applied' and len(result['applied']) == 1
        assert db.query(ConcursoPublication).count() == 1
        assert db.query(ConcursoVersion).filter(ConcursoVersion.change_type == 'document_added').count() == 1
        assert db.query(PublicationOutbox).count() == 1
        assert result['applied'][0]['publication_count'] == 1
    finally:
        db.close()


def test_normalized_link_apply_rolls_back_all_targets_on_late_conflict(monkeypatch):
    monkeypatch.setenv('TENDERPROOF_PUBLISHER_USER_IDS', '7')
    monkeypatch.setenv('TENDERPROOF_PUBLICATION_ENABLED', 'true')
    db = _db()
    try:
        user = User(id=7, name='Reviewer', email='reviewer@example.test', password_hash='x')
        source = Source(name='Teste', base_url='https://example.test',
                        list_url='https://example.test/list', source_type='test')
        db.add_all([user, source]); db.flush()
        first = Concurso(source_id=source.id, **_item())
        second_item = _item(); second_item['external_id'] = 'fallback-2'; second_item['link_pagina'] = 'https://example.test/concursos/fallback-2'
        second = Concurso(source_id=source.id, **second_item)
        db.add_all([first, second]); db.commit()
        plan = create_normalized_link_proposal(db, concurso_ids=[first.id, second.id], user=user)
        approve_normalized_link_proposal(db, proposal_id=plan['id'], proposal_hash=plan['proposal_hash'],
                                         fields=['publications'], user=user)
        second.titulo = 'Alterado após aprovação'; db.commit()
        with pytest.raises(HTTPException) as exc:
            apply_normalized_link_proposal(db, proposal_id=plan['id'], proposal_hash=plan['proposal_hash'], user=user)
        assert exc.value.status_code == 409
        assert db.query(ConcursoPublication).count() == 0
        assert db.query(ConcursoVersion).count() == 0
        assert db.query(PublicationOutbox).count() == 0
    finally:
        db.close()


def test_new_collector_observation_records_publication_in_creation_version(monkeypatch):
    monkeypatch.setenv('LEGACY_CRAWLER_ENABLED', 'true')
    from app.config import get_settings
    get_settings.cache_clear()
    db = _db()
    try:
        source = Source(name='Teste', base_url='https://example.test',
                        list_url='https://example.test/list', source_type='test')
        db.add(source); db.commit()
        item = _item()
        connector = MagicMock()
        connector.crawl_with_diagnostics.return_value = CrawlResult(
            items=[item], run_data=CrawlRunData(candidates_found=1, status='success'))
        with patch('app.services.get_connector', return_value=connector):
            result = CrawlService(db).crawl_source(source.id)
        assert result['inserted'] == 1
        version = db.execute(select(ConcursoVersion)).scalar_one()
        assert version.changed_fields['publications_added']['new'][0]['link'] == item['link_edital']
        assert db.execute(select(ConcursoPublication)).scalar_one().link == item['link_edital']
    finally:
        get_settings.cache_clear()
        db.close()


def test_repair_proposal_reconciles_orphan_without_rewriting_observation(monkeypatch):
    monkeypatch.setenv('TENDERPROOF_PUBLISHER_USER_IDS', '7')
    monkeypatch.setenv('TENDERPROOF_PUBLICATION_ENABLED', 'true')
    db = _db()
    try:
        user = User(id=7, name='Reviewer', email='reviewer@example.test', password_hash='x')
        source = Source(name='Teste', base_url='https://example.test', list_url='https://example.test/list', source_type='test')
        db.add_all([user, source]); db.flush()
        concurso = Concurso(source_id=source.id, **_item()); db.add(concurso); db.flush()
        assert len(CrawlService(db)._sync_publications(concurso, _item())) == 1
        db.commit()
        plan = create_normalized_link_repair_proposal(db, concurso_ids=[concurso.id], user=user)
        approve_normalized_link_repair_proposal(db, proposal_id=plan['id'], proposal_hash=plan['proposal_hash'], fields=['publications'], user=user)
        result = apply_normalized_link_repair_proposal(db, proposal_id=plan['id'], proposal_hash=plan['proposal_hash'], user=user)
        assert result['late_reconciliation'] is True
        assert db.execute(select(ConcursoVersion)).scalar_one().change_type == 'document_added'
        assert len(db.execute(select(PublicationOutbox)).scalars().all()) == 1
    finally:
        db.close()
