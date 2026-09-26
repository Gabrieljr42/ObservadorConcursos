"""Download every document of calls in the observed Abertos tab; isolate PDFs."""
import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import httpx
from app.tenderproof.fapepi_pages import LISTING, parse_listing, document_url
from app.tenderproof.processing import extract_pages_isolated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('inventory', type=Path)
    args = parser.parse_args()
    inventory = json.loads((args.inventory/'report.json').read_text(encoding='utf-8'))
    raw = (args.inventory/(inventory['listing_sha256']+'.html')).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == inventory['listing_sha256']
    listing = parse_listing(raw.decode('utf-8-sig'))
    targets = {r['url'] for r in listing['items'] if 'Abertos' in r['sections']}
    if not targets:
        raise ValueError('seção Abertos não identificada')
    calls = [r for r in inventory['documents'] if r['url'] in targets]
    if {r['url'] for r in calls} != targets:
        raise ValueError('detalhes abertos ainda não adquiridos')
    root = args.inventory.parent / datetime.now(timezone.utc).strftime('open-documents-%Y%m%dT%H%M%SZ')
    root.mkdir()
    report = {'listing_url': LISTING, 'listing_sha256': inventory['listing_sha256'],
        'calls': sorted(targets), 'documents': [], 'pending_links': [p for c in calls for p in c['pending_links']],
        'published': False, 'source_integrated': False}
    with httpx.Client(timeout=25, trust_env=False, follow_redirects=False) as client:
        for call in calls:
            for doc in call['documents']:
                record = {'call_url':call['url'], **doc}
                report['documents'].append(record)
                try:
                    document_url(doc['url'])
                    with client.stream('GET', doc['url']) as response:
                        response.raise_for_status()
                        content = bytearray()
                        for chunk in response.iter_bytes():
                            content.extend(chunk)
                            if len(content)>30*1024*1024:
                                raise ValueError('documento excede 30 MiB')
                    digest=hashlib.sha256(content).hexdigest()
                    extension=doc['url'].rsplit('.',1)[1].lower()
                    (root/(digest+'.'+extension)).write_bytes(content)
                    record.update(sha256=digest, bytes=len(content))
                    if extension != 'pdf':
                        raise ValueError('arquivo adquirido; leitura não PDF pendente')
                    pages,total,processed,truncated,errors=extract_pages_isolated(bytes(content),artifact_id='fapepi-'+digest,
                        owner_id='fapepi-scope-audit',max_bytes=30*1024*1024,max_pages=200)
                    (root/(digest+'-pages.json')).write_text(json.dumps([p.model_dump(mode='json') for p in pages],ensure_ascii=False),encoding='utf-8')
                    record.update(total_pages=total,processed_pages=processed,truncated=truncated,errors=errors)
                except Exception as exc:
                    record['error']=type(exc).__name__+': '+str(exc)
                (root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
                print(json.dumps({'processed':len(report['documents']),'error':record.get('error')}),flush=True)
                time.sleep(1)
    report['finished_at']=datetime.now(timezone.utc).isoformat()
    (root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(str(root),flush=True)


if __name__ == '__main__':
    main()
