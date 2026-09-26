"""Offline Garibaldi publication-ledger checks; no PDF/network is implied."""
import json
from pathlib import Path

from sqlalchemy import select

from app.models import Concurso, ConcursoPublication, ConcursoVersion, Source, User
from app.services import CrawlService
from app.tenderproof.publication import (
    approve_normalized_link_proposal,
    apply_normalized_link_proposal,
    create_normalized_link_proposal,
)
from app.tenderproof.publication_models import PublicationOutbox
from test_publication_fallback import _db


MANIFEST = Path(__file__).parents[2] / 'docs' / 'execucao' / 'evidencias' / 'T004' / 'garibaldi-publications-offline-manifest-20260913.json'


def _fixture(monkeypatch):
    monkeypatch.setenv('TENDERPROOF_PUBLISHER_USER_IDS', '7')
    monkeypatch.setenv('TENDERPROOF_PUBLICATION_ENABLED', 'true')
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    db = _db()
    user = User(id=7, name='Garibaldi reviewer', email='garibaldi@example.test', password_hash='x')
    source = Source(id=49, name='Legalle Concursos', base_url='https://portal.editais.legalleconcursos.com.br',
                    list_url='https://portal.editais.legalleconcursos.com.br/edital', source_type='legalle_open')
    db.add_all([user, source]); db.flush()
    documents = [{k: item[k] for k in ('title', 'kind', 'url', 'sha256')} for item in manifest['documents']]
    raw = {'tenderproof': {'amendments': [{'base_document': documents[0], 'amendment_documents': documents[1:]}]}}
    contest = Concurso(source_id=49, external_id='2486', banca='Legalle Concursos', titulo='Município de Garibaldi',
                       orgao='Prefeitura Municipal De Garibaldi', edital_numero='04/2025',
                       link_pagina=manifest['identity']['detail_url'], link_edital=documents[0]['url'],
                       edital_data=None, raw_data=raw, content_hash='garibaldi-offline-catalogue')
    db.add(contest); db.commit()
    return db, user, contest, manifest, documents


def test_garibaldi_four_document_proposal_replay_partial_and_no_false_field_change(monkeypatch):
    db, user, contest, manifest, documents = _fixture(monkeypatch)
    try:
        # Simulate one publication already present before the normal proposal.
        partial = dict(contest.raw_data)
        partial['publications'] = [{
            'title': documents[0]['title'], 'publication_type': 'edital', 'publication_date': None,
            'link': documents[0]['url'], 'content_hash': documents[0]['sha256'],
            'source': 'raw_data.tenderproof.amendments', 'provenance': {'reference_only': True},
        }]
        CrawlService(db)._sync_publications(contest, {**contest.__dict__, 'raw_data': partial})
        db.commit()

        plan = create_normalized_link_proposal(db, concurso_ids=[contest.id], user=user)
        approve_normalized_link_proposal(db, proposal_id=plan['id'], proposal_hash=plan['proposal_hash'],
                                         fields=['publications'], user=user)
        first = apply_normalized_link_proposal(db, proposal_id=plan['id'], proposal_hash=plan['proposal_hash'], user=user)
        assert first['state'] == 'applied' and len(first['applied']) == 1
        assert db.scalar(select(__import__('sqlalchemy').func.count()).select_from(ConcursoPublication)) == 4
        version = db.scalar(select(ConcursoVersion).where(ConcursoVersion.concurso_id == contest.id))
        assert set(version.changed_fields) == {'publications_added'}
        assert 'cargos' not in version.changed_fields and 'resultado_final_prazo' not in version.changed_fields
        assert db.scalar(select(__import__('sqlalchemy').func.count()).select_from(PublicationOutbox)) == 1

        second = apply_normalized_link_proposal(db, proposal_id=plan['id'], proposal_hash=plan['proposal_hash'], user=user)
        assert second == first
        assert db.scalar(select(__import__('sqlalchemy').func.count()).select_from(ConcursoPublication)) == 4
        assert db.scalar(select(__import__('sqlalchemy').func.count()).select_from(ConcursoVersion)) == 1
        assert db.scalar(select(__import__('sqlalchemy').func.count()).select_from(PublicationOutbox)) == 1
    finally:
        db.close()


def test_garibaldi_four_document_initial_sync_is_idempotent(monkeypatch):
    db, _, contest, _, documents = _fixture(monkeypatch)
    try:
        item = dict(contest.__dict__)
        item['raw_data'] = {'publications': [
            {'title': document['title'], 'publication_type': 'edital' if document['kind'] == 'edital' else 'errata',
             'publication_date': None, 'link': document['url'], 'content_hash': document['sha256'],
             'source': 'raw_data.tenderproof.amendments', 'provenance': {'reference_only': True}}
            for document in documents]}
        first = CrawlService(db)._sync_publications(contest, item)
        second = CrawlService(db)._sync_publications(contest, item)
        assert len(first) == 4 and second == []
        assert db.scalar(select(__import__('sqlalchemy').func.count()).select_from(ConcursoPublication)) == 4
    finally:
        db.close()
