"""Backup/restore of controlled durable evidence, without production data."""
import json
import pytest
from app.tenderproof.continuous_store import ContinuousStore, SourcePolicy
from app.tenderproof.operational_backup import backup, restore, verify


def test_backup_restore_preserves_queue_and_artifacts(tmp_path):
    root = tmp_path / 'source'
    queue = ContinuousStore(root / 'continuous.sqlite3')
    queue.configure(1, 'ibgp_open', SourcePolicy(), now=100)
    (root / 'artifacts').mkdir()
    (root / 'artifacts' / 'controlled.pdf').write_bytes(b'%PDF-controlled synthetic evidence')
    bundle, restored = tmp_path / 'backup', tmp_path / 'restored'
    report = backup(root, bundle, writers_stopped=True)
    assert len(report['files']) == 2
    assert verify(bundle) == report
    assert restore(bundle, restored)['restored_files'] == 2
    assert ContinuousStore(restored / 'continuous.sqlite3').configuration(1, 'ibgp_open') == queue.configuration(1, 'ibgp_open')
    assert (restored / 'artifacts' / 'controlled.pdf').read_bytes() == (root / 'artifacts' / 'controlled.pdf').read_bytes()
    with pytest.raises(FileExistsError):
        restore(bundle, restored)


def test_backup_corruption_blocks_restore_before_any_writes(tmp_path):
    root = tmp_path / 'source'
    root.mkdir()
    (root / 'evidence').write_bytes(b'original')
    bundle = tmp_path / 'backup'
    backup(root, bundle, writers_stopped=True)
    (bundle / 'evidence').write_bytes(b'tampered')
    with pytest.raises(ValueError, match='integridade'):
        restore(bundle, tmp_path / 'restored')
    assert not (tmp_path / 'restored').exists()


def test_backup_requires_stopped_writers_and_rejects_nested_target(tmp_path):
    root = tmp_path / 'source'
    root.mkdir()
    with pytest.raises(ValueError, match='parar API'):
        backup(root, tmp_path / 'backup')
    with pytest.raises(ValueError, match='separados'):
        backup(root, root / 'backup', writers_stopped=True)


def test_restore_rejects_manifest_path_escape(tmp_path):
    bundle = tmp_path / 'bundle'
    bundle.mkdir()
    (bundle / 'backup-manifest.json').write_text(json.dumps({'schema_version':1,'files':[{'path':'../outside'}]}))
    with pytest.raises(ValueError, match='fora do volume'):
        restore(bundle, tmp_path / 'restored')
