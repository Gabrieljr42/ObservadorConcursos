"""Replay preserved real pilot PDFs through publication in a disposable SQLite DB.

No network, original-store writes, or production DB access. Outputs omit URLs to
avoid exposing temporary signed acquisition destinations.
"""
from __future__ import annotations
import argparse
from collections import Counter
from contextlib import ExitStack, closing
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from fastapi import HTTPException
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Concurso, ConcursoVersion, Source, User, Notification
from app.tenderproof.contracts import TenderProofRun
from app.tenderproof import publication as pub
from app.tenderproof.publication_models import PublicationOutbox


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preserved-root', required=True)
    parser.add_argument('--inventory', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--sources', nargs='+', help='Explicit source strategies to replay; omitted means all')
    parser.add_argument('--max-pages', type=int, default=60, help='Explicit isolated processing page limit (default 60)')
    args = parser.parse_args()
    if not 1 <= args.max_pages <= 1000:
        parser.error('--max-pages must be between 1 and 1000')
    root = Path(args.preserved_root).resolve()
    inventory = {s['source_type']: s for s in json.loads(Path(args.inventory).read_text(encoding='utf-8'))['sources']}
    with sqlite3.connect((root/'operational.sqlite3').as_uri()+'?mode=ro', uri=True) as connection:
        runs = [TenderProofRun.model_validate_json(row[0]) for row in connection.execute('SELECT payload FROM runs ORDER BY saved_at, run_id')]
    runs = [r for r in runs if r.execution_status.value == 'completed' and r.validation_status.value == 'valid' and not r.is_synthetic_sample and r.mode != 'mock']
    if args.sources:
        runs = [r for r in runs if r.source in args.sources]
    class PreservedBytes:
        def load_artifact_bytes(self, artifact):
            filename = Path(artifact.storage_path.replace('\\', '/')).name
            path = (root/'artifacts'/filename).resolve()
            if path.parent != (root/'artifacts').resolve():
                raise ValueError('artifact outside preserved directory')
            return path.read_bytes()
    report = {'generated_at': datetime.now(timezone.utc).isoformat(), 'scope': 'real preserved pilot PDFs; disposable SQLite publication; no production writes or network',
              'input_operational_db': str(root/'operational.sqlite3'), 'samples': [], 'network_requests': 0, 'production_enabled': False, 'max_pages': args.max_pages, 'source_filter': args.sources}
    previous = dict(os.environ)
    try:
        with tempfile.TemporaryDirectory(prefix='tp-canonical-real-') as temporary:
            os.environ['TENDERPROOF_ARTIFACT_DIR'] = str(Path(temporary)/'artifacts')
            # Carry current documentary holds into the isolated publication
            # volume. Copy through SQLite backup so the source stays read-only
            # and WAL contents are included; do not discard holds by switching
            # to an empty test queue while replaying older runs.
            source_queue = root/'continuous.sqlite3'
            if source_queue.exists():
                with closing(sqlite3.connect(source_queue.as_uri()+'?mode=ro', uri=True)) as src, closing(sqlite3.connect(Path(temporary)/'continuous.sqlite3')) as dst:
                    src.backup(dst)
            os.environ['TENDERPROOF_MAX_PAGES'] = str(args.max_pages)
            os.environ['TENDERPROOF_PUBLICATION_ENABLED'] = 'true'
            os.environ['TENDERPROOF_PUBLICATION_ALLOW_SYNTHETIC'] = 'false'
            os.environ['TENDERPROOF_PUBLISHER_USER_IDS'] = ','.join(str(i) for i in {r.owner_user_id for r in runs})
            engine = create_engine('sqlite:///'+str(Path(temporary)/'canonical.sqlite3'))
            Base.metadata.create_all(engine)
            factory = sessionmaker(engine, expire_on_commit=False)
            with ExitStack() as cleanup, factory() as db:
                cleanup.callback(engine.dispose)
                for user_id in {r.owner_user_id for r in runs}:
                    db.add(User(id=user_id, name='Isolated evidence reviewer', email=f'fixture-{user_id}@example.test', password_hash='unused', is_active=True))
                for source_key in {r.source for r in runs}:
                    item = inventory[source_key]
                    db.add(Source(name=item['banca'], base_url=item['base_url'], source_type=source_key, active=False))
                db.commit()
                for run in runs:
                    sample = {'run_id': run.run_id, 'source': run.source, 'document_sha256': run.artifact.sha256,
                              'fields': {f.field_name: {'value': f.value, 'state': f.state.value} for f in run.fields}, 'synthetic': False}
                    try:
                        user = db.get(User, run.owner_user_id)
                        proposal = pub.create_proposal(db, run=run, user=user, store=PreservedBytes())
                        reviewed = pub.approve_proposal(db, proposal_id=proposal['id'], proposal_hash=proposal['proposal_hash'], fields=proposal['eligible_fields'], user=user, store=PreservedBytes())
                        result = pub.apply_proposal(db, proposal_id=reviewed['id'], proposal_hash=reviewed['proposal_hash'], user=user, store=PreservedBytes())
                        repeated = pub.apply_proposal(db, proposal_id=reviewed['id'], proposal_hash=reviewed['proposal_hash'], user=user, store=PreservedBytes())
                        assert repeated['version_id'] == result['version_id'] and repeated['concurso_id'] == result['concurso_id']
                        sample.update(state=result['state'], action=result['action'], concurso_id=result['concurso_id'], proposal_id=result['id'],
                                      version_id=result['version_id'], approved_fields=result['approved_fields'], diff={k: (v if not k.startswith('link_') else {'label': v['label'], 'old': '[URL preservada no ledger]' if v['old'] else None, 'new': '[URL preservada no ledger]' if v['new'] else None}) for k,v in result['result']['diff'].items()}, repeat_same_result=True)
                    except HTTPException as exc:
                        db.rollback()
                        sample.update(state='blocked', status_code=exc.status_code, reason=exc.detail)
                    report['samples'].append(sample)
                    print(json.dumps({'run_id': run.run_id, 'source': run.source, 'state': sample['state']}), flush=True)
                report['counts'] = {name: db.scalar(select(func.count()).select_from(model)) for name, model in [('concursos', Concurso), ('versions', ConcursoVersion), ('outbox', PublicationOutbox), ('notifications', Notification)]}
                report['states'] = dict(Counter(s['state'] for s in report['samples']))
                report['sources_with_creation'] = sorted({s['source'] for s in report['samples'] if s.get('action') == 'create' and s['state'] == 'applied'})
            engine.dispose()
        report['temporary_database_removed'] = not Path(temporary).exists()
    finally:
        os.environ.clear()
        os.environ.update(previous)
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('counts', 'states', 'sources_with_creation', 'temporary_database_removed')}))


if __name__ == '__main__':
    main()
