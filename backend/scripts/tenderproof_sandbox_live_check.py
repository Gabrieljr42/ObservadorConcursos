"""Single authorized Sandbox check; durable one-shot marker prevents a second run.

2026-09-07 authorization: 1 base Sandbox, 1 CPU/2 GB, 60+10 seconds,
one synthetic one-page PDF, one creation attempt, USD .002 reserved.
Do not remove the marker to retry; a new resource needs separate authorization.
"""
from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


def prepare_single_page_fixture() -> bytes:
    from io import BytesIO
    from pypdf import PdfReader
    from app.tenderproof.demo_pdf import make_text_pdf
    # Each list entry is a PAGE, not a line. Verify the actual bytes before create.
    pdf = make_text_pdf(['TenderProof authorized synthetic sandbox check.\nOne page; no official portal data.'])
    if len(PdfReader(BytesIO(pdf), strict=True).pages) != 1:
        raise ValueError('fixture_must_have_exactly_one_page')
    return pdf


def main():
    from dotenv import dotenv_values
    from app.tenderproof.processing import ProcessingService, ProcessingLimits
    from app.tenderproof.processing_solari import SolariSandboxProcessor

    logging.disable(logging.CRITICAL)
    revision = sys.argv[1] if len(sys.argv) == 2 else 'original'
    if revision not in ('original', 'zipapp-v2', 'zipapp-v3-one-page'):
        raise ValueError('invalid_operation_revision')
    root = BACKEND / '.tenderproof' / ('sandbox-live-authorized-20260907' if revision == 'original'
                                      else 'sandbox-live-authorized-20260907-' + revision)
    root.mkdir(parents=True, exist_ok=True)
    report_path = root / 'report.json'
    marker = root / 'authorization-consumed.json'
    if marker.exists():
        print(json.dumps({'state': 'already_attempted', 'new_resources_created': 0,
                          'note': 'One-shot authorization already consumed; inspect protected report.'}))
        return 2
    key = dotenv_values(BACKEND / '.env').get('SOLARI_API_KEY')
    if not key:
        print(json.dumps({'state': 'blocked', 'code': 'replacement_key_missing'}))
        return 2
    started = time.monotonic()
    events = []

    class ObservedProcessor(SolariSandboxProcessor):
        def _request(self, method, path, **kwargs):
            # Route labels only: capabilities and query tokens are never persisted here.
            parsed_path = urlsplit(path).path
            if parsed_path == '/sandboxes':
                label = 'create'
            elif method == 'DELETE':
                label = 'close'
            elif parsed_path.endswith('/exec'):
                label = 'fixed_pdf_command'
            elif parsed_path.endswith('upload-url'):
                label = 'mint_upload'
            elif parsed_path.endswith('download-url'):
                label = 'mint_download'
            elif parsed_path.endswith('/upload'):
                label = 'upload'
            elif parsed_path.endswith('/download'):
                label = 'download'
            else:
                label = 'status'
            entry = {'operation': label, 'at': datetime.now(timezone.utc).isoformat()}
            try:
                status, raw = super()._request(method, path, **kwargs)
                entry['http_status'] = status
                try:
                    body = json.loads(raw)
                    if isinstance(body, dict):
                        code = body.get('code')
                        if code in ('InsufficientCredit', 'NotEntitled', 'FeatureRequiresPlan',
                                    'ValidationError', 'ConcurrencyLimitExceeded'):
                            entry['provider_code'] = code
                        if label == 'fixed_pdf_command' and type(body.get('exitCode')) is int:
                            entry['exit_code'] = body['exitCode']
                        if label == 'close':
                            entry['provider_ok'] = body.get('ok') is True
                except Exception:
                    pass
                return status, raw
            except Exception:
                entry['error'] = 'transport_or_bounded_request_failed'
                raise
            finally:
                events.append(entry)
                report_path.write_text(json.dumps({'state': 'in_progress', 'events': events}, indent=2), encoding='utf-8')

    pdf = prepare_single_page_fixture()
    processor = ObservedProcessor(key, live_authorized=True, authorized_resources=1, authorized_seconds=60)
    if revision != 'original' and (processor.bundle_manifest['bundle_sha256'] !=
                                   '88f4f0e21e33f048c55b410c67d016a917a6912a918f02e576675831e7d7a2d8' or
                                   processor.bundle_manifest['bundle_bytes'] != 376355):
        raise ValueError('authorized_bundle_mismatch')
    service = ProcessingService(root / 'jobs', concurrency=1, budget_usd=.002, remote=processor)
    limits = ProcessingLimits(max_bytes=100_000, max_pages=1, total_seconds=60,
                              operation_seconds=30, max_output_bytes=100_000,
                              max_attempts=1, budget_usd=.002)
    job = service.enqueue('authorized-local-review', pdf, mode='solari', limits=limits)
    with marker.open('x', encoding='utf-8') as handle:
        json.dump({'job_id': job['id'], 'at': datetime.now(timezone.utc).isoformat(),
                   'max_creations': 1, 'budget_usd': .002}, handle)
    result = service.execute(job['id'], 'authorized-local-review')
    creation = next((e for e in events if e['operation'] == 'create'), {})
    if creation.get('http_status') in (400, 401, 402, 403, 404, 409, 429):
        service._mutate(job['id'], 'authorized-local-review', creation_unknown=False)
        result = service.get(job['id'], 'authorized-local-review')
    report = {'at': datetime.now(timezone.utc).isoformat(), 'fixture': 'synthetic one-page PDF',
              'operation_revision': revision, 'bundle_manifest': processor.bundle_manifest,
              'fixture_pages_verified_before_create': 1,
              'authorization': {'resources': 1, 'seconds': 60, 'cleanup_seconds': 10, 'budget_usd': .002},
              'job': result, 'events': events, 'observed_wall_seconds': round(time.monotonic()-started, 3),
              'provider_invoice_usd': None, 'provider_invoice_status': 'not_available'}
    if result['state'] == 'succeeded':
        output = service.result(job['id'], 'authorized-local-review')
        report['verified_pages'] = output['total_pages']
        report['fixture_text_verified'] = 'TenderProof authorized synthetic sandbox check.' in output['pages'][0]['text']
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        print(json.dumps({'state': 'failed', 'code': 'check_failed_without_logging_sensitive_exception',
                          'instruction': 'Inspect protected ledger; do not repeat resource creation.'}))
        sys.exit(1)
