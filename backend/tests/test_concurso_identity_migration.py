"""Identity schema migration and collector compatibility on disposable databases."""
import os
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
pytestmark = pytest.mark.usefixtures('legacy_crawler_enabled')
from sqlalchemy import MetaData, UniqueConstraint, create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema, DropSchema

from app.models import Concurso, Source
from app.concurso_identity_migration import upgrade, downgrade, IdentityMigrationBlocked, KNOWN, LEGACY, OLD
from app.services import CrawlService, AmbiguousContestIdentity


@pytest.fixture(params=['sqlite', 'postgresql'])
def legacy_engine(request, tmp_path):
    schema, admin = None, None
    if request.param == 'postgresql':
        url = os.getenv('TENDERPROOF_TEST_POSTGRES_URL')
        if not url:
            pytest.skip('explicit disposable PostgreSQL URL not configured')
        parsed = make_url(url)
        if parsed.host != '127.0.0.1' or parsed.database != 'tenderproof_acceptance' or parsed.username != 'fixture':
            raise ValueError('only the disposable loopback PostgreSQL fixture is allowed')
        schema = 'identity_' + uuid.uuid4().hex
        admin = create_engine(url)
        with admin.begin() as connection:
            connection.execute(CreateSchema(schema))
        engine = create_engine(url, connect_args={'options': '-csearch_path='+schema})
    else:
        engine = create_engine('sqlite:///'+str(tmp_path/'identity.sqlite'), connect_args={'timeout': 15})
    metadata = MetaData()
    Source.__table__.to_metadata(metadata)
    table = Concurso.__table__.to_metadata(metadata)
    for index in list(table.indexes):
        if index.name in (KNOWN, LEGACY):
            table.indexes.remove(index)
    table.append_constraint(UniqueConstraint('source_id', 'link_pagina', name=OLD))
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(metadata.tables['sources'].insert().values(id=1, name='Foundation', source_type='fixture', base_url='https://example.org'))
    try:
        yield engine
    finally:
        engine.dispose()
        if admin:
            with admin.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
            admin.dispose()


def insert(engine, external, url='https://example.org/catalogue', *, title='Observed contest'):
    with Session(engine) as db:
        contest = Concurso(source_id=1, external_id=external, banca='Foundation', titulo=title,
                           link_pagina=url, content_hash='a'*64)
        db.add(contest)
        db.commit()
        return contest.id


def rows(engine):
    with engine.connect() as connection:
        return [dict(row) for row in connection.execute(text('SELECT * FROM concursos ORDER BY id')).mappings()]


def test_upgrade_idempotent_preserves_rows_and_new_identity_arbiters(legacy_engine):
    engine = legacy_engine
    insert(engine, 'notice-1')
    before = rows(engine)
    upgrade(engine)
    upgrade(engine)
    assert rows(engine) == before
    insert(engine, 'notice-2')  # same URL, different known ID
    with pytest.raises(IntegrityError):
        insert(engine, 'notice-1', 'https://example.org/other-url')
    insert(engine, None, 'https://example.org/legacy')
    for empty in (None, '', '   '):
        with pytest.raises(IntegrityError):
            insert(engine, empty, 'https://example.org/legacy')
    assert len(rows(engine)) == 3


def test_upgrade_refuses_duplicate_historical_external_without_changes(legacy_engine):
    engine = legacy_engine
    insert(engine, 'same', 'https://example.org/one')
    insert(engine, 'same', 'https://example.org/two')
    before = rows(engine)
    with pytest.raises(IdentityMigrationBlocked, match='source_external'):
        upgrade(engine)
    assert rows(engine) == before
    with pytest.raises(IntegrityError):
        insert(engine, 'different', 'https://example.org/one')


def test_downgrade_refuses_new_shared_urls_and_preserves_new_schema(legacy_engine):
    engine = legacy_engine
    upgrade(engine)
    insert(engine, 'one')
    insert(engine, 'two')
    before = rows(engine)
    with pytest.raises(IdentityMigrationBlocked, match='source_url'):
        downgrade(engine)
    assert rows(engine) == before
    insert(engine, 'three')
    with pytest.raises(IntegrityError):
        insert(engine, 'one', 'https://example.org/different')


def test_safe_downgrade_then_upgrade_preserves_legacy_constraint(legacy_engine):
    engine = legacy_engine
    insert(engine, 'one')
    before = rows(engine)
    upgrade(engine)
    downgrade(engine)
    downgrade(engine)
    assert rows(engine) == before
    with pytest.raises(IntegrityError):
        insert(engine, 'two')
    upgrade(engine)
    insert(engine, 'two')


@pytest.mark.parametrize('external', ['same-known-id', None])
def test_concurrent_duplicate_insert_has_one_winner(legacy_engine, external):
    engine = legacy_engine
    upgrade(engine)
    def attempt(index):
        try:
            insert(engine, external, title='racing observation '+str(index))
            return 'inserted'
        except IntegrityError:
            return 'duplicate_rejected'
    with ThreadPoolExecutor(2) as pool:
        outcomes = list(pool.map(attempt, range(2)))
    assert sorted(outcomes) == ['duplicate_rejected', 'inserted']
    assert len(rows(engine)) == 1


