"""Prepare reviewed certification/paid-registration dates from preserved PDFs."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from app.database import SessionLocal
from app.tenderproof.acquisition import new_run_id
from app.tenderproof.contracts import ComparisonResult, ExecutionStatus
from app.tenderproof.fields import extract_fields, semantic_hash
from app.tenderproof.processing import extract_pages_isolated
from app.tenderproof.store import get_store
from app.tenderproof.validation import validate_identity
from delivery_next_reextract_six_2026 import AUTHORIZATION, proposal, evidence_fields

TARGETS = {
    'exame_open': ('tp-tcj-3b045d3d0afd521c8c921b26af614c65-1', '2026-07-22T09:00:00-03:00', '2026-07-24T23:59:00-03:00', '2026-08-23T08:00:00-03:00'),
    'cotec_open': ('tp-tcj-3b345fb2c6ac57ba83731ab67cd7af45-1', '2026-09-10T08:00:00-03:00', '2026-10-07T17:00:00-03:00', '2026-12-13'),
}

def main(targets=TARGETS, output='delivery-exame-cotec-proposed-20260909.json'):
    store = get_store()
    prepared, proofs = [], {}
    for source, (parent, start, end, exam) in targets.items():
        original = store.get_run(parent)
        assert original and original.artifact and original.document
        content = store.load_artifact_bytes(original.artifact)
        assert hashlib.sha256(content).hexdigest() == original.artifact.sha256
        pages, total, processed, truncated, errors = extract_pages_isolated(content,
            artifact_id=original.artifact.artifact_id, owner_id=str(original.owner_user_id),
            max_bytes=max(len(content), 30*1024*1024), max_pages=200, reuse_completed=True)
        assert not truncated and not errors and total == processed
        candidate = next(c for c in original.candidates if c.candidate_id == original.selected_candidate_id)
        validation = validate_identity(candidate=candidate, pages=pages, document_title=original.document.title,
            document_url=original.artifact.url_final, document_kind=original.document.kind)
        assert validation.status.value == 'valid'
        fields = extract_fields(candidate=candidate, artifact=original.artifact, pages=pages)
        observed = {field.field_name: field.value for field in fields}
        assert (observed['inscricao_inicio'], observed['inscricao_fim'], observed['prova_data']) == (start, end, exam), observed
        now = datetime.now(timezone.utc)
        run = original.model_copy(deep=True, update={'run_id': new_run_id(), 'fields': fields,
            'execution_status': ExecutionStatus.COMPLETED, 'validation_status': validation.status, 'validation': validation,
            'comparison_status': 'pending', 'comparison': ComparisonResult(), 'semantic_hash': semantic_hash(fields),
            'total_pages': total, 'processed_pages': processed, 'truncated': False, 'page_errors': [],
            'created_at': now, 'updated_at': now, 'diagnostics': [*original.diagnostics, 'reextract_of='+parent]})
        store.put_run(run)
        with SessionLocal() as db:
            prepared.append(proposal(db, run, store))
        proofs[source] = {'run_id': run.run_id, 'artifact_sha256': run.artifact.sha256, 'fields': evidence_fields(run)}
    assert Path(output).name == output
    path = Path('/var/lib/observador/tenderproof/product-completion') / output
    path.write_text(json.dumps({'authorization': AUTHORIZATION, 'proposals': prepared, 'runs': proofs}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'receipt': str(path), 'proposals': prepared}, ensure_ascii=False))

if __name__ == '__main__':
    main()
