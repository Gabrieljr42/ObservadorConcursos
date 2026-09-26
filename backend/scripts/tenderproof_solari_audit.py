"""Read-only Solari reconciliation. Never emit capabilities, credentials or bodies."""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from urllib.parse import quote

BACKEND = Path(__file__).resolve().parents[1]


async def audit() -> dict:
    from dotenv import dotenv_values
    from solari_browser import Solari

    snapshot = BACKEND / '.tenderproof/review/runs/tpr-c84fdce378eb.json'
    raw = snapshot.read_bytes()
    run = json.loads(raw)
    config = dotenv_values(BACKEND / '.env')
    report = {
        'audited_at': datetime.now(timezone.utc).isoformat(),
        'run_id': run['run_id'], 'snapshot_sha256': hashlib.sha256(raw).hexdigest(),
        'browser_sdk': version('solari-browser'),
        'patchright': version('patchright'),
        'key_source': 'backend/.env current replacement key only',
        'historical_key_identity': 'unknown',
        'configured_base_override_present': bool(config.get('SOLARI_BASE_URL')),
        'query_base': 'official production endpoint (fixed)',
        'new_resources_created': 0, 'sessions': [],
        'account_identity': 'session org can be compared by hash; dashboard organization identity remains unverified',
    }
    artifact = run.get('artifact') or {}
    artifact_path = snapshot.parent.parent / 'artifacts' / Path(artifact.get('storage_path') or 'missing').name
    if artifact_path.is_file():
        data = artifact_path.read_bytes()
        from pypdf import PdfReader
        from io import BytesIO
        report['artifact'] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                              'pages': len(PdfReader(BytesIO(data)).pages)}
    key = config.get('SOLARI_API_KEY')
    if not key:
        report['blocked'] = 'replacement_key_missing'
        return report
    async with Solari(api_key=key, base_url='https://api.getsolari.com', max_attempts=1, timeout_ms=15000) as client:
        for stored in run.get('sessions', []):
            sid = stored.get('session_id')
            if not isinstance(sid, str) or not sid:
                continue
            item = {'phase': stored['phase'], 'id_sha256': hashlib.sha256(sid.encode()).hexdigest(),
                    'local_closed_claim': stored.get('closed'), 'queries': []}
            for label, suffix in [('status', ''), ('replay', '/replay-url')]:
                entry = {'operation': label, 'at': datetime.now(timezone.utc).isoformat()}
                try:
                    response = await client.request('GET', '/sessions/' + quote(sid, safe='') + suffix)
                    entry['http_status'] = response.status_code
                    if response.status_code == 200:
                        body = response.json()
                        state = body.get('status')
                        if label == 'status' and state in ('active', 'released', 'expired', 'unknown'):
                            entry['provider_status'] = state
                            org = body.get('org')
                            if isinstance(org, str):
                                entry['org_sha256'] = hashlib.sha256(org.encode()).hexdigest()
                        if label == 'replay':
                            entry['url_returned'] = isinstance(body.get('url'), str)
                    else:
                        entry['conclusion'] = 'not_reconciled; does not prove prior existence or closure'
                except Exception:
                    entry['error'] = 'query_failed_without_logging_exception'
                item['queries'].append(entry)
            report['sessions'].append(item)
    return report


async def audit_sandbox_history() -> dict:
    from dotenv import dotenv_values
    from solari_browser import Solari
    config = dotenv_values(BACKEND / '.env')
    report = {'at': datetime.now(timezone.utc).isoformat(), 'operation': 'documented_read_only_sandbox_history',
              'new_resources_created': 0, 'query_base': 'official production endpoint (fixed)',
              'env_override_matches_official_production': (config.get('SOLARI_BASE_URL') or '').rstrip('/') == 'https://api.getsolari.com',
              'entries': []}
    key = config.get('SOLARI_API_KEY')
    if not key:
        return dict(report, blocked='replacement_key_missing')
    async with Solari(api_key=key, base_url='https://api.getsolari.com', max_attempts=1, timeout_ms=15000) as client:
        for directory in ('sandbox-live-authorized-20260907', 'sandbox-live-authorized-20260907-zipapp-v2',
                          'sandbox-live-authorized-20260907-zipapp-v3-one-page'):
            ledger = BACKEND / '.tenderproof' / directory / 'jobs/jobs.sqlite3'
            with sqlite3.connect('file:' + ledger.as_posix() + '?mode=ro', uri=True) as db:
                jobs = [json.loads(row[0]) for row in db.execute('SELECT data FROM processing_jobs')]
            for job in jobs:
                item = {'job_id': job['id'], 'local_close_confirmed': job['close_confirmed'], 'queries': []}
                paths = [('metadata_history', '/sandboxes?metadata.tenderproof_job=' + quote(job['id'], safe='') + '&limit=10'),
                         ('resource_status', '/sandboxes/' + quote(job['resource'], safe=''))]
                for label, path in paths:
                    entry = {'operation': label, 'at': datetime.now(timezone.utc).isoformat()}
                    try:
                        response = await client.request('GET', path)
                        entry['http_status'] = response.status_code
                        if response.status_code == 200:
                            data = response.json()
                            if label == 'metadata_history':
                                records = data.get('sandboxes', [])
                                entry['returned_records'] = len(records)
                                entry['matching_resource_count'] = sum(r.get('sandboxId') == job['resource'] for r in records)
                                entry['states'] = [r.get('state') for r in records if r.get('state') in
                                                   ('starting','running','paused','archived','releasing','gone')]
                                entry['more_pages'] = bool(data.get('nextCursor'))
                            elif data.get('state') in ('starting','running','paused','archived','releasing','gone'):
                                entry['provider_state'] = data['state']
                        else:
                            entry['conclusion'] = 'not_queryable; status alone does not establish prior lifecycle'
                    except Exception:
                        entry['error'] = 'query_failed_without_sensitive_exception'
                    item['queries'].append(entry)
                report['entries'].append(item)
    return report


async def audit_negative_auth() -> dict:
    """Exactly one documented status GET without Authorization; never guesses keys."""
    import httpx
    run = json.loads((BACKEND / '.tenderproof/review/runs/tpr-c84fdce378eb.json').read_text(encoding='utf-8'))
    session = run['sessions'][0]['session_id']
    names = ('SOLARI_API_KEY', 'SOLARI_BASE_URL', 'SOLARI_REGION')
    text = (BACKEND / '.env').read_text(encoding='utf-8')
    counts = {name: len(re.findall(r'^\s*(?:export\s+)?' + name + r'\s*=', text, re.MULTILINE)) for name in names}
    report = {'at': datetime.now(timezone.utc).isoformat(), 'operation': 'one_browser_status_get_without_authorization',
              'new_resources_created': 0, 'dotenv_assignment_counts': counts}
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=False, trust_env=False) as client:
            response = await client.get('https://api.getsolari.com/sessions/' + quote(session, safe=''))
            report['http_status'] = response.status_code
            report['unauthenticated_request_rejected'] = response.status_code in (401, 403)
    except Exception:
        report['error'] = 'query_failed_without_sensitive_exception'
    return report


if __name__ == '__main__':
    history = len(sys.argv) == 2 and sys.argv[1] == '--sandbox-history'
    negative = len(sys.argv) == 2 and sys.argv[1] == '--negative-auth'
    result = asyncio.run(audit_negative_auth() if negative else audit_sandbox_history() if history else audit())
    destination = BACKEND / '.tenderproof' / ('solari-negative-auth-audit.json' if negative else
                                            'solari-sandbox-history-audit.json' if history else 'solari-audit.json')
    destination.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
