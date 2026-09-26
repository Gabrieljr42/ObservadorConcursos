"""Local acceptance receipt; credentials are read in memory and never emitted."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx


def main():
    root = Path(__file__).resolve().parents[1]
    credentials = (root / '.tenderproof/local-pilot/ACESSO-LOCAL.md').read_text(encoding='utf-8')
    email = re.search(r'E-mail:\s*([^\r\n]+)', credentials)[1].strip(' `')
    password = re.search(r'Senha:\s*([^\r\n]+)', credentials)[1].strip(' `')
    run_id = 'tp-tcj-f919f71f0a9051d9baae5ff0e2acae7f-1'
    prefix = '/tenderproof/continuous/document-review/' + run_id
    with httpx.Client(base_url='http://localhost:13000/api', trust_env=False, timeout=45) as client:
        login = client.post('/auth/login', json={'email': email, 'password': password})
        assert login.status_code == 200, f'Login status {login.status_code}'
        client.headers['Authorization'] = 'Bearer ' + login.json()['access_token']
        response = client.get(prefix + '/current')
        assert response.status_code == 200
        case = response.json()
        region = next(r for r in case['ocr_regions'] if r.get('preview_effects'))
        result = client.post(prefix + '/cases/' + case['id'] + '/registration-targets',
                             json={'revision_hash': case['revision_hash'], 'region_id': region['id']})
        assert result.status_code == 200, f'Comparison status {result.status_code}'
        comparison = result.json()
        assert comparison['status'] == 'missing_contest' and comparison['published'] is False
        after_response = client.get(prefix + '/current')
        assert after_response.status_code == 200
        after = after_response.json()
        assert after['draft'] == case['draft'] and after['draft_revision'] == case['draft_revision']
        assert after['approved_at'] is None
    receipt = {'verified_at': datetime.now(timezone.utc).isoformat(), 'run_id': run_id,
               'comparison': comparison, 'draft_unchanged': True, 'approved_at': None,
               'ui_verified': 'Conferir cargo no catálogo displays missing original identity/roles; no publication.'}
    output = root / '.tenderproof/product-completion/facepe/registration-target-runtime.json'
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': comparison['status'], 'draft_revision': after['draft_revision'],
                      'draft_unchanged': True, 'published': False}))


if __name__ == '__main__':
    main()
