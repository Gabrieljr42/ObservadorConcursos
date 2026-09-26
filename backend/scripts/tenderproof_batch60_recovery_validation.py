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


REPORT_NAMES = (
    'tenderproof-batch60-catalogue-live.json', 'tenderproof-batch60-cpcon-valid-live.json',
    'tenderproof-batch60-elo-live.json', 'tenderproof-batch60-major-live.json',
    'tenderproof-batch60-major-page-recovery.json', 'tenderproof-batch60-own-live.json',
    'tenderproof-batch60-recovered-live.json', 'tenderproof-batch60-shared-live.json',
    'tenderproof-batch60-shared-page-recovery.json',
)
PAGE_LIMITS = {'fundep_open':160, 'facet_open':120, 'cesgranrio_open':100}


def discover(reports):
    result={}
    for name in REPORT_NAMES:
        path=reports/name
        report=json.loads(path.read_text(encoding='utf-8-sig'))
        for cycle in report['cycles']:
            for attempt in cycle['attempts']:
                if attempt.get('validation_status')=='valid' and cycle['source'] not in result:
                    result[cycle['source']]={'report':path,'original':Path(report['root']), 'cycle':cycle,'attempt':attempt}
    if len(result)!=19:raise AssertionError(f'expected19 distinct preserved valid sources, got{sorted(result)}')
    return result


def fixture(original, source):
    from tenderproof_pilot_continuous_replay import capture
    from urllib.parse import urlsplit
    entry=discover(original)[source]; root=entry['original']; attempt=entry['attempt'];cycle=entry['cycle']
    with readonly(root/'operational.sqlite3') as db:
        row=db.execute('SELECT payload FROM runs WHERE run_id=?',(attempt['run_id'],)).fetchone()
        run=TenderProofRun.model_validate_json(row[0])
    assert run.validation_status.value=='valid'
    candidate=next(c for c in run.candidates if c.candidate_id==run.selected_candidate_id)
    pdf=(root/'artifacts'/run.artifact.storage_path).read_bytes()
    assert hashlib.sha256(pdf).hexdigest()==run.artifact.sha256
    roots=list((Path(__file__).resolve().parents[1]/'tests/fixtures').glob('tenderproof_batch60*'))
    listing=cycle['captures'][0]
    # Page recoveries retain captures on each attempt, or use the original live report.
    detail=attempt.get('captures')
    if not detail:
        origin=json.loads(Path(entry['report'].parent / Path(json.loads(entry['report'].read_text(encoding='utf-8-sig'))['origin_report']).name).read_text(encoding='utf-8-sig'))
        detail=next(a['captures'] for c in origin['cycles'] for a in c['attempts'] if a['run_id']==attempt['original_run_id'])
    listing_html=capture(listing,roots); detail_html=capture(detail[0],roots)
    adapter=get_source_adapter(source)
    selected=adapter.choose_document(adapter.documents(detail_html,candidate))
    adapter.validate_document_url(run.document.url_requested,candidate)
    before,after=urlsplit(run.document.url_requested),urlsplit(selected.url_requested)
    assert (before.scheme,before.netloc,before.path)==(after.scheme,after.netloc,after.path)
    return {'run':run,'candidate':candidate,'pdf':pdf,'listing_url':listing['url'],
        'listing_html':listing_html,'detail_html':detail_html,'replay_document_url':selected.url_requested,
        'origin_report':str(entry['report']),'original_root':str(root),'original_run_id':run.run_id,
        'measured_pages':run.validation.total_pages if hasattr(run.validation,'total_pages') else attempt.get('measured_pages',attempt.get('total_pages')),
        'max_pdf_pages':PAGE_LIMITS.get(source,60)}


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
            max_listing_pages=1, max_attempts=1, min_request_gap_s=0, max_documents=100, max_pdf_pages=data['max_pdf_pages'], max_browser_seconds=0))
        queue.track(901, args.source, data['candidate'])
        drivers=[]
        def factory(*a, **kw):
            driver=PreservedDriver(data);drivers.append(driver);return driver
        engine = ContinuousEngine(queue=queue, driver_factory=factory)
        cycle = engine.enqueue(901, args.source, force=True)
        def die(lease, run_id, *unused):
            run = TenderProofStore().get_run(run_id)
            assert run.execution_status.value == 'completed' and run.validation_status.value == 'valid'
            assert queue.observations(901) == []
            marker = {'pid': os.getpid(), 'run_id': run_id, 'job_id': lease.job_id, 'cycle': cycle,
                'fence': lease.fence, 'attempt': lease.attempts, 'artifact_sha256': run.artifact.sha256,
                'original_run_id':data['original_run_id'],'origin_report':data['origin_report'],'measured_pages':data['measured_pages'],'max_pdf_pages':data['max_pdf_pages'],'drivers_closed':all(d.closed for d in drivers),
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
        'driver_calls': 0, 'downloads': 0, 'validation_status':run.validation_status.value}, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', type=Path, default=Path('../docs'))
    # Short root keeps local processing job paths under Windows path limits.
    parser.add_argument('--root', type=Path, default=Path('.tenderproof/r60kill'))
    parser.add_argument('--output', type=Path, default=Path('../docs/tenderproof-batch60-recovery-validation.json'))
    parser.add_argument('--sources', nargs='+')
    parser.add_argument('--source')
    parser.add_argument('--phase', choices=('crash', 'recover'))
    args = parser.parse_args()
    args.root, args.original = args.root.resolve(), args.original.resolve()
    if args.phase:
        child(args)
        return
    args.root.mkdir(parents=True, exist_ok=False)
    sources = args.sources or sorted(discover(args.original))
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
        assert marker['drivers_closed'] and marker['pid']!=recovered['pid']
        assert recovered['validation_status']=='valid'
        row = {'source': source, 'passed': True, 'commands': [base + ['--phase', p] for p in ('crash', 'recover')],
            'crash_exitcode': crash.returncode, 'recover_exitcode': recover.returncode, 'child_processes_exited':True, 'crash': marker,
            'before': before, 'after': after, 'recovered': recovered}
        report['sources'].append(row)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        print(source, 'real child death; final attempt recovered; one observation; zero downloads', flush=True)
    report['passed'] = len(report['sources']) == len(sources)
    report['expected_source_count'] = 19
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    report['limitations'] = ['Fresh isolated queues only; historical raw signed-URL signature migration is covered by independent focused tests.', 'Preserved selected valid original PDFs; no whole-source completeness or new availability claim.']
    report['resources'] = {'child_processes_exited': len(report['sources'])*2, 'preserved_drivers_closed': all(r['crash']['drivers_closed'] for r in report['sources']), 'recovery_driver_calls': sum(r['recovered']['driver_calls'] for r in report['sources']), 'recovery_downloads': sum(r['recovered']['downloads'] for r in report['sources'])}
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
