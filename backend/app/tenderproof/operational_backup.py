"""Offline evidence-preserving backup for the single-host operational volume.

API, acquisition/processing workers and scheduler must be stopped by the operator.
This is not a distributed snapshot or a backup of the separate canonical database.
Destinations must be new. Nothing is pruned or overwritten.
"""
from __future__ import annotations

import hashlib
from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
from datetime import datetime, timezone


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _file(root, relative):
    path = (root / relative).resolve()
    if path == root or not path.is_relative_to(root):
        raise ValueError('caminho de backup fora do volume')
    return path


def backup(source, destination, *, writers_stopped=False):
    if not writers_stopped:
        raise ValueError('parar API, workers e scheduler antes de copiar evidências')
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_dir() or destination.is_relative_to(source) or source.is_relative_to(destination):
        raise ValueError('origem e destino devem ser diretórios separados')
    if (source / 'backup-manifest.json').exists():
        raise ValueError('origem já contém manifesto reservado de backup')
    files = sorted(source.rglob('*'))
    if any(path.is_symlink() or path.is_junction() for path in files):
        raise ValueError('links ou junctions não são aceitos no volume de backup')
    destination.mkdir(parents=True, exist_ok=False)
    records = []
    for path in files:
        if not path.is_file():
            continue
        relative = path.relative_to(source).as_posix()
        if path.name.endswith(('-wal', '-shm')):
            # Database backup below folds WAL into the destination database.
            base = path.with_name(path.name.rsplit('-', 1)[0])
            if base.is_file():
                with base.open('rb') as stream:
                    if stream.read(16) == b'SQLite format 3\x00':
                        continue
        target = _file(destination, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        with path.open('rb') as stream:
            sqlite = stream.read(16) == b'SQLite format 3\x00'
        if sqlite:
            with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as original:
                with closing(sqlite3.connect(target)) as copied:
                    original.backup(copied)
                    if copied.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
                        raise ValueError('banco operacional íntegro não confirmado')
        else:
            shutil.copyfile(path, target)
        records.append({'path':relative, 'bytes':target.stat().st_size, 'sha256':digest(target), 'sqlite':sqlite})
    manifest = {'schema_version':1, 'created_at':datetime.now(timezone.utc).isoformat(),
                'writers_stopped_attested':True, 'canonical_database_included':False,
                'files':records}
    (destination / 'backup-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest


def verify(bundle):
    root = Path(bundle).resolve()
    manifest = json.loads((root / 'backup-manifest.json').read_text(encoding='utf-8'))
    if manifest.get('schema_version') != 1:
        raise ValueError('versão de backup não suportada')
    seen = set()
    for record in manifest['files']:
        path = _file(root, record['path'])
        if path in seen or path.is_symlink() or not path.is_file():
            raise ValueError('artefato de backup ausente ou caminho duplicado')
        seen.add(path)
        if path.stat().st_size != record['bytes'] or digest(path) != record['sha256']:
            raise ValueError('integridade do backup divergente')
    return manifest


def restore(bundle, destination):
    manifest = verify(bundle)  # Verify every byte before creating any destination.
    root, destination = Path(bundle).resolve(), Path(destination).resolve()
    if destination.is_relative_to(root) or root.is_relative_to(destination):
        raise ValueError('restaurar em volume novo e separado')
    destination.mkdir(parents=True, exist_ok=False)
    for record in manifest['files']:
        target = _file(destination, record['path'])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(_file(root, record['path']), target)
    return {'restored_files':len(manifest['files']), 'canonical_database_restored':False}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('backup', 'verify', 'restore'))
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path, nargs='?')
    parser.add_argument('--writers-stopped', action='store_true')
    args = parser.parse_args()
    if args.action != 'verify' and args.destination is None:
        parser.error('destino novo obrigatório')
    result = (backup(args.source, args.destination, writers_stopped=args.writers_stopped) if args.action == 'backup'
              else restore(args.source, args.destination) if args.action == 'restore' else verify(args.source))
    print(json.dumps({'action':args.action, 'files':len(result['files']) if 'files' in result else result['restored_files'],
                      'canonical_database_included':False}))
