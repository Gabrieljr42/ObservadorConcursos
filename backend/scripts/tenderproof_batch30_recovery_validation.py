"""Offline real-process crash after completed run commit, before observation commit.

Original evidence is read-only. A separate volume per source starts with no jobs,
runs or observations. Lease expiry is a controlled clock fixture, not wall time.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tenderproof.contracts import TenderProofRun
from app.tenderproof.continuous import ContinuousEngine
from app.tenderproof.continuous_store import ContinuousStore, SourcePolicy
from app.tenderproof.source_adapters import get_source_adapter
from app.tenderproof.store import TenderProofStore
from tenderproof_pilot_continuous_replay import PreservedDriver


def readonly(path):
    db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    return db


def fixture(original, source):
    with readonly(original / 'continuous.sqlite3') as db:
        observation = db.execute('SELECT * FROM observations WHERE source=? ORDER BY first_seen LIMIT 1', (source,)).fetchone()
        detail = db.execute('SELECT s.* FROM snapshots s JOIN jobs j USING(job_id) WHERE j.run_id=?', (observation['run_id'],)).fetchone()
        listing = db.execute("SELECT s.* FROM snapshots s JOIN jobs j USING(job_id) JOIN cycles c USING(cycle_id) WHERE c.source=? AND j.kind='listing' ORDER BY captured_at LIMIT 1", (source,)).fetchone()
    with readonly(original / 'operational.sqlite3') as db:
        run = TenderProofRun.model_validate_json(db.execute('SELECT payload FROM runs WHERE run_id=?', (observation['run_id'],)).fetchone()[0])
    assert run.validation_status.value == 'valid'
    for capture in (listing, detail):
        assert hashlib.sha256(capture['html'].encode()).hexdigest() == capture['sha256']
    candidate = next(c for c in run.candidates if c.candidate_id == run.selected_candidate_id)
    pdf = (original / 'artifacts' / run.artifact.storage_path).read_bytes()
    assert hashlib.sha256(pdf).hexdigest() == run.artifact.sha256
    selected = get_source_adapter(source).choose_document(get_source_adapter(source).documents(detail['html'], candidate))
    assert selected.url_requested == run.document.url_requested
    return {'run': run, 'candidate': candidate, 'pdf': pdf, 'listing_url': listing['url'],
        'listing_html': listing['html'], 'detail_html': detail['html'], 'replay_document_url': selected.url_requested}


def environment(root):
    os.environ.update(TENDERPROOF_ARTIFACT_DIR=str(root / 'artifacts'), TENDERPROOF_PROCESSING_DIR=str(root / 'processing'),
        TENDERPROOF_CONTINUOUS_ENABLED='true', TENDERPROOF_CONTINUOUS_OPERATOR_USER_IDS='901',
        TENDERPROOF_BROWSER_LIVE_ENABLED='false', TENDERPROOF_PUBLICATION_ENABLED='false', TENDERPROOF_PROCESSING_MODE='local')
    def denied(*args, **kwargs):
        raise AssertionError('network forbidden by offline proof')
    socket.create_connection = denied
    socket.socket.connect = denied


def child(args):
    environment(args.root)
    queue = ContinuousStore(args.root / 'continuous.sqlite3')
    if args.phase == 'crash':
        data = fixture(args.original, args.source)
        adapter = get_source_adapter(args.source)
        adapter.listing_urls = (data['listing_url'],)
        queue.configure(901, args.source, SourcePolicy(enabled=True, mode='real', max_candidates=1,
            max_listing_pages=1, max_attempts=1, min_request_gap_s=0, max_documents=100, max_pdf_pages=80, max_browser_seconds=0))
        queue.track(901, args.source, data['candidate'])
        engine = ContinuousEngine(queue=queue, driver_factory=lambda *a, **kw: PreservedDriver(data))
        cycle = engine.enqueue(901, args.source, force=True)
        def die(lease, run_id, *unused):
            run = TenderProofStore().get_run(run_id)
            assert run.execution_status.value == 'completed' and run.validation_status.value == 'valid'
            assert queue.observations(901) == []
            marker = {'pid': os.getpid(), 'run_id': run_id, 'job_id': lease.job_id, 'cycle': cycle,
                'fence': lease.fence, 'attempt': lease.attempts, 'artifact_sha256': run.artifact.sha256,
                'point': 'completed run persisted; queue.complete_detail not called; observations=0'}
            with (args.root / 'crash-marker.json').open('w', encoding='utf-8') as handle:
                json.dump(marker, handle, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os._exit(73)
        queue.complete_detail = die
        for _ in range(3):
            ready = engine.ready_jobs()
            if ready:
                engine.process_job(ready[0])
        raise AssertionError('child did not reach crash hook')
    marker = json.loads((args.root / 'crash-marker.json').read_text())
    def forbidden(*a, **kw):
        raise AssertionError('recovery opened a driver/download')
    engine = ContinuousEngine(queue=queue, driver_factory=forbidden)
    result = engine.process_job(marker['job_id'])
    assert result.get('recovered') is True and result['status'] == 'succeeded', result
    observations = queue.observations(901)
    assert len(observations) == 1 and observations[0]['run_id'] == marker['run_id']
    run = TenderProofStore().get_run(marker['run_id'])
    assert hashlib.sha256(TenderProofStore().load_artifact_bytes(run.artifact)).hexdigest() == marker['artifact_sha256']
    again = engine.process_job(marker['job_id'])
    assert again['status'] == 'not_claimed' and len(queue.observations(901)) == 1
    (args.root / 'recovered.json').write_text(json.dumps({'pid': os.getpid(), 'result': result,
        'observations': 1, 'repeat_result': again, 'artifact_sha256': run.artifact.sha256,
        'driver_calls': 0, 'downloads': 0}, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', type=Path, default=Path('.tenderproof/batch30-continuous-replay-verified-20260908'))
    # Short root keeps local processing job paths under Windows path limits.
    parser.add_argument('--root', type=Path, default=Path('.tenderproof/r30kill'))
    parser.add_argument('--output', type=Path, default=Path('../docs/tenderproof-batch30-recovery-validation.json'))
    parser.add_argument('--sources', nargs='+')
    parser.add_argument('--source')
    parser.add_argument('--phase', choices=('crash', 'recover'))
    args = parser.parse_args()
    args.root, args.original = args.root.resolve(), args.original.resolve()
    if args.phase:
        child(args)
        return
    args.root.mkdir(parents=True, exist_ok=False)
    with readonly(args.original / 'continuous.sqlite3') as db:
        sources = args.sources or [r[0] for r in db.execute('SELECT DISTINCT source FROM observations ORDER BY source')]
    report = {'validated_at': datetime.now(timezone.utc).isoformat(), 'scope': 'offline process crash/recovery; original captures and PDFs; no source availability claim',
        'original_read_only': str(args.original), 'root': str(args.root), 'network_requests': 0, 'browser_sessions': 0,
        'canonical_writes': 0, 'controlled_fixture': 'Only new isolated crashed job lease_until set to0; real os._exit73 after run commit; max_attempts1 final-attempt recovery.', 'sources': []}
    for source in sources:
        root = args.root / source
        root.mkdir()
        base = [sys.executable, str(Path(__file__).resolve()), '--original', str(args.original), '--root', str(root), '--source', source]
        crash = subprocess.run(base + ['--phase', 'crash'], capture_output=True, text=True, timeout=90)
        assert crash.returncode == 73, (source, crash.returncode, crash.stdout, crash.stderr)
        marker = json.loads((root / 'crash-marker.json').read_text())
        with sqlite3.connect(root / 'continuous.sqlite3') as db:
            before = db.execute('SELECT status,attempts,fence FROM jobs WHERE job_id=?', (marker['job_id'],)).fetchone()
            assert before == ('running', 1, marker['fence'])
            assert db.execute('SELECT count(*) FROM observations').fetchone()[0] == 0
            db.execute('UPDATE jobs SET lease_until=0 WHERE job_id=?', (marker['job_id'],))
        recover = subprocess.run(base + ['--phase', 'recover'], capture_output=True, text=True, timeout=90)
        assert recover.returncode == 0, (source, recover.stdout, recover.stderr)
        recovered = json.loads((root / 'recovered.json').read_text())
        with sqlite3.connect(root / 'continuous.sqlite3') as db:
            after = db.execute('SELECT status,attempts,fence FROM jobs WHERE job_id=?', (marker['job_id'],)).fetchone()
        assert after == ('succeeded', 1, marker['fence'] + 1), after
        row = {'source': source, 'passed': True, 'commands': [base + ['--phase', p] for p in ('crash', 'recover')],
            'crash_exitcode': crash.returncode, 'recover_exitcode': recover.returncode, 'crash': marker,
            'before': before, 'after': after, 'recovered': recovered}
        report['sources'].append(row)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        print(source, 'real child death; final attempt recovered; one observation; zero downloads', flush=True)
    report['passed'] = len(report['sources']) == len(sources)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
