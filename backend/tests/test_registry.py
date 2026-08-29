import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.connectors.registry import MASTER_SOURCES, get_connector, seed_master_sources
from app.database import Base
from app.models import Source


def test_master_sources_count_and_uniqueness():
    assert len(MASTER_SOURCES) == 99, f'Expected 99 sources in catalog, found {len(MASTER_SOURCES)}'

    source_types = [s.source_type for s in MASTER_SOURCES]
    assert len(source_types) == len(set(source_types)), 'Duplicate source_type found in MASTER_SOURCES!'

    for defn in MASTER_SOURCES:
        assert defn.source_type, 'source_type must not be empty'
        assert defn.name, 'name must not be empty'
        assert defn.base_url.startswith(('http://', 'https://')), f'Invalid base_url: {defn.base_url}'
        assert len(defn.list_urls) >= 1, f'No list_urls specified for {defn.source_type}'


def test_get_connector_instantiation_for_all_99_sources():
    for defn in MASTER_SOURCES:
        connector = get_connector(defn.source_type)
        assert connector is not None
        assert connector.base_url is not None
        assert hasattr(connector, 'crawl')


def test_seed_master_sources_in_database():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # First seed: all 99 inserted
        res1 = seed_master_sources(db)
        assert res1['total_master_sources'] == 99
        assert res1['created'] == 99
        assert res1['updated'] == 0
        assert res1['unchanged'] == 0

        count = len(db.execute(select(Source)).scalars().all())
        assert count == 99

        # Second seed: 0 inserted, 0 updated, 99 unchanged
        res2 = seed_master_sources(db)
        assert res2['created'] == 0
        assert res2['updated'] == 0
        assert res2['unchanged'] == 99

    finally:
        db.close()
