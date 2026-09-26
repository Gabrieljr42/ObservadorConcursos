"""Two simultaneous local consumers, 19 valid fixtures plus two controlled refusals."""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tenderproof.contracts import DiscoveredCandidate
from app.tenderproof.continuous import ContinuousEngine
from app.tenderproof.continuous_store import ContinuousStore, SourcePolicy
from app.tenderproof.source_adapters import get_source_adapter
from app.tenderproof.store import TenderProofStore
from tenderproof_batch30_recovery_validation import fixture, readonly, environment
from tenderproof_pilot_continuous_replay import PreservedDriver, capture

BLOCKED = {'gualimp_open', 'contemax_open'}
PAGE_LIMITS = {'fundep_open': 160, 'facet_open': 120, 'cesgranrio_open': 100}


def fixtures(original):
    report = json.loads(Path('../docs/tenderproof-batch60-continuous-replay.json').read_text(encoding='utf8'))
    assert report.get('passed') is True and Path(report['root']).resolve() == original
    with closing(readonly(original/'continuous.sqlite3')) as connection:
        sources = [r[0] for r in connection.execute('SELECT DISTINCT source FROM observations ORDER BY source')]
    assert len(sources) == 19
    samples = {source: fixture(original, source) for source in sources}
    gualimp = json.loads(Path('../docs/tenderproof-batch60-extended-verified-live.json').read_text(encoding='utf8'))
    cycle = next(c for c in gualimp['cycles'] if c['source'] == 'gualimp_open')
    attempt = cycle['attempts'][0]
    assert '403 Forbidden' in attempt['error']
    samples['gualimp_open'] = {'candidate': DiscoveredCandidate.model_validate(attempt['candidate']),
        'listing_url': cycle['captures'][0]['url'], 'listing_html': capture(cycle['captures'][0], [Path('tests/fixtures/tenderproof_batch60_extended')]),
        'detail_html': '', 'refusal': 'HTTP403 at detail; controlled replay of preserved diagnostic'}
    root = Path('tests/fixtures/tenderproof_batch60_contemax')
    manifests = json.loads((root/'manifest-https.json').read_text(encoding='utf8'))
    pages = {}
    for row in manifests:
        body = (root/row['file']).read_bytes()
        assert hashlib.sha256(body).hexdigest() == row['fixture_sha256']
        pages[row['name']] = (row['url'], body.decode('utf8'))
    adapter = get_source_adapter('contemax_open')
    listing_url, listing_html = pages['listing']
    detail_url, detail_html = pages['cubati']
    candidate = next(c for c in adapter.parse_listing(listing_html, listing_url).candidates if c.detail_url_observed == detail_url)
    adapter.confirm_identity(candidate, detail_html, detail_url)
    chosen = adapter.choose_document(adapter.documents(detail_html, candidate))
    refusal = json.loads(Path('../docs/tenderproof-batch60-contemax-pdf-probe.json').read_text(encoding='utf8'))
    assert refusal['url'] == chosen.url_requested and refusal['error'] == 'ConnectError'
    samples['contemax_open'] = {'candidate': candidate, 'listing_url': listing_url, 'listing_html': listing_html,
        'detail_html': detail_html, 'replay_document_url': chosen.url_requested, 'refusal': 'ConnectError at selected PDF; controlled replay of preserved diagnostic'}
    assert len(samples) == 21
    for source, data in samples.items():
        adapter = get_source_adapter(source)
        adapter.validate_listing_url(data['listing_url'])
        adapter.listing_urls = (data['listing_url'],)
    return samples, sources


def pending(queue):
    with queue._db() as db:
        return db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','retry','running','recover')").fetchone()[0]


