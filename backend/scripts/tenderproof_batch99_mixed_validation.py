"""Two simultaneous local consumers, parameterized valid fixtures plus three preserved failure cases."""
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
from app.tenderproof.contracts import DiscoveredCandidate, TenderProofRun
from app.tenderproof.continuous import ContinuousEngine
from app.tenderproof.continuous_store import ContinuousStore, SourcePolicy
from app.tenderproof.source_adapters import get_source_adapter
from app.tenderproof.store import TenderProofStore
from tenderproof_batch30_recovery_validation import fixture, readonly, environment
from tenderproof_pilot_continuous_replay import PreservedDriver, capture

BLOCKED = {'nossorumo_open', 'fepese_open', 'fapesc_selection'}
PAGE_LIMITS = {}


def fixtures(original, original_report, selected_sources=None):
    report = json.loads(original_report.read_text(encoding='utf8'))
    assert report.get('passed') is True and Path(report['root']).resolve() == original
    with closing(readonly(original/'continuous.sqlite3')) as connection:
        available = [r[0] for r in connection.execute('SELECT DISTINCT source FROM observations ORDER BY source')]
    sources=sorted(selected_sources or available)
    assert sources and set(sources)<=set(available) and not set(sources)&BLOCKED
    samples={source:fixture(original,source) for source in sources}
    reports={
        'nossorumo_open':('../docs/tenderproof-batch99-nossorumo-live.json','tests/fixtures/tenderproof_batch99_own','401 Unauthorized'),
        'fepese_open':('../docs/tenderproof-batch99-fepese-live.json','tests/fixtures/tenderproof_batch99_fepese','nenhum edital principal'),
        'fapesc_selection':('../docs/tenderproof-batch99-regions-pdf-replay.json','tests/fixtures/tenderproof_batch99_regions','invalid_document')}
    for source,(path,capture_root,expected_error) in reports.items():
        preserved=json.loads(Path(path).read_text(encoding='utf8'))
        cycle=next(c for c in preserved['cycles'] if c['source']==source)
        attempt=cycle['attempts'][0]
        assert expected_error in attempt['error']
        candidate=DiscoveredCandidate.model_validate(attempt['candidate'])
        data={'candidate':candidate,'listing_url':cycle['captures'][0]['url'],
              'listing_html':capture(cycle['captures'][0],[Path(capture_root)]),
              'detail_html':capture(attempt['captures'][0],[Path(capture_root)]),
              'refusal':'Controlled OFFLINE replay of preserved diagnostic: '+expected_error,'origin_report':path}
        adapter=get_source_adapter(source)
        adapter.confirm_identity(candidate,data['detail_html'],candidate.detail_url_observed)
        docs=adapter.documents(data['detail_html'],candidate)
        if source=='fepese_open':
            try:adapter.choose_document(docs)
            except ValueError:pass
            else:raise AssertionError('preserved FEPESE no longer refuses amendment-only selection')
        else:
            document=adapter.choose_document(docs)
            data['replay_document_url']=document.url_requested
        if source=='fapesc_selection':
            original_root=Path(preserved['root'])
            with closing(readonly(original_root/'operational.sqlite3')) as connection:
                run=TenderProofRun.model_validate_json(connection.execute('SELECT payload FROM runs WHERE run_id=?',(attempt['run_id'],)).fetchone()[0])
            raw=(original_root/'artifacts'/run.artifact.storage_path).read_bytes()
            assert hashlib.sha256(raw).hexdigest()==run.artifact.sha256
            assert raw.startswith(b'\n\n%PDF-') and run.document.url_requested==data['replay_document_url']
            data.update(run=run,pdf=raw)
        samples[source]=data
    for source,data in samples.items():
        adapter=get_source_adapter(source)
        adapter.validate_listing_url(data['listing_url'])
        adapter.listing_urls=(data['listing_url'],)
    return samples,sources


