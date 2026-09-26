"""Two real processes consume a mixed20-source offline queue for two rounds."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tenderproof.contracts import DiscoveredCandidate
from app.tenderproof.continuous import ContinuousEngine
from app.tenderproof.continuous_store import ContinuousStore, SourcePolicy
from app.tenderproof.source_adapters import get_source_adapter
from app.tenderproof.store import TenderProofStore
from tenderproof_batch30_recovery_validation import fixture, readonly, environment
from tenderproof_batch30_blocked_replay import SAMPLES
from tenderproof_pilot_continuous_replay import PreservedDriver, capture


def fixtures(original):
    with readonly(original / 'continuous.sqlite3') as db:
        valid = [r[0] for r in db.execute('SELECT DISTINCT source FROM observations ORDER BY source')]
    result = {source: fixture(original, source) for source in valid}
    for source, (name, folder) in SAMPLES.items():
        report = json.loads((Path('../docs') / name).read_text(encoding='utf-8'))
        cycle = next(c for c in report['cycles'] if c['source'] == source)
        attempt = cycle['attempts'][0]
        roots = [Path('tests/fixtures') / folder]
        result[source] = dict(candidate=DiscoveredCandidate.model_validate(attempt['candidate']),
            listing_url=cycle['captures'][0]['url'], listing_html=capture(cycle['captures'][0], roots),
            detail_html=capture(attempt['captures'][0], roots))
    assert len(result) == 20 and len(valid) == 16
    for source, data in result.items():
        adapter = get_source_adapter(source)
        adapter.validate_listing_url(data['listing_url'])
        adapter.listing_urls = (data['listing_url'],)
    return result, valid


def pending(queue):
    with queue._db() as db:
        return db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','retry','running','recover')").fetchone()[0]


def worker(args):
    environment(args.root)
    samples, valid = fixtures(args.original)
    queue = ContinuousStore(args.root / 'continuous.sqlite3')
    events, drivers, downloads = [], [], Counter()
    class Driver(PreservedDriver):
        def download(self, url, *, max_bytes):
            source = self.fixture['candidate'].source
            downloads[source] += 1
            if source in SAMPLES:
                raise AssertionError('blocked source attempted download')
            return super().download(url, max_bytes=max_bytes)
    def factory(source, *a, **kw):
        driver = Driver(samples[source])
        drivers.append(driver)
        return driver
    engine = ContinuousEngine(queue=queue, driver_factory=factory)
    started = time.monotonic()
    while pending(queue):
        if time.monotonic() - started > 290:
            raise TimeoutError('mixed queue worker exceeded290seconds')
        jobs = engine.ready_jobs()
        if not jobs:
            time.sleep(.1)
            continue
        job = jobs[0]
        begin = time.monotonic()
        result = engine.process_job(job)
        events.append({'job_id': job, 'result': result, 'duration_s': round(time.monotonic() - begin, 4)})
        if result['status'] in ('not_claimed', 'acquisition_busy'):
            time.sleep(.05)
    assert all(d.closed for d in drivers)
    payload = {'pid': os.getpid(), 'events': events, 'statuses': dict(Counter(e['result']['status'] for e in events)),
        'duration_s': round(time.monotonic() - started, 3), 'downloads': dict(downloads), 'drivers_closed': len(drivers)}
    (args.root / f'worker-{args.round}-{args.worker}.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.tenderproof/r30mix'))
    parser.add_argument('--original', type=Path, default=Path('.tenderproof/batch30-continuous-replay-verified-20260908'))
    parser.add_argument('--output', type=Path, default=Path('../docs/tenderproof-batch30-mixed-validation.json'))
    parser.add_argument('--worker', type=int)
    parser.add_argument('--round', type=int)
    parser.add_argument('--retry-base-s', type=int, default=30)
    parser.add_argument('--inspect-failed-only', action='store_true', help='read preserved failed queue and logs without executing workers')
    args = parser.parse_args()
    args.root, args.original = args.root.resolve(), args.original.resolve()
    if args.inspect_failed_only:
        queue = ContinuousStore(args.root / 'continuous.sqlite3')
        with queue._db() as db:
            states = dict(db.execute('SELECT status,count(*) FROM jobs GROUP BY status').fetchall())
            rows = [dict(r) for r in db.execute('SELECT source,status,cycle_id FROM cycles ORDER BY source')]
            busy = db.execute("SELECT count(*) FROM jobs WHERE error='acquisition_busy'").fetchone()[0]
        for row in rows:
            observations = queue.observations(901, source=row['source'])
            row['observations'] = len(observations)
            row['valid_observations'] = sum(o['summary'].get('validation_status') == 'valid' for o in observations)
        logs = [(args.root / f'worker-1-{i}.log').read_text(encoding='utf-8') for i in (0, 1)]
        assert all('TimeoutError: mixed queue worker exceeded290seconds' in log for log in logs)
        payload = dict(validated_at=datetime.now(timezone.utc).isoformat(), root=str(args.root), passed=False,
            scope='offline mixed20-source queue; two processes; first round exceeded worker290s budget; second round not executed',
            command=[sys.executable, 'scripts/tenderproof_batch30_mixed_validation.py'],
            worker_timeout_s=290, round_timeout_s=300, initial_backlog=40, remaining_backlog=pending(queue),
            job_states=states, acquisition_busy_deferred_jobs=busy, sources=rows, metrics=queue.metrics(901),
            network_requests=0, browser_sessions=0, canonical_writes=0,
            workers_terminal=True,
            termination_evidence='Parent process finally block polled both workers, kills/waits any live worker, then asserted worker failure; both retained logs end with worker290s TimeoutError. Parent command observed terminal exit1.',
            worker_exitcodes=None, exitcode_limitation='Original harness did not persist individual worker exitcodes or PIDs on failure; future script version does.',
            worker_logs=[str(args.root / f'worker-1-{i}.log') for i in (0, 1)],
            explanation='Global acquisition lease contention deferred jobs with acquisition_busy and retry_base_s30. Workers polled other ready jobs after0.05s. Remaining retry jobs show contention, not source unavailability.',
            limitations=['Not a Celery/Redis worker proof; custom consumers using unmodified ContinuousEngine.',
                'No two-round deduplication claim: second round did not execute.',
                'Workers imported core before concurrent document-change code update; this is evidence for that loaded revision only.',
                'Root contains interrupted bounded experiment; no original evidence modified.'])
        args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
        print('failed proof preserved:', states, 'backlog', pending(queue))
        return
    if args.worker is not None:
        worker(args)
        return
    args.root.mkdir(parents=True, exist_ok=False)
    environment(args.root)
    samples, valid = fixtures(args.original)
    queue = ContinuousStore(args.root / 'continuous.sqlite3')
    engine = ContinuousEngine(queue=queue)
    for source, data in samples.items():
        queue.configure(901, source, SourcePolicy(enabled=True, mode='real', max_candidates=1,
            max_listing_pages=1, max_attempts=1, min_request_gap_s=0, max_documents=100, max_pdf_pages=80,
            max_browser_seconds=0, retry_base_s=args.retry_base_s))
        queue.track(901, source, data['candidate'])
    report = {'validated_at': datetime.now(timezone.utc).isoformat(), 'root': str(args.root),
        'scope': 'offline first-page sample with two simultaneous processes and shared SQLite; not full source coverage or production load capacity',
        'network_requests': 0, 'browser_sessions': 0, 'canonical_writes': 0,
        'retry_base_s': args.retry_base_s, 'consumer_busy_sleep_s': .05,
        'timing_limitation': 'Shared host may run other validation processes; timings do not isolate retry policy or prove a causal speedup.',
        'clock_fixture': 'Only selected known candidate next_check=0,last_checked=-1 between rounds; no forced retry timestamps', 'rounds': []}
    for iteration in (1, 2):
        cycles = {}
        for source, data in samples.items():
            with queue._db(write=True) as db:
                db.execute('UPDATE known_candidates SET next_check=0,last_checked=-1 WHERE owner=901 AND source=? AND candidate_key=?',
                    (source, data['candidate'].external_id))
            cycles[source] = engine.enqueue(901, source, force=True)
        backlog = pending(queue)
        assert backlog == 40
        started = time.monotonic()
        core_hashes = {name: hashlib.sha256((Path(__file__).resolve().parents[1] / 'app/tenderproof' / name).read_bytes()).hexdigest()
            for name in ('continuous.py', 'continuous_store.py', 'service.py', 'store.py')}
        processes = []
        for index in (0, 1):
            command = [sys.executable, str(Path(__file__).resolve()), '--root', str(args.root), '--original', str(args.original),
                '--round', str(iteration), '--worker', str(index)]
            log = (args.root / f'worker-{iteration}-{index}.log').open('w', encoding='utf-8')
            processes.append((subprocess.Popen(command, stdout=log, stderr=log,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)), log, command))
        failure = None
        try:
            while any(p.poll() is None for p, _, _ in processes):
                if time.monotonic() - started > 300:
                    raise TimeoutError('round exceeded300seconds')
                time.sleep(.2)
        except Exception as exc:
            failure = type(exc).__name__
        finally:
            for p, log, _ in processes:
                if p.poll() is None:
                    p.kill()
                    p.wait(timeout=10)
                log.close()
        if failure or any(p.returncode != 0 for p, _, _ in processes):
            report.update(passed=False, failure=failure or 'worker_failed', failed_round=iteration,
                core_sha256_before_failed_round=core_hashes,
                elapsed_s=round(time.monotonic()-started,3), remaining_backlog=pending(queue),
                failed_workers=[{'pid': p.pid, 'exitcode': p.returncode, 'confirmed_terminal': p.poll() is not None,
                                 'command': cmd} for p, _, cmd in processes], metrics=queue.metrics(901))
            args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
            raise AssertionError('mixed proof failed; terminal processes and metrics preserved')
        assert all(p.returncode == 0 for p, _, _ in processes), 'worker failed; inspect preserved logs'
        workers = [json.loads((args.root / f'worker-{iteration}-{i}.json').read_text()) for i in (0, 1)]
        assert workers[0]['pid'] != workers[1]['pid']
        rows = []
        for source, cycle in cycles.items():
            state = queue.cycle(cycle, 901)
            observations = queue.observations(901, source=source)
            valid_obs = [o for o in observations if o['summary'].get('validation_status') == 'valid']
            if source in valid:
                assert len(observations) == len(valid_obs) == 1, (source, state, observations)
                run = TenderProofStore().get_run(valid_obs[0]['run_id'])
                assert hashlib.sha256(TenderProofStore().load_artifact_bytes(run.artifact)).hexdigest() == samples[source]['run'].artifact.sha256
            else:
                assert not valid_obs and len(observations) <= 1
                assert state['status'] != 'completed'
                assert not any(w['downloads'].get(source) for w in workers)
            assert state['status'] != 'active'
            rows.append({'source': source, 'status': state['status'], 'reasons': state['reasons'],
                'observations': len(observations), 'valid_observations': len(valid_obs)})
        assert pending(queue) == 0
        report['rounds'].append({'iteration': iteration, 'duration_s': round(time.monotonic()-started, 3),
            'core_sha256_before_workers': core_hashes,
            'initial_backlog': backlog, 'final_backlog': 0, 'workers': workers, 'exitcodes': [p.returncode for p, _, _ in processes],
            'commands': [cmd for _, _, cmd in processes], 'sources': rows, 'metrics': queue.metrics(901)})
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        print('round', iteration, '16valid/4blocked; backlog40to0; two workers exited', flush=True)
    report['passed'] = True
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