def worker(args):
    environment(args.root)
    samples, _ = fixtures(args.original)
    queue = ContinuousStore(args.root/'continuous.sqlite3')
    events, drivers, downloads = [], [], Counter()
    class Driver(PreservedDriver):
        def open_detail(self, url):
            if self.fixture['candidate'].source == 'gualimp_open':
                assert url == self.fixture['candidate'].detail_url_observed
                request = httpx.Request('GET', url)
                response = httpx.Response(403, request=request)
                raise httpx.HTTPStatusError('Controlled offline replay: official Gualimp detail HTTP403 browser challenge', request=request, response=response)
            return super().open_detail(url)

        def download(self, url, *, max_bytes):
            source = self.fixture['candidate'].source
            downloads[source] += 1
            if source == 'contemax_open':
                assert url == self.fixture['replay_document_url']
                raise httpx.ConnectError('Controlled offline replay: official Contemax principal HTTPS connection refused')
            if source == 'gualimp_open':
                raise AssertionError('Gualimp detail refusal must prevent download')
            return super().download(url, max_bytes=max_bytes)

    def factory(source, *unused, **kwargs):
        driver = Driver(samples[source])
        drivers.append(driver)
        return driver

    engine = ContinuousEngine(queue=queue, driver_factory=factory)
    started = time.monotonic()
    peak_backlog = 0
    while pending(queue):
        if time.monotonic()-started > 290:
            raise TimeoutError('mixed queue worker exceeded 290 seconds')
        peak_backlog = max(peak_backlog, pending(queue))
        jobs = engine.ready_jobs()
        if not jobs:
            time.sleep(.1)
            continue
        begin = time.monotonic()
        result = engine.process_job(jobs[0])
        events.append({'job_id': jobs[0], 'result': result, 'duration_s': round(time.monotonic()-begin,4)})
        if result['status'] in ('not_claimed','acquisition_busy'):
            time.sleep(.05)
    assert all(driver.closed for driver in drivers)
    payload = {'pid': os.getpid(), 'duration_s': round(time.monotonic()-started,3), 'peak_pending_backlog': peak_backlog,
        'events': events, 'statuses': dict(Counter(e['result']['status'] for e in events)), 'downloads': dict(downloads),
        'drivers_created': len(drivers), 'drivers_closed': sum(driver.closed for driver in drivers)}
    (args.root/f'worker-{args.round}-{args.worker}.json').write_text(json.dumps(payload,indent=2),encoding='utf8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.tenderproof/r60mix'))
    parser.add_argument('--original', type=Path, default=Path('.tenderproof/r60replay'))
    parser.add_argument('--output', type=Path, default=Path('../docs/tenderproof-batch60-mixed-validation.json'))
    parser.add_argument('--worker', type=int)
    parser.add_argument('--round', type=int)
    args = parser.parse_args()
    args.root, args.original = args.root.resolve(), args.original.resolve()
    if args.worker is not None:
        worker(args)
        return
    samples, valid = fixtures(args.original)
    args.root.mkdir(parents=True,exist_ok=False)
    environment(args.root)
    queue = ContinuousStore(args.root/'continuous.sqlite3')
    engine = ContinuousEngine(queue=queue)
    for source,data in samples.items():
        queue.configure(901,source,SourcePolicy(enabled=True,mode='real',max_candidates=1,max_listing_pages=1,
            max_attempts=1,min_request_gap_s=0,max_documents=100,max_pdf_pages=PAGE_LIMITS.get(source,60),
            max_browser_seconds=0,retry_base_s=1))
        queue.track(901,source,data['candidate'])
    plan = json.loads(Path('../docs/tenderproof-rollout-plan.json').read_text(encoding='utf8'))
    additions = next(b['sources'] for b in plan['batches'] if b['cumulative_sources']==60)
    report = {'validated_at': datetime.now(timezone.utc).isoformat(), 'root': str(args.root), 'original': str(args.original),
        'scope': 'Two real same-host processes consume a shared local SQLite queue using 19 preserved valid source samples and two explicitly controlled failures; no production throughput or distributed-storage claim.',
        'valid_sources': valid, 'controlled_blocked_sources': sorted(BLOCKED), 'sources_without_contract_excluded_from_queue': [s for s in additions if s not in samples],
        'network_requests': 0,'browser_sessions': 0,'canonical_writes': 0,'retry_base_s': 1,'consumer_busy_sleep_s': .05,
        'page_limits': {'default':60,**PAGE_LIMITS}, 'clock_fixture': 'Between rounds, only selected known candidate next_check=0,last_checked=-1; real retry timestamps unchanged.',
        'failure_fixture_evidence': ['docs/tenderproof-batch60-extended-verified-live.json','docs/tenderproof-batch60-contemax-pdf-probe.json'],
        'limitations': ['Controlled replay reproduces reported HTTP/connection failures; it does not assert current external availability.', 'Consumers use unmodified ContinuousEngine, not Celery/Redis.', 'Other validation tasks share the host; measured times do not isolate queue policy.'], 'rounds': []}
    for iteration in (1,2):
        cycles = {}
        for source,data in samples.items():
            with queue._db(write=True) as db:
                db.execute('UPDATE known_candidates SET next_check=0,last_checked=-1 WHERE owner=901 AND source=? AND candidate_key=?',(source,data['candidate'].external_id))
            cycles[source] = engine.enqueue(901,source,force=True)
        backlog = pending(queue)
        assert backlog == 42
        started = time.monotonic()
        core = {name:hashlib.sha256((Path('app/tenderproof')/name).read_bytes()).hexdigest() for name in ('continuous.py','continuous_store.py','service.py','store.py')}
        processes = []
        for index in (0,1):
            command = [sys.executable,str(Path(__file__).resolve()),'--root',str(args.root),'--original',str(args.original),'--round',str(iteration),'--worker',str(index)]
            log = (args.root/f'worker-{iteration}-{index}.log').open('w',encoding='utf8')
            processes.append((subprocess.Popen(command,stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)),log,command))
        failure = None
        try:
            while any(p.poll() is None for p,_,_ in processes):
                if time.monotonic()-started>300:
                    raise TimeoutError('round exceeded 300 seconds')
                time.sleep(.2)
        except Exception as exc:
            failure = type(exc).__name__+': '+str(exc)
        finally:
            for process,log,_ in processes:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=10)
                log.close()
        if failure or any(p.returncode!=0 for p,_,_ in processes):
            report.update(passed=False,failure=failure or 'worker_failed',failed_round=iteration,elapsed_s=round(time.monotonic()-started,3),remaining_backlog=pending(queue),
                failed_workers=[{'pid':p.pid,'exitcode':p.returncode,'confirmed_terminal':p.poll() is not None,'command':command} for p,_,command in processes],metrics=queue.metrics(901))
            args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
            raise AssertionError('mixed proof failed; logs, backlog and terminal worker evidence preserved')
        workers = [json.loads((args.root/f'worker-{iteration}-{index}.json').read_text(encoding='utf8')) for index in (0,1)]
        assert workers[0]['pid'] != workers[1]['pid']
        rows = []
        for source,cycle in cycles.items():
            state = queue.cycle(cycle,901)
            observations = queue.observations(901,source=source)
            valid_obs = [o for o in observations if o['summary'].get('validation_status')=='valid']
            if source in valid:
                assert len(observations)==len(valid_obs)==1,(source,state,observations)
                store=TenderProofStore()
                run=store.get_run(valid_obs[0]['run_id'])
                assert hashlib.sha256(store.load_artifact_bytes(run.artifact)).hexdigest()==samples[source]['run'].artifact.sha256
            else:
                assert not valid_obs and len(observations)<=1
                assert state['status']!='completed'
                if source=='gualimp_open':
                    assert not any(w['downloads'].get(source) for w in workers)
                else:
                    assert sum(w['downloads'].get(source,0) for w in workers)==1
            assert state['status']!='active'
            rows.append({'source':source,'status':state['status'],'reasons':state['reasons'],'observations':len(observations),'valid_observations':len(valid_obs)})
        assert pending(queue)==0
        report['rounds'].append({'iteration':iteration,'duration_s':round(time.monotonic()-started,3),'initial_backlog':backlog,'final_backlog':0,
            'core_sha256_before_workers':core,'workers':workers,'exitcodes':[p.returncode for p,_,_ in processes],
            'worker_pids':[p.pid for p,_,_ in processes],'workers_confirmed_terminal':all(p.poll() is not None for p,_,_ in processes),'sources':rows,'metrics':queue.metrics(901)})
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
        print('round',iteration,'19 valid / 2 controlled blocked; backlog 42 to 0; two workers exited',flush=True)
    report['passed']=True
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')


if __name__=='__main__':
    main()
