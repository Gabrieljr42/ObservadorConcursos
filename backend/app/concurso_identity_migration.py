"""Explicit migration for multiple identified contests on one catalogue URL.

No rows are merged, rewritten or deleted. Upgrade refuses duplicate known IDs;
downgrade refuses repeated source/URL pairs. Never invoked automatically at boot.
"""
from sqlalchemy import MetaData, UniqueConstraint, inspect, text
from sqlalchemy.schema import CreateIndex, CreateTable
from app.concurso_identity import identity_predicate

REVISION = 'concurso-section-identity-001'
OLD = 'uq_concursos_source_link_pagina'
KNOWN = 'uq_concursos_source_external_known'
LEGACY = 'uq_concursos_source_link_legacy'


class IdentityMigrationBlocked(ValueError):
    pass


def _preflight(connection, downgrade):
    KNOWN_WHERE = identity_predicate(connection.dialect.name, known=True)
    LEGACY_WHERE = identity_predicate(connection.dialect.name, known=False)
    checks = [('source_url', 'source_id, link_pagina', '')] if downgrade else [
        ('source_external', 'source_id, external_id', 'WHERE '+KNOWN_WHERE),
        ('legacy_source_url', 'source_id, link_pagina', 'WHERE '+LEGACY_WHERE)]
    for label, columns, where in checks:
        count = connection.execute(text(f'SELECT COUNT(*) FROM (SELECT {columns} FROM concursos {where} GROUP BY {columns} HAVING COUNT(*) > 1) AS conflicts')).scalar_one()
        if count:
            raise IdentityMigrationBlocked(f'{label}: {count} duplicate identity groups; explicit reconciliation required, no rows changed')


def _indexes(connection, downgrade):
    KNOWN_WHERE = identity_predicate(connection.dialect.name, known=True)
    LEGACY_WHERE = identity_predicate(connection.dialect.name, known=False)
    for name in (KNOWN, LEGACY):
        connection.exec_driver_sql(f'DROP INDEX IF EXISTS {name}')
    if not downgrade:
        connection.exec_driver_sql(f'CREATE UNIQUE INDEX {KNOWN} ON concursos (source_id, external_id) WHERE {KNOWN_WHERE}')
        connection.exec_driver_sql(f'CREATE UNIQUE INDEX {LEGACY} ON concursos (source_id, link_pagina) WHERE {LEGACY_WHERE}')


def _sqlite_rebuild(connection, downgrade):
    inspector = inspect(connection)
    old_constraints = [c for c in inspector.get_unique_constraints('concursos')
                       if c['column_names'] == ['source_id', 'link_pagina']]
    if not old_constraints and not downgrade:
        _indexes(connection, False)
        return
    metadata = MetaData()
    metadata.reflect(bind=connection, only=['concursos'])
    original = metadata.tables['concursos']
    temporary_name = 'concursos_identity_migration'
    if inspector.has_table(temporary_name):
        raise IdentityMigrationBlocked('reserved migration table exists; inspect prior state first')
    ddl = connection.exec_driver_sql("SELECT sql FROM sqlite_master WHERE type='table' AND name='concursos'").scalar_one()
    triggers = list(connection.exec_driver_sql("SELECT sql FROM sqlite_master WHERE type='trigger' AND tbl_name='concursos' AND sql IS NOT NULL").scalars())
    sequence = None
    if 'AUTOINCREMENT' in ddl.upper():
        sequence = connection.exec_driver_sql("SELECT seq FROM sqlite_sequence WHERE name='concursos'").scalar_one_or_none()
    original_indexes = [index for index in original.indexes if index.name not in (KNOWN, LEGACY)]
    temporary = original.to_metadata(metadata, name=temporary_name)
    temporary.indexes.clear()
    for constraint in list(temporary.constraints):
        if isinstance(constraint, UniqueConstraint) and list(constraint.columns.keys()) == ['source_id', 'link_pagina']:
            temporary.constraints.remove(constraint)
    if downgrade:
        temporary.append_constraint(UniqueConstraint('source_id', 'link_pagina', name=OLD))
    if 'AUTOINCREMENT' in ddl.upper():
        temporary.dialect_options['sqlite']['autoincrement'] = True
    connection.execute(CreateTable(temporary))
    quote = connection.dialect.identifier_preparer.quote
    columns = ', '.join(quote(column.name) for column in original.columns)
    connection.exec_driver_sql(f'INSERT INTO {temporary_name} ({columns}) SELECT {columns} FROM concursos')
    connection.exec_driver_sql('DROP TABLE concursos')
    connection.exec_driver_sql(f'ALTER TABLE {temporary_name} RENAME TO concursos')
    for index in original_indexes:
        connection.execute(CreateIndex(index))
    _indexes(connection, downgrade)
    for trigger in triggers:
        connection.exec_driver_sql(trigger)
    if sequence is not None:
        connection.exec_driver_sql("UPDATE sqlite_sequence SET seq=MAX(seq, ?) WHERE name='concursos'", (sequence,))
    if connection.exec_driver_sql('PRAGMA foreign_key_check').first():
        raise IdentityMigrationBlocked('foreign key validation failed; rebuild rolled back')


