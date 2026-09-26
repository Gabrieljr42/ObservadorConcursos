"""Disposable PostgreSQL review for T007; writes only to the review container."""
import os
import sys
sys.path.insert(0, 'backend')
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Concurso, ConcursoPublication, ConcursoVersion, Source, User
from app.tenderproof.publication_models import PublicationOutbox
from app.services import CrawlService
sys.path.insert(0, '/app/tests')
sys.path.insert(0, 'backend/tests')
from test_publication_fallback import _item
from app.tenderproof.publication import create_normalized_link_proposal, approve_normalized_link_proposal, apply_normalized_link_proposal

url = os.environ['T007_REVIEW_PG_URL']
engine = create_engine(url)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()
try:
    os.environ['TENDERPROOF_PUBLISHER_USER_IDS'] = '7'
    os.environ['TENDERPROOF_PUBLICATION_ENABLED'] = 'true'
    user = User(id=7, name='reviewer', email='reviewer@invalid.test', password_hash='x')
    source = Source(name='review', base_url='https://example.test', list_url='https://example.test/list', source_type='test')
    db.add_all([user, source]); db.flush()
    contest = Concurso(source_id=source.id, **_item()); db.add(contest); db.commit()
    plan = create_normalized_link_proposal(db, concurso_ids=[contest.id], user=user)
    approve_normalized_link_proposal(db, proposal_id=plan['id'], proposal_hash=plan['proposal_hash'], fields=['publications'], user=user)
    result = apply_normalized_link_proposal(db, proposal_id=plan['id'], proposal_hash=plan['proposal_hash'], user=user)
    print({'dialect': engine.dialect.name, 'state': result['state'], 'applied': len(result.get('applied', [])), 'skipped': len(result.get('skipped', [])), 'publications': db.scalar(select(__import__('sqlalchemy').func.count()).select_from(ConcursoPublication)), 'versions': db.scalar(select(__import__('sqlalchemy').func.count()).select_from(ConcursoVersion)), 'outbox': db.scalar(select(__import__('sqlalchemy').func.count()).select_from(PublicationOutbox))})
finally:
    db.close(); engine.dispose()
