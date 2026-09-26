"""Real preserved official PDF processing under the task's shared USD20 ledger.

Run in the pilot container with SOLARI_API_KEY passed by environment. The unique
report directory prevents accidentally repeating this check and paid creation.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.tenderproof.processing import ProcessingService, ProcessingLimits
from app.tenderproof.processing_solari import SolariSandboxProcessor
from app.tenderproof.solari_budget import configured_budget
from app.tenderproof.store import get_store
from app.tenderproof.pdf_text import extract_pages


def main():
    root = Path('/var/lib/observador/tenderproof/product-sandbox-20260908-v2')
    budget = configured_budget()
    if budget is None or not os.getenv('SOLARI_API_KEY'):
        raise ValueError('configured budget and credentials required')
    source_run = get_store().get_run('tp-tcj-dccfc5d2d765587da05aa20032b70f2e-1')
    content = get_store().load_artifact_bytes(source_run.artifact)
    if hashlib.sha256(content).hexdigest() != source_run.artifact.sha256:
        raise ValueError('preserved bytes mismatch')
    local_pages, *_ = extract_pages(content, artifact_id=source_run.artifact.artifact_id)
    events = []
    report_path = root/'report.json'
    class ObservedProcessor(SolariSandboxProcessor):
        def _request(self, method, path, **kwargs):
            event = {'method': method, 'operation': 'create' if path == '/sandboxes' else
                     'close' if method == 'DELETE' else 'exec' if urlsplit(path).path.endswith('/exec') else 'transfer_or_status'}
            try:
                status, raw = super()._request(method, path, **kwargs)
                event['http_status'] = status
                return status, raw
            finally:
                events.append(event)
                report_path.write_text(json.dumps({'state':'in_progress','events':events}), encoding='utf-8')
    processor = ObservedProcessor(os.environ['SOLARI_API_KEY'], live_authorized=True,
                                 authorized_resources=1, authorized_seconds=120)
    root.mkdir(exist_ok=False)
    service = ProcessingService(root/'jobs', concurrency=1, budget_usd=.01, remote=processor)
    limits = ProcessingLimits(max_bytes=30_000_000, max_pages=120, total_seconds=120,
                              operation_seconds=30, max_output_bytes=1_000_000, max_attempts=1, budget_usd=.01)
    job = service.enqueue('product-completion', content, mode='solari', limits=limits)
    (root/'attempt.json').write_text(json.dumps({'job_id':job['id'],'source_run':source_run.run_id}), encoding='utf-8')
    result = service.execute(job['id'], 'product-completion')
    report = {'state':result['state'], 'source_run':source_run.run_id,
              'document_sha256':source_run.artifact.sha256, 'job':result, 'events':events,
              'budget':budget.snapshot(), 'confirmed_billed_usd':None}
    if result['state'] == 'succeeded':
        output = service.result(job['id'], 'product-completion')
        report['local_pages'] = len(local_pages)
        report['remote_pages'] = output['total_pages']
        report['all_page_text_matches_local'] = [p.text for p in local_pages] == [p['text'] for p in output['pages']]
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('job','budget')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
