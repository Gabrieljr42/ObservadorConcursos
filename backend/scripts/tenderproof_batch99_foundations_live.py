"""Two bounded real cycles through the normal registry; isolated evidence only."""
import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tenderproof.acquisition import new_run_id
from app.tenderproof.batch99_foundation_adapters import BATCH99_FOUNDATION_ADAPTERS
from app.tenderproof.batch99_foundation_adapters import BATCH99_FOUNDATION_PUBLIC_ALTERNATIVE_ADAPTERS
from app.tenderproof.batch99_foundation_adapters import BATCH99_FOUNDATION_SECTION_ADAPTERS, BATCH99_FOUNDATION_FAPESE_ADAPTERS
from app.tenderproof.http_driver import BoundedHTTPDriver
from app.tenderproof.security import TenderProofLimits, TenderProofSettings
from app.tenderproof.service import TenderProofService
from app.tenderproof.store import TenderProofStore

FIX = Path(__file__).resolve().parents[1]/'tests/fixtures/tenderproof_batch99_foundations'

class CaptureDriver(BoundedHTTPDriver):
    instances = []
    def __init__(self, source, settings, cycle):
        super().__init__(source, settings)
        self.cycle, self.captures = cycle, []
        self.instances.append(self)
    def save(self, kind, url, html):
        raw = html.encode('utf8')
        name = f'{self.adapter.source}-cycle{self.cycle}-{kind}-{hashlib.sha256(raw).hexdigest()[:12]}.html'
        (FIX/name).write_bytes(raw)
        self.captures.append({'kind': kind, 'url': url, 'file': name,
                              'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
                              'format': 'decoded public HTTP HTML normalized to UTF-8',
                              'observed_at': datetime.now(timezone.utc).isoformat()})
        return html
    def open_listing(self, url):
        return self.save('listing', url, super().open_listing(url))
    def open_detail(self, url):
        return self.save('detail', url, super().open_detail(url))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', nargs='*')
    parser.add_argument('--root', default='.tenderproof/r99found')
    parser.add_argument('--report', default='../docs/tenderproof-batch99-foundations-live.json')
    args = parser.parse_args()
    root, output = Path(args.root).resolve(), Path(args.report).resolve()
    if root.exists():
        parser.error('preserve existing evidence; use a fresh root')
    os.environ['TENDERPROOF_ARTIFACT_DIR'] = str(root/'artifacts')
    os.environ['TENDERPROOF_PROCESSING_DIR'] = str(root/'processing')
    os.environ['TENDERPROOF_PROCESSING_MODE'] = 'local'
    os.environ['TENDERPROOF_BROWSER_LIVE_ENABLED'] = 'false'
    adapters = [a for source, a in {**BATCH99_FOUNDATION_ADAPTERS,**BATCH99_FOUNDATION_PUBLIC_ALTERNATIVE_ADAPTERS,**BATCH99_FOUNDATION_SECTION_ADAPTERS,**BATCH99_FOUNDATION_FAPESE_ADAPTERS}.items() if not args.sources or source in args.sources]
    if not adapters:
        parser.error('no implemented foundation selected')
    report = {'root': str(root), 'observed_at': datetime.now(timezone.utc).isoformat(),
              'scope': 'two bounded samples, not full source coverage or publication',
              'tls_verified': True, 'browser_sessions': 0,
              'limits': {'listing_pages_per_cycle': 1, 'detail_attempts_per_cycle': 3,
                         'html_bytes': 2097152, 'driver_deadline_s': 25,
                         'pdf_bytes': 30*1024*1024, 'pdf_pages': 60}, 'cycles': []}
    try:
        for cycle in (1, 2):
            for adapter in adapters:
                start = time.monotonic()
                settings = TenderProofSettings(allowlist_hosts=adapter.allowed_hosts,
                    limits=TenderProofLimits(max_candidates=5, max_documents=100,
                        max_navigations=8, max_pages=60, max_attempts=1, total_timeout_s=25))
                service = TenderProofService(TenderProofStore(), settings)
                driver = CaptureDriver(adapter.source, settings, cycle)
                try:
                    listing = service.start_discovery(driver, source=adapter.source,
                        listing_url=adapter.listing_urls[0], mode='real', owner_user_id=901)
                finally:
                    driver.close()
                record = {'source': adapter.source, 'cycle': cycle,
                          'listing_run_id': listing.run_id, 'listing_status': listing.execution_status,
                          'coverage': listing.coverage, 'captures': driver.captures, 'attempts': []}
                report['cycles'].append(record)
                for candidate in listing.candidates[:3]:
                    run = listing.model_copy(deep=True)
                    run.run_id = new_run_id()
                    service.store.put_run(run)
                    detail = CaptureDriver(adapter.source, settings, cycle)
                    try:
                        run = service.select_and_process(run.run_id, candidate.candidate_id, detail)
                    finally:
                        detail.close()
                    row = {'run_id': run.run_id, 'candidate': candidate.model_dump(mode='json'),
                           'execution_status': run.execution_status, 'validation_status': run.validation_status,
                           'error': run.error, 'captures': detail.captures,
                           'document': run.document.model_dump(mode='json') if run.document else None,
                           'artifact': run.artifact.model_dump(mode='json') if run.artifact else None,
                           'total_pages': run.total_pages, 'processed_pages': run.processed_pages,
                           'validation': run.validation.model_dump(mode='json') if run.validation else None}
                    if run.artifact:
                        data = TenderProofStore().load_artifact_bytes(run.artifact)
                        row['durable_hash_verified'] = hashlib.sha256(data).hexdigest() == run.artifact.sha256
                    record['attempts'].append(row)
                    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str)+'\n', encoding='utf8')
                    print(adapter.source, cycle, candidate.external_id, run.execution_status.value,
                          run.validation_status.value if run.validation_status else None, run.error, flush=True)
                    if run.execution_status.value == 'completed' and run.validation_status.value == 'valid':
                        break
                record['duration_s'] = round(time.monotonic()-start, 3)
    finally:
        for driver in CaptureDriver.instances:
            driver.close()
        report['driver_cleanup'] = {'instances': len(CaptureDriver.instances),
            'all_clients_closed': all(d.client.is_closed for d in CaptureDriver.instances)}
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str)+'\n', encoding='utf8')

if __name__ == '__main__':
    main()