def test_legacy_collector_does_not_merge_distinct_ids_or_pick_ambiguous_url(legacy_engine):
    engine = legacy_engine
    upgrade(engine)
    first = insert(engine, 'one')
    with Session(engine) as db:
        service = CrawlService(db)
        assert service._find_existing_concurso(1, {'external_id': 'two', 'link_pagina': 'https://example.org/catalogue'}) is None
        assert service._find_existing_concurso(1, {'link_pagina': 'https://example.org/catalogue'}).id == first
    second = insert(engine, 'two')
    with Session(engine) as db:
        service = CrawlService(db)
        assert service._find_existing_concurso(1, {'external_id': 'one', 'link_pagina': 'https://example.org/catalogue'}).id == first
        assert service._find_existing_concurso(1, {'external_id': 'two', 'link_pagina': 'https://example.org/catalogue'}).id == second
        with pytest.raises(AmbiguousContestIdentity):
            service._find_existing_concurso(1, {'link_pagina': 'https://example.org/catalogue'})
        with pytest.raises(AmbiguousContestIdentity):
            service._find_existing_concurso(99, {'link_pagina': 'https://example.org/catalogue'})


def test_url_only_crawl_preserves_known_external_id_and_retries_idempotently(legacy_engine, monkeypatch):
    from types import SimpleNamespace
    from app.database import Base
    from app import services
    from app.connectors.base import CrawlResult, CrawlRunData
    engine = legacy_engine
    upgrade(engine)
    Base.metadata.create_all(engine)
    identifier = insert(engine, 'reviewed-id')
    item = {'external_id': None, 'banca': 'Foundation', 'titulo': 'Updated observation',
            'link_pagina': 'https://example.org/catalogue', 'content_hash': 'b'*64}
    connector = SimpleNamespace(crawl_with_diagnostics=lambda: CrawlResult(items=[item], run_data=CrawlRunData(status='success', candidates_found=1)))
    monkeypatch.setattr(services, 'get_connector', lambda *args, **kwargs: connector)
    with Session(engine) as db:
        service = CrawlService(db)
        first = service.crawl_source(1)
        second = service.crawl_source(1)
        assert first['status'] == second['status'] == 'success'
        assert first['updated'] == 1 and second['unchanged'] == 1
        assert db.get(Concurso, identifier).external_id == 'reviewed-id'
        assert len(db.scalars(select(Concurso)).all()) == 1


def test_sqlite_rebuild_preserves_child_foreign_keys_indexes_and_audit_triggers(tmp_path):
    engine = create_engine('sqlite:///'+str(tmp_path/'old.sqlite'))
    with engine.begin() as connection:
        connection.exec_driver_sql('CREATE TABLE concursos (id INTEGER PRIMARY KEY AUTOINCREMENT, source_id INTEGER NOT NULL, external_id TEXT, link_pagina TEXT NOT NULL, payload TEXT, CONSTRAINT uq_concursos_source_link_pagina UNIQUE(source_id, link_pagina))')
        connection.exec_driver_sql('CREATE TABLE children (id INTEGER PRIMARY KEY, concurso_id INTEGER REFERENCES concursos(id))')
        connection.exec_driver_sql('CREATE TABLE audit (contest_id INTEGER)')
        connection.exec_driver_sql('CREATE INDEX ix_payload ON concursos(payload)')
        connection.exec_driver_sql('CREATE TRIGGER record_concurso_insert AFTER INSERT ON concursos BEGIN INSERT INTO audit VALUES (NEW.id); END')
        connection.exec_driver_sql("INSERT INTO concursos VALUES (100, 1, 'one', 'https://example.org/page', 'unchanged')")
        connection.exec_driver_sql('INSERT INTO children VALUES (1,100)')
        connection.exec_driver_sql('PRAGMA foreign_keys=ON')
    upgrade(engine)
    with engine.begin() as connection:
        assert connection.exec_driver_sql('SELECT * FROM children').all() == [(1, 100)]
        assert connection.exec_driver_sql('SELECT * FROM audit').all() == [(100,)]
        assert not connection.exec_driver_sql('PRAGMA foreign_key_check').all()
        connection.exec_driver_sql("INSERT INTO concursos(source_id,external_id,link_pagina,payload) VALUES (1,'two','https://example.org/page','second')")
        assert connection.exec_driver_sql('SELECT * FROM audit ORDER BY contest_id').all() == [(100,), (101,)]
        assert any(row[1] == 'ix_payload' for row in connection.exec_driver_sql('PRAGMA index_list(concursos)'))
    engine.dispose()


@pytest.mark.parametrize('blank', ['\t', '\r\n', '\v\f', '\u00a0', '\u2003', ' \t\n\u3000'])
def test_all_blank_whitespace_is_legacy_in_schema_and_collector(legacy_engine, blank):
    from app.concurso_identity import identity_is_blank
    upgrade(legacy_engine)
    insert(legacy_engine, blank)
    assert identity_is_blank(blank)
    with pytest.raises(IntegrityError):
        insert(legacy_engine, None)
    with Session(legacy_engine) as db:
        row = CrawlService(db)._find_existing_concurso(1, {'external_id': 'section-new', 'link_pagina': 'https://example.org/catalogue'})
        assert row.external_id == blank


