"""Read preserved replay volumes; backup/restore into new isolated directories."""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tenderproof.operational_backup import backup, restore, verify

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT.parent / 'docs'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def pdf_categories(pdfs):
    return {prefix: {'files': sum(path.startswith(prefix + '/') for path in pdfs),
        'bytes': sum(row['bytes'] for path, row in pdfs.items() if path.startswith(prefix + '/'))}
        for prefix in ('artifacts', 'processing')}


def database_inventory(path):
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as db:
        assert db.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
        tables = {}
        for (table,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
            safe = '"' + table.replace('"', '""') + '"'
            # All current operational tables contain scalar JSON/SQL values.
            rows = sorted(json.dumps(list(row), ensure_ascii=False, sort_keys=True) for row in db.execute('SELECT * FROM ' + safe))
            tables[table] = {'rows': len(rows), 'logical_sha256': hashlib.sha256('\n'.join(rows).encode()).hexdigest()}
        return tables


def inventory(root):
    files = sorted(p for p in root.rglob('*') if p.is_file())
    pdfs = {str(p.relative_to(root)).replace('\\', '/'): {'bytes': p.stat().st_size, 'sha256': digest(p)} for p in files if p.suffix.lower() == '.pdf'}
    unique = {record['sha256']: record['bytes'] for record in pdfs.values()}
    dbs = {}
    for path in files:
        with path.open('rb') as stream:
            is_sqlite = stream.read(16) == b'SQLite format 3\0'
        if is_sqlite:
            dbs[path.relative_to(root).as_posix()] = database_inventory(path)
    sources = {}
    with sqlite3.connect((root / 'operational.sqlite3').as_uri() + '?mode=ro', uri=True) as db:
        runs = [json.loads(row[0]) for row in db.execute('SELECT payload FROM runs')]
    referenced = set()
    for run in runs:
        artifact = run.get('artifact')
        if not artifact:
            continue
        storage = Path(artifact['storage_path'])
        path = storage if storage.is_absolute() else root / 'artifacts' / storage
        assert path.resolve().is_relative_to(root.resolve()), path
        key = path.relative_to(root).as_posix()
        assert key in pdfs and pdfs[key]['sha256'] == artifact['sha256'] and pdfs[key]['bytes'] == artifact['byte_len']
        referenced.add(key)
        source = sources.setdefault(run['source'], {'runs': [], 'pdf_paths': set(), 'hashes': set()})
        source['runs'].append({'run_id': run['run_id'], 'validation_status': run['validation_status'],
                               'artifact_id': artifact['artifact_id'], 'sha256': artifact['sha256'],
                               'bytes': artifact['byte_len'], 'pdf_path': key, 'total_pages': run.get('total_pages')})
        source['pdf_paths'].add(key)
        source['hashes'].add(artifact['sha256'])
    for source in sources.values():
        source['pdf_paths'] = sorted(source['pdf_paths'])
        source['physical_pdf_count'] = len(source['pdf_paths'])
        source['physical_pdf_bytes'] = sum(pdfs[p]['bytes'] for p in source['pdf_paths'])
        source['hashes'] = sorted(source['hashes'])
        source['runs'].sort(key=lambda r: r['run_id'])
    return {'root': str(root), 'total_files_including_sqlite_sidecars': len(files),
        'total_bytes_including_sqlite_sidecars': sum(p.stat().st_size for p in files),
        'physical_pdf_count': len(pdfs), 'physical_pdf_bytes': sum(r['bytes'] for r in pdfs.values()),
        'distinct_pdf_sha256_count': len(unique), 'deduplicated_pdf_bytes': sum(unique.values()),
        'pdf_files': pdfs, 'pdf_categories': pdf_categories(pdfs),
        'unreferenced_pdf_paths': sorted(set(pdfs) - referenced),
        'source_ids': sorted(sources), 'sources': sources, 'databases': dbs}


def main():
    destination = DOCS / 'tenderproof-batch99-operations-storage-backup.json'
    append_fapese = '--append-fapese' in sys.argv
    if destination.exists() and not append_fapese:
        raise ValueError('preserve prior report')
    output = {'validated_at': datetime.now(timezone.utc).isoformat(),
        'writers_stopped_basis': 'Root explicitly confirmed replay13/sections writers finished; canonical and crash validation only read these originals.',
        'scope': 'Offline operational volume measurement and new-directory backup/restore. Original PDFs and evidence never deleted.',
        'canonical_database_included': False, 'public_network_requests': 0, 'browser_sessions': 0, 'volumes': []}
    specs = [('13', 'r99replay13', 'tenderproof-batch99-continuous-replay13.json'),
             ('sections', 'r99replaysections', 'tenderproof-batch99-continuous-replay-sections.json')]
    if append_fapese:
        output = json.loads(destination.read_text(encoding='utf-8'))
        output['fapese_append_validated_at'] = datetime.now(timezone.utc).isoformat()
        output['fapese_writers_stopped_basis'] = 'Root explicitly confirmed final r99replayfapese quiet before backup.'
        specs = [('fapese', 'r99replayfapese', 'tenderproof-batch99-continuous-replay-fapese.json')]
    for suffix, folder, report in specs:
        original = ROOT / '.tenderproof' / folder
        before = inventory(original)
        bundle = ROOT / '.tenderproof' / ('r99opsbackup' + suffix)
        restored = ROOT / '.tenderproof' / ('r99opsrestore' + suffix)
        manifest = backup(original, bundle, writers_stopped=True)
        assert verify(bundle) == manifest
        restored_result = restore(bundle, restored)
        after, recovered = inventory(original), inventory(restored)
        assert before['pdf_files'] == after['pdf_files'] == recovered['pdf_files']
        assert before['databases'] == after['databases'] == recovered['databases']
        assert before['sources'] == recovered['sources']
        origin_report = json.loads((DOCS / report).read_text(encoding='utf-8'))
        expected_sources = sorted(s['source'] for s in origin_report['sources'])
        assert before['source_ids'] == expected_sources
        output['volumes'].append({'inventory': before, 'replay_report': report,
            'bundle': str(bundle), 'restored': str(restored), 'backup_files': len(manifest['files']),
            'restored_files': restored_result['restored_files'], 'backup_manifest_sha256': digest(bundle / 'backup-manifest.json'),
            'original_pdf_hashes_unchanged': True, 'restored_pdf_hashes_identical': True,
            'original_and_restored_sqlite_tables_identical': True, 'sqlite_integrity_check': 'ok',
            'files_deleted': 0, 'backup_and_restore_preserved': True})
    all_pdfs = [r for v in output['volumes'] for r in v['inventory']['pdf_files'].values()]
    unique = {r['sha256']: r['bytes'] for r in all_pdfs}
    output['combined'] = {'distinct_source_ids': sorted({s for v in output['volumes'] for s in v['inventory']['source_ids']}),
        'physical_pdf_count': len(all_pdfs), 'physical_pdf_bytes': sum(r['bytes'] for r in all_pdfs),
        'distinct_pdf_sha256_count': len(unique), 'deduplicated_pdf_bytes': sum(unique.values())}
    output['combined']['pdf_categories'] = {k: {f: sum(v['inventory']['pdf_categories'][k][f] for v in output['volumes'])
        for f in ('files', 'bytes')} for k in ('artifacts', 'processing')}
    output['passed'] = True
    output['limits'] = ['Physical PDFs include separately preserved cycle artifacts AND processing input copies, not unique notices. Unreferenced PDF paths refer to run.artifact pointers only, not a deletion recommendation.',
        'File totals include transient SQLite WAL/SHM; logical tables and PDF digests are compared separately.',
        'WAL is folded into backed-up databases using SQLite backup; database file hashes need not equal original files.',
        'No production restore, PostgreSQL canonical backup, live service restart, or distributed/cloud-sync storage guarantee.',
        'These isolated evidence directories remain under the workspace; operational deployment should use local storage outside OneDrive/NFS.']
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed': True, 'combined': output['combined'], 'report': str(destination)}))


if __name__ == '__main__':
    main()
