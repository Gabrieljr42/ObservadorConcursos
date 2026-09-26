"""Read-only batch60 evidence audit; never changes rollout gates or registration."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT/'docs'
BACKEND = ROOT/'backend'
sys.path.insert(0, str(BACKEND))
from app.tenderproof.source_adapters import SOURCE_ADAPTERS


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def relative(path):
    return path.resolve().relative_to(ROOT).as_posix()


def validate_sample(report, cycle, attempt, capture_dirs):
    root = Path(report['root']).resolve()
    if not root.is_relative_to(BACKEND/'.tenderproof'):
        raise ValueError('evidence volume outside isolated backend roots')
    artifact = attempt['artifact']
    storage = root/'artifacts'/artifact['storage_path']
    if not storage.resolve().is_relative_to(root/'artifacts'):
        raise ValueError('artifact path escaped preserved volume')
    if storage.stat().st_size != artifact['byte_len'] or digest(storage) != artifact['sha256']:
        raise ValueError('artifact bytes/hash differ from report')
    with storage.open('rb') as stream:
        if stream.read(4) != b'%PDF':
            raise ValueError('artifact is not PDF')
    with closing(sqlite3.connect((root/'operational.sqlite3').as_uri()+'?mode=ro', uri=True)) as connection:
        saved = connection.execute('SELECT payload FROM runs WHERE run_id=?', (attempt['run_id'],)).fetchone()
    if not saved:
        raise ValueError('run missing from durable operational database')
    run = json.loads(saved[0])
    if (run.get('execution_status') != 'completed' or run.get('validation_status') != 'valid'
            or run.get('source') != cycle['source']
            or run.get('selected_candidate_id') != attempt['candidate']['candidate_id']
            or (run.get('artifact') or {}).get('sha256') != artifact['sha256']):
        raise ValueError('durable run does not corroborate report status/source/candidate/hash')
    capture_paths = []
    for capture in [*cycle.get('captures', []), *attempt.get('captures', [])]:
        name = capture['file']
        if Path(name).name != name:
            raise ValueError('capture file is not a filename')
        matches = [folder/name for folder in capture_dirs if (folder/name).is_file() and digest(folder/name) == capture['sha256']]
        if not matches:
            raise ValueError('capture file absent or hash differs: '+name)
        capture_paths.append(relative(matches[0]))
    if not capture_paths:
        raise ValueError('no preserved listing/detail capture evidence')
    return {'artifact_path': relative(storage), 'artifact_sha256': artifact['sha256'], 'artifact_bytes': artifact['byte_len'], 'capture_paths': sorted(set(capture_paths)), 'persisted_run_checked': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DOCS/'tenderproof-batch60-current-validation.json')
    args = parser.parse_args()
    plan = read(DOCS/'tenderproof-rollout-plan.json')
    batch = next(b for b in plan['batches'] if b['cumulative_sources'] == 60)
    previous = next(b for b in plan['batches'] if b['cumulative_sources'] == 30)
    sources = batch['sources']
    if len(sources) != 30 or len(set(sources)) != 30:
        raise ValueError('batch60 must contain thirty distinct additions')
    # Read every group/live/recovery report, retaining earlier failed trials.
    inputs = {p.name: read(p) for p in sorted(DOCS.glob('tenderproof-batch60-*.json')) if p.resolve() != args.output.resolve()}
    capture_dirs = list((BACKEND/'tests/fixtures').glob('tenderproof_batch60*'))
    rows_by_source = defaultdict(list)
    attempt_records, cycle_records, errors = [], [], []
    audited_paths, unique_candidates, attempted_candidates = {}, set(), set()
    for filename, report in inputs.items():
        for cycle in report.get('cycles', []):
            source = cycle.get('source')
            if source not in sources:
                continue
            offline = report.get('network_requests') == 0
            cycle_records.append({'report': filename, 'source': source, 'cycle': cycle.get('cycle'), 'offline_revalidation': offline})
            for attempt in cycle.get('attempts', []):
                candidate = attempt.get('candidate') or {}
                external = candidate.get('external_id')
                attempted_candidates.add((source, external))
                item = {'report': filename, 'source': source, 'cycle': cycle.get('cycle'), 'external_id': external,
                        'run_id': attempt.get('run_id'), 'execution_status': attempt.get('execution_status'),
                        'validation_status': attempt.get('validation_status'), 'offline_page_revalidation': offline,
                        'error': attempt.get('error')}
                attempt_records.append(item)
                if attempt.get('execution_status') != 'completed' or attempt.get('validation_status') != 'valid':
                    continue
                try:
                    checked = validate_sample(report, cycle, attempt, capture_dirs)
                except (ValueError, KeyError, OSError, sqlite3.Error) as exc:
                    errors.append({'report': filename, 'source': source, 'run_id': attempt.get('run_id'), 'error': str(exc)})
                    continue
                item = {**item, **checked, 'total_pages': attempt.get('total_pages'), 'processed_pages': attempt.get('processed_pages'), 'explicit_page_limit': attempt.get('explicit_page_limit', 60)}
                rows_by_source[source].append(item)
                unique_candidates.add((source, external))
                audited_paths[item['artifact_path']] = checked
    blockers = inputs.get('tenderproof-batch60-blockers.json', {}).get('unresolved', {})
    blockers.update({'gualimp_open': 'Official initial detail/JSON captures succeeded, but subsequent two-cycle acquisition received browser challenge HTTP403; no valid PDF.',
                     'contemax_open': 'Observed official principal HTTPS connection failed; no PDF bytes or insecure fallback.',
                     'idib_open': 'No implemented adapter or validated PDF evidence in this batch.',
                     'jcm_open': 'No implemented adapter or validated PDF evidence in this batch.'})
    source_rows = []
    for source in sources:
        samples = rows_by_source[source]
        paired = defaultdict(set)
        for sample in samples:
            paired[(sample['report'], sample['external_id'])].add(sample['cycle'])
        source_rows.append({'source': source, 'adapter_registered': source in SOURCE_ADAPTERS,
            'evidence_status': 'verified_valid_sample' if samples else ('implemented_without_valid_pdf' if source in SOURCE_ADAPTERS else 'contract_missing'),
            'homologation_state': 'pending', 'coverage': 'bounded samples only; whole-source coverage unproven',
            'two_cycles_same_candidate_verified': any({1,2}.issubset(cycles) for cycles in paired.values()),
            'distinct_valid_candidates': len({s['external_id'] for s in samples}),
            'distinct_valid_pdf_hashes': len({s['artifact_sha256'] for s in samples}),
            'blocker': None if samples else blockers.get(source, 'No verified valid sample in available evidence.'),
            'samples': samples})
    tests = []
    for path in sorted((BACKEND/'.tenderproof').glob('batch60*.xml')):
        suites = list(ElementTree.parse(path).getroot().iter('testsuite'))
        tests.append({'file': relative(path), 'tests': sum(int(s.get('tests',0)) for s in suites), 'failures': sum(int(s.get('failures',0)) for s in suites), 'errors': sum(int(s.get('errors',0)) for s in suites), 'skipped': sum(int(s.get('skipped',0)) for s in suites)})
    unique_hashes = {item['artifact_sha256']: item['artifact_bytes'] for item in audited_paths.values()}
    hash_sources = defaultdict(set)
    for source, samples in rows_by_source.items():
        for sample in samples:
            hash_sources[sample['artifact_sha256']].add(source)
    offline_only = [r['source'] for r in source_rows if r['samples'] and all(s['offline_page_revalidation'] for s in r['samples'])]
    output = {'generated_at': datetime.now(timezone.utc).isoformat(), 'batch_gate': batch['gate'],
        'observed_plan_gate': batch['gate'], 'previous_batch30_gate_preserved': previous['gate'],
        'scope': 'Read-only report, fixture, persisted-run and PDF-byte audit. Page-limit recovery is offline revalidation, not process-crash recovery or an extra HTTP acquisition.',
        'registration': {'total_registered_adapters': len(SOURCE_ADAPTERS), 'batch_additions': len(sources), 'batch_registered_adapters': sum(s in SOURCE_ADAPTERS for s in sources), 'batch_missing_adapters': [s for s in sources if s not in SOURCE_ADAPTERS]},
        'counts': {'sources_with_verified_valid_pdf': sum(bool(r['samples']) for r in source_rows),
            'sources_with_two_verified_cycles': sum(r['two_cycles_same_candidate_verified'] for r in source_rows),
            'sources_without_verified_valid_pdf': sum(not r['samples'] for r in source_rows),
            'attempt_records_including_failed_trials': len(attempt_records), 'distinct_attempted_source_candidate_pairs': len(attempted_candidates),
            'distinct_valid_source_candidate_pairs': len(unique_candidates), 'valid_sample_records_including_offline_reprocessing': sum(len(r['samples']) for r in source_rows),
            'distinct_durable_pdf_files_verified': len(audited_paths), 'distinct_pdf_sha256_verified': len(unique_hashes),
            'physical_verified_pdf_bytes': sum(p['artifact_bytes'] for p in audited_paths.values()), 'deduplicated_verified_pdf_bytes': sum(unique_hashes.values())},
        'sources_requiring_offline_page_limit_revalidation': offline_only,
        'pdf_hashes_shared_across_source_entries': [{'sha256': sha, 'sources': sorted(names)} for sha,names in sorted(hash_sources.items()) if len(names)>1],
        'source_count_note': 'Catalogue entries are counted separately; shared PDF hashes do not become distinct documents or prove independent source families.',
        'cycle_records': cycle_records, 'validation_status_records': dict(Counter(a['validation_status'] for a in attempt_records)),
        'audit_errors': errors, 'junit_reports': tests, 'tests_note': 'Per-report counts overlap; do not sum these suites as unique tests.',
        'remaining_gate_requirements': ['Continuous replay for all new valid and blocked sources with deduplication and failure isolation.', 'Real process-crash recovery for the new valid source scope.', 'Mixed queue capacity proof covering the new batch and retry behavior.', 'Canonical creation/update review evidence from preserved new-batch PDFs with documentary holds.', 'Resolve missing contracts and external/documentary impediments or explicitly adjudicate their bounded exclusion before gate acceptance.'],
        'whole_source_coverage_certified': False, 'gate_acceptance_written': False, 'production_activation_performed': False,
        'input_reports': [{'file': 'docs/'+name, 'sha256': digest(DOCS/name)} for name in inputs], 'sources': source_rows}
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps({'registration': output['registration'], 'counts': output['counts'], 'audit_errors': errors}, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