def test_concurrent_stale_legacy_promotions_do_not_overwrite_identity(legacy_engine):
    import threading
    from sqlalchemy.exc import OperationalError
    upgrade(legacy_engine)
    original = insert(legacy_engine, None)
    barrier = threading.Barrier(2)
    def promote(external):
        with Session(legacy_engine) as db:
            service = CrawlService(db)
            item = {'external_id': external, 'link_pagina': 'https://example.org/catalogue'}
            row = service._find_existing_concurso(1, item)
            assert row.id == original and row.external_id is None
            barrier.wait(timeout=10)
            try:
                service._claim_external_identity(row, item)
                row.external_id = external
                db.commit()
                return ('winner', external)
            except (AmbiguousContestIdentity, OperationalError):
                db.rollback()
                return ('retry', external)
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(promote, ['section-one', 'section-two']))
    assert sorted(x[0] for x in outcomes) == ['retry', 'winner']
    winner = next(value for state, value in outcomes if state == 'winner')
    loser = next(value for state, value in outcomes if state == 'retry')
    assert rows(legacy_engine)[0]['external_id'] == winner
    with Session(legacy_engine) as db:
        assert CrawlService(db)._find_existing_concurso(1, {'external_id': loser, 'link_pagina': 'https://example.org/catalogue'}) is None
    insert(legacy_engine, loser)
    assert {r['external_id'] for r in rows(legacy_engine)} == {winner, loser}


def test_upgrade_whitespace_duplicate_preflight_preserves_rows(legacy_engine):
    # Old schema permits only distinct URLs: emulate the already deployed v1 indexes.
    upgrade(legacy_engine)
    with legacy_engine.begin() as c:
        c.exec_driver_sql(f'DROP INDEX {LEGACY}')
        c.exec_driver_sql(f'DROP INDEX {KNOWN}')
        c.exec_driver_sql(f"CREATE UNIQUE INDEX {KNOWN} ON concursos(source_id, external_id) WHERE external_id IS NOT NULL AND trim(external_id) <> ''")
        c.exec_driver_sql(f"CREATE UNIQUE INDEX {LEGACY} ON concursos(source_id, link_pagina) WHERE external_id IS NULL OR trim(external_id) = ''")
    insert(legacy_engine, '\t')
    insert(legacy_engine, None)
    before = rows(legacy_engine)
    with pytest.raises(IdentityMigrationBlocked, match='legacy_source_url'):
        upgrade(legacy_engine)
    assert rows(legacy_engine) == before



def test_claim_preserves_orm_identity_for_audit_and_unchanged_timestamp(legacy_engine):
    upgrade(legacy_engine)
    row_id = insert(legacy_engine, None)
    with Session(legacy_engine) as db:
        row = db.get(Concurso, row_id)
        timestamp = row.updated_at
        service = CrawlService(db)
        service._claim_external_identity(row, {'external_id': 'promoted'})
        assert row.external_id is None
        assert db.execute(text('SELECT updated_at FROM concursos WHERE id=:id'), {'id': row_id}).scalar_one() == (timestamp if legacy_engine.dialect.name == 'postgresql' else timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'))
        db.rollback()
    assert rows(legacy_engine)[0]['external_id'] is None


def test_legacy_promotion_creates_identity_audit_once(legacy_engine, monkeypatch):
    from types import SimpleNamespace
    from app.database import Base
    from app import services
    from app.connectors.base import CrawlResult, CrawlRunData
    engine = legacy_engine
    upgrade(engine)
    Base.metadata.create_all(engine)
    identifier = insert(engine, None)
    item = {'external_id': 'reviewed-id', 'banca': 'Foundation', 'titulo': 'Updated observation',
            'link_pagina': 'https://example.org/catalogue', 'content_hash': 'b'*64}
    connector = SimpleNamespace(crawl_with_diagnostics=lambda: CrawlResult(items=[item], run_data=CrawlRunData(status='success', candidates_found=1)))
    monkeypatch.setattr(services, 'get_connector', lambda *args, **kwargs: connector)
    with Session(engine) as db:
        service = CrawlService(db)
        first = service.crawl_source(1)
        second = service.crawl_source(1)
        assert first['status'] == second['status'] == 'success'
        assert first['updated'] == 1 and second['unchanged'] == 1
        assert db.get(Concurso, identifier).external_id == 'reviewed-id'
        assert len(db.scalars(select(Concurso)).all()) == 1

        from app.models import ConcursoVersion
        versions = db.scalars(select(ConcursoVersion).where(ConcursoVersion.concurso_id == identifier)).all()
        assert len(versions) == 1
        assert versions[0].changed_fields['external_id'] == {'label': 'identificador externo', 'old': None, 'new': 'reviewed-id'}
