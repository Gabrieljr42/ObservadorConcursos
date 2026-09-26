"""Offline two-cycle proof of conservative failure for four official samples."""
import hashlib
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tenderproof.contracts import DiscoveredCandidate
from app.tenderproof.continuous import ContinuousEngine
from app.tenderproof.continuous_store import ContinuousStore, SourcePolicy
from app.tenderproof.source_adapters import get_source_adapter
from tenderproof_pilot_continuous_replay import PreservedDriver, capture

SAMPLES = {
    'rbo_open': ('tenderproof-batch30-shared-live.json', 'tenderproof_batch30_shared'),
    'idecan_open': ('tenderproof-batch30-edital-live.json', 'tenderproof_batch30_edital'),
    'ibfc_open': ('tenderproof-batch30-own-live.json', 'tenderproof_batch30_own'),
    'admtec_open': ('tenderproof-batch30-own-live.json', 'tenderproof_batch30_own'),
}


def main():
    root = Path('.tenderproof/batch30-blocked-replay-20260908').resolve()
    root.mkdir(parents=True, exist_ok=False)
    fixtures, drivers = {}, []
    for source, (name, folder) in SAMPLES.items():
        data = json.loads((Path('../docs')/name).read_text(encoding='utf-8'))
        cycle = next(c for c in data['cycles'] if c['source'] == source)
        attempt = cycle['attempts'][0]
        candidate = DiscoveredCandidate.model_validate(attempt['candidate'])
        roots = [Path('tests/fixtures')/folder]
        fixtures[source] = dict(candidate=candidate, listing_url=cycle['captures'][0]['url'],
            listing_html=capture(cycle['captures'][0], roots), detail_html=capture(attempt['captures'][0], roots))
        adapter = get_source_adapter(source)
        adapter.validate_listing_url(fixtures[source]['listing_url'])
        adapter.listing_urls = (fixtures[source]['listing_url'],)
    os.environ.update(TENDERPROOF_ARTIFACT_DIR=str(root/'artifacts'),
        TENDERPROOF_CONTINUOUS_ENABLED='true', TENDERPROOF_CONTINUOUS_OPERATOR_USER_IDS='901',
        TENDERPROOF_BROWSER_LIVE_ENABLED='false', TENDERPROOF_PUBLICATION_ENABLED='false')

    class RefusingDriver(PreservedDriver):
        download_calls = 0
        def download(self, url, *, max_bytes):
            self.download_calls += 1
            raise AssertionError('blocked sample must not select a principal for download')

    def factory(source, settings, **kwargs):
        driver = RefusingDriver(fixtures[source]); drivers.append(driver); return driver

    queue = ContinuousStore(root/'continuous.sqlite3')
    engine = ContinuousEngine(queue=queue, driver_factory=factory)
    report = dict(validated_at=datetime.now(timezone.utc).isoformat(), root=str(root),
        scope='offline official blocked samples; controlled due-time advancement between cycles',
        network_requests=0, browser_sessions=0, canonical_writes=0, sources=[])
    for source, fixture in fixtures.items():
        queue.configure(901, source, SourcePolicy(enabled=True, mode='real', max_candidates=1,
            max_listing_pages=1, max_attempts=1, min_request_gap_s=0, max_documents=100, max_browser_seconds=0))
        queue.track(901, source, fixture['candidate'])
        row = dict(source=source, candidate=fixture['candidate'].external_id, cycles=[])
        for iteration in (1, 2):
            with queue._db(write=True) as db:
                db.execute('UPDATE known_candidates SET next_check=0,last_checked=-1 WHERE owner=? AND source=? AND candidate_key=?',
                    (901, source, fixture['candidate'].external_id))
            cycle_id = engine.enqueue(901, source, force=True)
            results = []
            for _ in range(6):
                jobs = engine.ready_jobs()
                if not jobs: break
                results.append(engine.process_job(jobs[0]))
            state = queue.cycle(cycle_id, 901)
            observations = queue.observations(901, source=source)
            assert not any(o['summary'].get('validation_status') == 'valid' for o in observations)
            assert len(observations) <= 1, 'repeated blocked document manifest must deduplicate'
            assert state['status'] != 'completed'
            with queue._db() as db:
                assert db.execute('SELECT 1 FROM known_candidates WHERE owner=? AND source=? AND candidate_key=?',
                    (901, source, fixture['candidate'].external_id)).fetchone()
            row['cycles'].append(dict(iteration=iteration,status=state['status'],reasons=state['reasons'],
                observations=len(observations),valid_observations=0,known_candidate_preserved=True,job_results=results))
        row['passed'] = True; report['sources'].append(row)
        print(source, 'two conservative cycles; known candidate preserved', flush=True)
    assert all(d.closed and not d.download_calls for d in drivers)
    report.update(passed=len(report['sources']) == 4, downloads=0, drivers_closed=len(drivers), metrics=queue.metrics(901))
    Path('../docs/tenderproof-batch30-blocked-replay.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
