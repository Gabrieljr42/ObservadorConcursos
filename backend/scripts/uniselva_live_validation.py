"""Two public HTTP cycles of observed selection 1363; isolated acquisition only."""
import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tenderproof.batch30_uniselva_adapter import UniselvaAdapter
from app.tenderproof.source_adapters import SOURCE_ADAPTERS
import tenderproof_pilot_live as probe


class JSONCapturingDriver(probe.CapturingDriver):
    def _save(self, kind, url, html):
        json.loads(html)
        super()._save(kind, url, html)
        self.captures[-1]['format'] = 'decoded public JSON normalized to UTF-8; fixture bytes preserved'


def normalize_report(report, root):
    """Normalize previous captures without acquisition; reopen artifacts through store."""
    report['root'] = str(root.resolve())
    report['tls_verified'] = True
    source = report['source']
    cycles = []
    for row in report['cycles']:
        if 'attempts' in row:
            raise ValueError('report is already normalized')
        run = probe.TenderProofStore().get_run(row['run_id'])
        if run is None:
            raise ValueError('preserved run unavailable')
        for capture in row['captures']:
            body = (probe.CAPTURE / capture['file']).read_bytes()
            if hashlib.sha256(body).hexdigest() != capture['sha256']:
                raise ValueError('capture hash mismatch')
            json.loads(body)
            capture['format'] = 'decoded public JSON normalized to UTF-8; fixture bytes preserved'
        attempt = {key: value for key, value in row.items() if key not in ('cycle', 'coverage', 'captures')}
        attempt['captures'] = [c for c in row['captures'] if c['kind'] == 'detail']
        attempt['total_pages'] = run.total_pages
        attempt['processed_pages'] = run.processed_pages
        attempt['fields'] = [{'field': f.field_name, 'state': f.state} for f in run.fields]
        if run.artifact:
            body = probe.TenderProofStore().load_artifact_bytes(run.artifact)
            verified = body is not None and hashlib.sha256(body).hexdigest() == run.artifact.sha256
            if not verified:
                raise ValueError('durable artifact hash mismatch')
            attempt['durable_hash_verified'] = verified
        cycles.append({'source': source, 'cycle': row['cycle'], 'listing_run_id': row['run_id'],
            'listing_status': 'awaiting_selection', 'candidates_sampled': len(run.candidates),
            'coverage': row['coverage'], 'captures': [c for c in row['captures'] if c['kind'] == 'listing'],
            'attempts': [attempt]})
    return {**report, 'cycles': cycles}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--normalize-only', action='store_true', help='reuse preserved run/bytes; no HTTP')
    args = parser.parse_args()
    adapter = UniselvaAdapter()
    SOURCE_ADAPTERS[adapter.source] = adapter
    root = Path('.tenderproof/uniselva-live-20260908').resolve()
    os.environ['TENDERPROOF_ARTIFACT_DIR'] = str(root / 'artifacts')
    probe.CAPTURE = Path('tests/fixtures/tenderproof_batch30_institutional')
    output = Path('../docs/tenderproof-batch30-uniselva-live.json')
    if args.normalize_only:
        report = normalize_report(json.loads((root / 'report.json').read_text(encoding='utf-8')), root)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
        print('normalized preserved cycles:', len(report['cycles']), flush=True)
        sys.exit(0)
    report = {'observed_at': datetime.now(timezone.utc).isoformat(), 'source': adapter.source, 'root': str(root),
              'scope': 'two first-page discoveries; selection1363 observed on page1; partial coverage; no canonical publication',
              'browser_sessions': 0, 'cycles': []}
    for cycle in (1, 2):
        settings = probe.TenderProofSettings(allowlist_hosts=adapter.allowed_hosts,
            limits=probe.TenderProofLimits(max_candidates=9, max_documents=20, max_navigations=3, max_pages=60, total_timeout_s=120))
        service = probe.TenderProofService(probe.TenderProofStore(), settings)
        driver = JSONCapturingDriver(adapter.source, settings, cycle)
        run = service.start_discovery(driver, source=adapter.source, listing_url=adapter.listing_urls[0], mode='real', owner_user_id=901)
        candidate = next(c for c in run.candidates if c.external_id == '1363')
        detail_driver = JSONCapturingDriver(adapter.source, settings, cycle)
        run = service.select_and_process(run.run_id, candidate.candidate_id, detail_driver)
        record = {'cycle': cycle, 'run_id': run.run_id, 'candidate': candidate.model_dump(mode='json'),
            'execution_status': run.execution_status, 'validation_status': run.validation_status, 'error': run.error,
            'coverage': run.coverage, 'captures': driver.captures + detail_driver.captures,
            'artifact': run.artifact.model_dump(mode='json') if run.artifact else None,
            'document': run.document.model_dump(mode='json') if run.document else None,
            'validation': run.validation.model_dump(mode='json') if run.validation else None}
        if run.artifact:
            record['durable_hash_verified'] = hashlib.sha256(probe.TenderProofStore().load_artifact_bytes(run.artifact)).hexdigest() == run.artifact.sha256
        report['cycles'].append(record)
        (root / 'report.json').parent.mkdir(parents=True, exist_ok=True)
        (root / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
        print(cycle, run.execution_status, run.validation_status, run.error, flush=True)
    output.write_text(json.dumps(normalize_report(report, root), ensure_ascii=False, indent=2, default=str), encoding='utf-8')
