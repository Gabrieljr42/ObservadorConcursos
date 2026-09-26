"""Preserve a bounded real acquisition of the observed public API contract."""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
from app.tenderproof.fumarc_publications import publication_url, parse_publications, downloadable_pdf
from app.tenderproof.tls_chain import source_tls_verification


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('contest_id', type=int)
    args = parser.parse_args()
    url = publication_url(args.contest_id)
    root = Path(__file__).resolve().parents[1] / '.tenderproof/product-completion/fumarc' / datetime.now(timezone.utc).strftime('publications-%Y%m%dT%H%M%S%fZ')
    root.mkdir(parents=True, exist_ok=False)
    seen, identities, records = set(), set(), []
    report = {'contest_id': args.contest_id, 'tls_verified': True, 'pages': records,
              'scope': 'Public API acquisition and parser verification only; not publication or adapter registration.'}
    try:
        with httpx.Client(verify=source_tls_verification('fumarc_open'), trust_env=False,
                          follow_redirects=False, timeout=12,
                          headers={'Accept': 'application/json;odata=verbose', 'User-Agent': 'ObservadorDeConcursos/1.0'}) as client:
            while url:
                if url in seen or len(seen) >= 20:
                    raise ValueError('paginação incompleta ou circular')
                seen.add(url)
                with client.stream('GET', url) as response:
                    response.raise_for_status()
                    content = bytearray()
                    for chunk in response.iter_bytes():
                        content.extend(chunk)
                        if len(content) > 2 * 1024 * 1024:
                            raise ValueError('página excede limite')
                page = parse_publications(content.decode('utf-8-sig'), url, args.contest_id)
                for row in page.rows:
                    if row['Id'] in identities:
                        raise ValueError('publicação duplicada entre páginas')
                    identities.add(row['Id'])
                    downloadable_pdf(row)
                name = f'page-{len(seen)}.json'
                (root / name).write_bytes(content)
                records.append({'file': name, 'url': url, 'sha256': hashlib.sha256(content).hexdigest(),
                                'count': len(page.rows), 'terminal': page.next_url is None})
                url = page.next_url
        report['complete_pagination'] = True
    except Exception as exc:
        report['complete_pagination'] = False
        report['error_type'] = type(exc).__name__
        raise
    finally:
        report['unique_publications'] = len(identities)
        report['observed_at'] = datetime.now(timezone.utc).isoformat()
        (root / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'pages': len(records), 'unique_publications': len(identities),
                          'complete_pagination': report['complete_pagination'], 'evidence': str(root)}))


if __name__ == '__main__':
    main()