def _postgres_change(connection, downgrade):
    connection.exec_driver_sql('LOCK TABLE concursos IN ACCESS EXCLUSIVE MODE')
    _preflight(connection, downgrade)
    inspector = inspect(connection)
    constraints = [c for c in inspector.get_unique_constraints('concursos')
                   if c['column_names'] == ['source_id', 'link_pagina']]
    if downgrade:
        # Install the old arbiter before removing the new ones, inside one lock.
        if not constraints:
            connection.exec_driver_sql(f'ALTER TABLE concursos ADD CONSTRAINT {OLD} UNIQUE (source_id, link_pagina)')
        _indexes(connection, True)
    else:
        _indexes(connection, False)
        for constraint in constraints:
            name = connection.dialect.identifier_preparer.quote(constraint['name'])
            connection.exec_driver_sql(f'ALTER TABLE concursos DROP CONSTRAINT {name}')


def migrate(engine, *, downgrade=False):
    if engine.dialect.name == 'postgresql':
        with engine.begin() as connection:
            _postgres_change(connection, downgrade)
    elif engine.dialect.name == 'sqlite':
        with engine.connect() as connection:
            foreign_keys = connection.exec_driver_sql('PRAGMA foreign_keys').scalar_one()
            legacy_alter = connection.exec_driver_sql('PRAGMA legacy_alter_table').scalar_one()
            connection.commit()
            connection.exec_driver_sql('PRAGMA foreign_keys=OFF')
            connection.exec_driver_sql('PRAGMA legacy_alter_table=ON')
            connection.commit()
            try:
                connection.exec_driver_sql('BEGIN IMMEDIATE')
                _preflight(connection, downgrade)
                _sqlite_rebuild(connection, downgrade)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.exec_driver_sql(f'PRAGMA foreign_keys={int(foreign_keys)}')
                connection.exec_driver_sql(f'PRAGMA legacy_alter_table={int(legacy_alter)}')
                connection.commit()
    else:
        raise IdentityMigrationBlocked('only SQLite and PostgreSQL migrations are implemented')
    return {'revision': REVISION, 'direction': 'downgrade' if downgrade else 'upgrade',
            'dialect': engine.dialect.name, 'row_values_changed': False,
            'physical_table_rebuild': engine.dialect.name == 'sqlite'}


def upgrade(engine):
    return migrate(engine)


def downgrade(engine):
    return migrate(engine, downgrade=True)


if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--downgrade', action='store_true')
    args = parser.parse_args()
    if not args.apply:
        parser.error('--apply requires an explicitly configured and authorized target database')
    from app.database import engine
    print(json.dumps(migrate(engine, downgrade=args.downgrade)))
