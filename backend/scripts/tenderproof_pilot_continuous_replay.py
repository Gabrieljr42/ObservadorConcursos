"""Explicit OFFLINE replay of preserved official HTML/PDF through ContinuousEngine.

No HTTP/browser; fresh isolated volume. Two cycles prove integration, not a live
change of the source. Clock/priority adjustment is a controlled scheduling fixture.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tenderproof.contracts import TenderProofRun
from app.tenderproof.continuous import ContinuousEngine
from app.tenderproof.continuous_store import ContinuousStore, SourcePolicy
from app.tenderproof.source_adapters import get_source_adapter
from app.tenderproof.solari_adapter import DownloadedBytes
from app.tenderproof.store import TenderProofStore


class PreservedDriver:
    session_id = None
    replay_available = False

    def __init__(self, fixture):
        self.fixture = fixture
        self.closed = False

    def open_listing(self, url):
        if url != self.fixture['listing_url']:
            raise ValueError('offline fixture has no such listing')
        return self.fixture['listing_html']

    def open_detail(self, url):
        if url != self.fixture['candidate'].detail_url_observed:
            raise ValueError('offline fixture has no such detail')
        return self.fixture['detail_html']

    def download(self, url, *, max_bytes):
        run = self.fixture['run']
        if run.document and run.document.acquisition_request is not None:
            raise ValueError('preserved POST cannot be replayed as GET')
        if url != self.fixture['replay_document_url'] or len(self.fixture['pdf']) > max_bytes:
            raise ValueError('offline document absent or oversized')
        return DownloadedBytes(url_requested=url, url_final=run.artifact.url_final,
                               content=self.fixture['pdf'], content_type='application/pdf',
                               redirect_chain=[url, run.artifact.url_final])

    def download_document(self, document, candidate, *, max_bytes):
        # The preserved POST body is part of identity; endpoint alone is not
        # enough when original and retifications share an export route.
        run = self.fixture['run']
        expected = self.fixture['candidate']
        if (candidate.source, candidate.external_id, candidate.detail_url_observed) != (expected.source, expected.external_id, expected.detail_url_observed):
            raise ValueError('offline POST candidate differs from preserved run')
        if not run.document or not run.document.acquisition_request or not document.acquisition_request:
            raise ValueError('offline POST requires preserved acquisition request')
        if (document.doc_id != run.document.doc_id or document.url_requested != run.document.url_requested
                or document.acquisition_request.model_dump() != run.document.acquisition_request.model_dump()):
            raise ValueError('offline POST request differs from preserved run')
        adapter = get_source_adapter(candidate.source)
        validator = getattr(adapter, 'validate_document_request', None)
        if not callable(validator):
            raise ValueError('offline source lacks POST contract')
        validator(document, candidate)
        if run.artifact.url_final != document.url_requested or len(self.fixture['pdf']) > max_bytes:
            raise ValueError('offline POST redirect or oversized payload')
        if hashlib.sha256(self.fixture['pdf']).hexdigest() != run.artifact.sha256:
            raise ValueError('offline POST bytes differ from preserved artifact')
        return DownloadedBytes(url_requested=document.url_requested, url_final=run.artifact.url_final,
                               content=self.fixture['pdf'], content_type='application/pdf',
                               redirect_chain=[document.url_requested])

    def observed_json(self): return []
    def session_records(self): return []
    def replay_url(self): return None
    def diagnostics(self): return ['offline replay of preserved official bytes; no network']
    def close(self): self.closed = True


def capture(row, roots):
    for root in roots:
        path = root / row['file']
        if path.is_file():
            content = path.read_bytes()
            if hashlib.sha256(content).hexdigest() == row['sha256']:
                return content.decode('utf-8')
    raise ValueError('official capture absent or hash mismatch in explicit fixture roots')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--reports', type=Path, nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--capture-roots', type=Path, nargs='+', default=[Path('tests/fixtures/tenderproof_pilot')])
    parser.add_argument('--expected-sources', nargs='+')
    parser.add_argument('--source-page-limits', type=Path, help='Explicit per-source offline PDF limits backed by preserved recovery evidence')
    args = parser.parse_args()
    page_limits = json.loads(args.source_page_limits.read_text(encoding='utf-8')) if args.source_page_limits else {}
    if not isinstance(page_limits, dict) or any(type(v) is not int or not 1 <= v <= 200 for v in page_limits.values()):
        raise ValueError('offline page limits must be a source-to-integer map, bounded at 200')
    root = args.root.resolve()
    root.mkdir(parents=True, exist_ok=False)
    fixtures = {}
    for report_path in args.reports:
        report = json.loads(report_path.read_text(encoding='utf-8'))
        original = Path(report['root'])
        os.environ['TENDERPROOF_ARTIFACT_DIR'] = str(original / 'artifacts')
        for cycle in report['cycles']:
            if args.expected_sources and cycle['source'] not in args.expected_sources:
                continue
            for attempt in cycle['attempts']:
                if not attempt.get('artifact') or not attempt.get('captures'):
                    continue
                run = TenderProofStore().get_run(attempt['run_id'])
                if not run or not run.artifact or not run.document:
                    continue
                pdf = TenderProofStore().load_artifact_bytes(run.artifact)
                if not pdf:
                    raise ValueError('preserved PDF missing')
                candidate = next(c for c in run.candidates if c.candidate_id == run.selected_candidate_id)
                fixture = {'run':run, 'candidate':candidate, 'pdf':pdf,
                           'listing_url':cycle['captures'][0]['url'],
                           'listing_html':capture(cycle['captures'][0], args.capture_roots),
                           'detail_html':capture(attempt['captures'][0], args.capture_roots),
                           'origin_report':str(report_path)}
                adapter = get_source_adapter(cycle['source'])
                # Sanitized captures can omit ephemeral signed URL queries.
                # Reparse their actual manifest, validate both destinations and
                # require identical host/path before mapping preserved bytes.
                from urllib.parse import urlsplit
                selected = adapter.choose_document(adapter.documents(fixture['detail_html'], candidate))
                adapter.validate_document_url(run.document.url_requested, candidate)
                if selected.acquisition_request is not None or run.document.acquisition_request is not None:
                    if (selected.acquisition_request is None or run.document.acquisition_request is None
                            or selected.doc_id != run.document.doc_id
                            or selected.url_requested != run.document.url_requested
                            or selected.acquisition_request.model_dump() != run.document.acquisition_request.model_dump()):
                        raise ValueError('replay POST selection differs from preserved request')
                    adapter.validate_document_request(selected, candidate)

                before, after = urlsplit(run.document.url_requested), urlsplit(selected.url_requested)
                if (before.scheme, before.netloc, before.path) != (after.scheme, after.netloc, after.path):
                    raise ValueError('replay selected a different preserved document')
                fixture['replay_document_url'] = selected.url_requested
                if cycle['source'] not in fixtures or run.validation_status.value == 'valid':
                    fixtures[cycle['source']] = fixture
                if run.validation_status.value == 'valid':
                    break
    os.environ.update(TENDERPROOF_ARTIFACT_DIR=str(root / 'artifacts'),
                      TENDERPROOF_PROCESSING_DIR=str(root / 'processing'),
                      TENDERPROOF_CONTINUOUS_ENABLED='true', TENDERPROOF_CONTINUOUS_OPERATOR_USER_IDS='901',
                      TENDERPROOF_BROWSER_LIVE_ENABLED='false', TENDERPROOF_PUBLICATION_ENABLED='false')
    os.environ.pop('SOLARI_API_KEY', None)
    queue = ContinuousStore(root / 'continuous.sqlite3')
    engine = ContinuousEngine(queue=queue, driver_factory=lambda source, settings, **kwargs:PreservedDriver(fixtures[source]))
    report = {'validated_at':datetime.now(timezone.utc).isoformat(), 'scope':'offline official capture replay',
              'network_requests':0, 'browser_sessions':0, 'canonical_writes':0,
              'clock_fixture':'Between cycles only: advance selected candidate priority/due timestamp in isolated queue; preserve all other known candidates.',
              'root':str(root), 'sources':[]}
    for source, fixture in fixtures.items():
        adapter = get_source_adapter(source)
        adapter.validate_listing_url(fixture['listing_url'])
        adapter.listing_urls = (fixture['listing_url'],)
        queue.configure(901, source, SourcePolicy(enabled=True, mode='real', max_candidates=1,
                        max_listing_pages=1, max_attempts=1, min_request_gap_s=0, max_documents=100,
                        max_pdf_pages=page_limits.get(source,80), max_browser_seconds=0))
        queue.track(901, source, fixture['candidate'])
        row = {'source':source, 'candidate':fixture['candidate'].external_id,
               'document_sha256':fixture['run'].artifact.sha256, 'origin_report':fixture['origin_report'],
               'max_pdf_pages':page_limits.get(source,80), 'cycles':[]}
        for iteration in (1, 2):
            with queue._db(write=True) as db:
                db.execute('UPDATE known_candidates SET next_check=0,last_checked=-1 WHERE owner=? AND source=? AND candidate_key=?',
                           (901,source,fixture['candidate'].external_id))
            cycle = engine.enqueue(901,source,force=True)
            results=[]
            for _ in range(6):
                jobs = engine.ready_jobs()
                if not jobs:
                    break
                results.append(engine.process_job(jobs[0]))
            state = queue.cycle(cycle,901)
            observations = queue.observations(901,source=source)
            valid = [o for o in observations if o['summary'].get('validation_status')=='valid']
            row['cycles'].append({'iteration':iteration, 'status':state['status'], 'reasons':state['reasons'],
                                  'job_results':results, 'observations':len(observations), 'valid_observations':len(valid)})
            if len(valid) != 1 or len(observations) != 1:
                raise AssertionError(f'{source}: expected one deduplicated valid observation: {results}')
            saved = TenderProofStore().get_run(valid[0]['run_id'])
            assert hashlib.sha256(TenderProofStore().load_artifact_bytes(saved.artifact)).hexdigest() == row['document_sha256']
            listing_page = adapter.parse_listing(fixture['listing_html'], fixture['listing_url'], limit=1)
            if state['status'] == 'completed':
                assert listing_page.terminal_evidence and not listing_page.truncated and not listing_page.next_urls
                assert not state['reasons']
            else:
                assert state['status'] == 'partial' and state['reasons']
            row['listing_terminal_evidence'] = listing_page.terminal_evidence
            row['coverage_scope'] = 'captured listing/filter only; not all historical or other portal scopes'
        row['passed'] = True
        report['sources'].append(row)
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(source, 'two cycles, one valid observation, bounded listing coverage', flush=True)
    report['metrics'] = queue.metrics(901)
    actual = {row['source'] for row in report['sources']}
    report['expected_sources'] = args.expected_sources or 'legacy pilot: eight sources'
    report['passed'] = actual == set(args.expected_sources) if args.expected_sources else len(actual) == 8
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    if not report['passed']:
        raise AssertionError('required source replay evidence is missing')


if __name__ == '__main__': main()