def pid_running(pid):
    if os.name=='nt':
        import ctypes
        from ctypes import wintypes
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.OpenProcess.restype=wintypes.HANDLE
        kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
        kernel.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
        kernel.CloseHandle.argtypes=[wintypes.HANDLE]
        handle=kernel.OpenProcess(0x1000,False,pid)
        if not handle:
            if ctypes.get_last_error()==87:return False
            raise RuntimeError('cannot confirm worker PID termination')
        try:
            code=wintypes.DWORD()
            if not kernel.GetExitCodeProcess(handle,ctypes.byref(code)):raise RuntimeError('cannot read worker exit code')
            return code.value==259
        finally:kernel.CloseHandle(handle)
    try:os.kill(pid,0);return True
    except ProcessLookupError:return False


def pending(queue):
    with queue._db() as db:
        return db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','retry','running','recover')").fetchone()[0]


def worker(args):
    environment(args.root)
    samples, _ = fixtures(args.original,args.original_report,args.sources)
    queue = ContinuousStore(args.root/'continuous.sqlite3')
    events, drivers, downloads = [], [], Counter()
    class Driver(PreservedDriver):
        def download(self, url, *, max_bytes):
            source = self.fixture['candidate'].source
            downloads[source] += 1
            if source == 'nossorumo_open':
                assert url == self.fixture['replay_document_url']
                request=httpx.Request('GET',url)
                response=httpx.Response(401,request=request)
                raise httpx.HTTPStatusError('Controlled OFFLINE replay: observed NossoRumo principal HTTP401',request=request,response=response)
            if source == 'fepese_open':
                raise AssertionError('FEPESE amendment-only refusal must prevent download')
            return super().download(url, max_bytes=max_bytes)

        def download_document(self,document,candidate,*,max_bytes):
            downloads[candidate.source] += 1
            return super().download_document(document,candidate,max_bytes=max_bytes)

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
    parser.add_argument('--root', type=Path, default=Path('.tenderproof/r99mix13'))
    parser.add_argument('--original', type=Path, default=Path('.tenderproof/r99replay13'))
    parser.add_argument('--output', type=Path, default=Path('../docs/tenderproof-batch99-mixed-validation.json'))
    parser.add_argument('--original-report',type=Path,default=Path('../docs/tenderproof-batch99-continuous-replay13.json'))
    parser.add_argument('--sources',nargs='+',help='Valid sources selected from the passed original replay; blocked cases always included')
    parser.add_argument('--worker', type=int)
    parser.add_argument('--round', type=int)
    args = parser.parse_args()
    args.root, args.original = args.root.resolve(), args.original.resolve()
    args.original_report=args.original_report.resolve()
    if args.worker is not None:
        worker(args)
        return
    samples, valid = fixtures(args.original,args.original_report,args.sources)
    args.root.mkdir(parents=True,exist_ok=False)
    environment(args.root)
    queue = ContinuousStore(args.root/'continuous.sqlite3')
    engine = ContinuousEngine(queue=queue)
    for source,data in samples.items():
        queue.configure(901,source,SourcePolicy(enabled=True,mode='real',max_candidates=1,max_listing_pages=1,
            max_attempts=2,min_request_gap_s=0,max_documents=100,max_pdf_pages=PAGE_LIMITS.get(source,60),
            max_browser_seconds=0,retry_base_s=1))
        queue.track(901,source,data['candidate'])
    plan = json.loads(Path('../docs/tenderproof-rollout-plan.json').read_text(encoding='utf8'))
    additions = next(b['sources'] for b in plan['batches'] if b['cumulative_sources']==99)
    report = {'validated_at': datetime.now(timezone.utc).isoformat(), 'root': str(args.root), 'original': str(args.original),
        'scope': 'Two real same-host processes consume shared isolated SQLite using parameterized preserved valid samples and three explicit failure cases; no production throughput or distributed-storage claim.',
        'valid_sources': valid, 'controlled_blocked_sources': sorted(BLOCKED), 'sources_without_contract_excluded_from_queue': [s for s in additions if s not in __import__('app.tenderproof.source_adapters',fromlist=['SOURCE_ADAPTERS']).SOURCE_ADAPTERS], 'registered_sources_not_in_this_proof':[s for s in additions if s not in samples and s in __import__('app.tenderproof.source_adapters',fromlist=['SOURCE_ADAPTERS']).SOURCE_ADAPTERS],
        'network_requests': 0,'browser_sessions': 0,'canonical_writes': 0,'retry_base_s': 1,'max_attempts':2,'original_report':str(args.original_report),'consumer_busy_sleep_s': .05,
        'page_limits': {'default':60,**PAGE_LIMITS}, 'clock_fixture': 'Between rounds, only selected known candidate next_check=0,last_checked=-1; real retry timestamps unchanged.',
        'failure_fixture_evidence': [samples[s]['origin_report'] for s in sorted(BLOCKED)],
        'limitations': ['Controlled replay reproduces reported HTTP/connection failures; it does not assert current external availability.', 'Consumers use unmodified ContinuousEngine, not Celery/Redis.', 'Other validation tasks share the host; measured times do not isolate queue policy.'], 'rounds': []}
    for iteration in (1,2):
        cycles = {}
        for source,data in samples.items():
            with queue._db(write=True) as db:
                db.execute('UPDATE known_candidates SET next_check=0,last_checked=-1 WHERE owner=901 AND source=? AND candidate_key=?',(source,data['candidate'].external_id))
            cycles[source] = engine.enqueue(901,source,force=True)
        backlog = pending(queue)
        assert backlog == len(samples)*2
        started = time.monotonic()
        core = {name:hashlib.sha256((Path('app/tenderproof')/name).read_bytes()).hexdigest() for name in ('continuous.py','continuous_store.py','service.py','store.py')}
        processes = []
        for index in (0,1):
            command = [sys.executable,str(Path(__file__).resolve()),'--root',str(args.root),'--original',str(args.original),'--round',str(iteration),'--worker',str(index),'--original-report',str(args.original_report),'--sources',*valid]
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
                    if os.name=='nt':
                        subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,timeout=10,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                    else:process.kill()
                    process.wait(timeout=10)
                log.close()
        if failure or any(p.returncode!=0 for p,_,_ in processes):
            report.update(passed=False,failure=failure or 'worker_failed',failed_round=iteration,elapsed_s=round(time.monotonic()-started,3),remaining_backlog=pending(queue),
                failed_workers=[{'pid':p.pid,'exitcode':p.returncode,'confirmed_terminal':p.poll() is not None,'command':command} for p,_,command in processes],metrics=queue.metrics(901))
            args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
            raise AssertionError('mixed proof failed; logs, backlog and terminal worker evidence preserved')
        workers = [json.loads((args.root/f'worker-{iteration}-{index}.json').read_text(encoding='utf8')) for index in (0,1)]
        assert workers[0]['pid'] != workers[1]['pid']
        actual_pids=[w['pid'] for w in workers]
        actual_terminal=all(not pid_running(pid) for pid in actual_pids)
        assert actual_terminal,'worker child PID still running'
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
                if source=='fepese_open':
                    assert not any(w['downloads'].get(source) for w in workers)
                else:
                    assert sum(w['downloads'].get(source,0) for w in workers)==2
            assert state['status']!='active'
            rows.append({'source':source,'status':state['status'],'reasons':state['reasons'],'observations':len(observations),'valid_observations':len(valid_obs)})
        assert pending(queue)==0
        report['rounds'].append({'iteration':iteration,'duration_s':round(time.monotonic()-started,3),'initial_backlog':backlog,'final_backlog':0,
            'core_sha256_before_workers':core,'workers':workers,'exitcodes':[p.returncode for p,_,_ in processes],
            'worker_pids':[p.pid for p,_,_ in processes],'actual_worker_pids':actual_pids,'actual_workers_confirmed_terminal':actual_terminal,'workers_confirmed_terminal':all(p.poll() is not None for p,_,_ in processes),'sources':rows,'metrics':queue.metrics(901)})
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
        print('round',iteration,len(valid),'valid / 3 controlled blocked; backlog',backlog,'to0; two workers exited',flush=True)
    report['passed']=True
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')


if __name__=='__main__':
    main()
