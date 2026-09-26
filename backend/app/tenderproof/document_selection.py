"""Re-extract a preserved principal document without rewriting its original run."""
import hashlib
import json
import time
from dataclasses import replace
from datetime import datetime, timezone
from fastapi import HTTPException
from app.tenderproof import review_cases as review
from app.tenderproof.contracts import Artifact, DocumentCandidate, FieldState
from app.tenderproof.fields import extract_fields, semantic_hash, METHOD_VERSION
from app.tenderproof.processing import extract_pages_isolated
from app.tenderproof.security import TenderProofSettings
from app.tenderproof.validation import validate_identity
from app.tenderproof.compare import compare
from app.tenderproof.supplementary_fields import supplement_fields


def select_preserved(queue, store, run, case_id, revision_hash, artifact_id, reason):
    if run.execution_status != 'completed' or not run.artifact or not run.document:
        raise HTTPException(409, 'Conclua a extração atual antes de selecionar outro edital')
    case = review.read(queue, case_id, run.owner_user_id)
    if (case['run_id'] != run.run_id or case['revision_hash'] != revision_hash
            or case['approved_at'] is not None or len(reason.strip()) < 20):
        raise HTTPException(409, 'Seleção exige revisão pendente correspondente e justificativa')
    with queue._db() as db:
        if review.revision(queue, run, db) != case['revision']:
            raise HTTPException(409, 'A coleta mudou; atualize a preparação')
    matches = [d for d in case['documents'] if d['artifact']['artifact_id'] == artifact_id]
    if len(matches) != 1 or matches[0]['document']['kind'] not in ('edital', 'consolidado'):
        raise HTTPException(422, 'Selecione um edital ou consolidado preservado nesta revisão')
    selected = matches[0]
    if selected['artifact']['sha256'] == run.artifact.sha256:
        raise HTTPException(422, 'Este documento já é utilizado na extração atual')
    operation = review.digest({'owner':run.owner_user_id, 'run_id':run.run_id, 'case_id':case_id,
        'revision_hash':revision_hash, 'artifact_id':artifact_id, 'reason':reason.strip()})
    config = queue.configuration(run.owner_user_id, run.source)
    if not config:
        raise HTTPException(409, 'Configure os limites da fonte antes de reprocessar')
    settings = TenderProofSettings.from_env()
    settings = replace(settings, limits=replace(settings.limits,
        max_pages=config['policy']['max_pdf_pages'], max_download_bytes=config['policy']['max_download_bytes']))
    candidate = next(c for c in run.candidates if c.candidate_id == run.selected_candidate_id)
    documents, extracted = [], {}
    for item in case['documents']:
        artifact = Artifact.model_validate(item['artifact'])
        content = store.load_artifact_bytes(artifact)
        if (not content or len(content) != artifact.byte_len or len(content) > settings.limits.max_download_bytes
                or hashlib.sha256(content).hexdigest() != artifact.sha256):
            raise HTTPException(409, 'Documento preservado ausente ou divergente; prepare novamente')
        pages, total, processed, truncated, errors = extract_pages_isolated(content,
            artifact_id=artifact.artifact_id, owner_id=str(run.owner_user_id),
            max_bytes=settings.limits.max_download_bytes, max_pages=settings.limits.max_pages)
        if truncated or errors or total != processed or not pages:
            raise HTTPException(409, 'Extração integral do documento ainda está pendente')
        fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
        extracted[artifact.artifact_id] = (fields, pages)
        documents.append({**item, 'pages':[{'page_number':p.page_number, 'text':p.text} for p in pages],
                          'fields':[f.model_dump(mode='json') for f in fields]})
    original = next((d for d in documents if d['artifact']['sha256'] == run.artifact.sha256), None)
    if original is None:
        raise HTTPException(409, 'Edital original ausente da revisão')
    fields, pages = extracted[artifact_id]
    old_fields = {f.field_name:f for f in extracted[original['artifact']['artifact_id']][0]}
    new_fields = {f.field_name:f for f in fields}
    for name in ('orgao', 'edital_numero'):
        old, new = old_fields.get(name), new_fields.get(name)
        if not old or not new or old.state != FieldState.SUPPORTED or new.state != FieldState.SUPPORTED or old.value != new.value:
            raise HTTPException(409, 'Órgão e número do edital precisam coincidir com evidências')
    artifact = Artifact.model_validate(selected['artifact'])
    manifest = selected['document']
    document = DocumentCandidate(doc_id='review-'+artifact_id, title=manifest['title'], kind=manifest['kind'],
        url_requested=manifest['url'], url_final=artifact.url_final,
        acquisition_request=manifest.get('acquisition_request'), reason_chosen=reason.strip())
    validation = validate_identity(candidate=candidate, pages=pages, document_title=document.title,
        document_url=artifact.url_final, document_kind=document.kind)
    if validation.errors:
        raise HTTPException(409, 'O documento selecionado não passou na validação de identidade')
    fields = supplement_fields(candidate, fields, run.supplementary_documents, store, settings, run.owner_user_id)
    now = datetime.now(timezone.utc)
    result = run.model_copy(deep=True, update={'run_id':'tp-review-'+operation,
        'document':document, 'artifact':artifact, 'fields':fields, 'total_pages':len(pages),
        'processed_pages':len(pages), 'truncated':False, 'page_errors':[], 'error':None,
        'validation':validation, 'validation_status':validation.status, 'semantic_hash':semantic_hash(fields),
        'created_at':now, 'updated_at':now, 'comparison_status':'compared',
        'document_selection':{'parent_run_id':run.run_id, 'case_id':case_id, 'reason':reason.strip(),
                              'selected_artifact_id':artifact_id, 'selected_at':now.isoformat()}})
    result.comparison = compare(baseline={f.field_name:f.value for f in run.fields if f.state == FieldState.SUPPORTED},
        baseline_collected_at=run.updated_at, baseline_origin='Extração anterior preservada: '+run.run_id, fields=fields)
    with queue._db() as db:
        if review.revision(queue, run, db) != case['revision']:
            raise HTTPException(409, 'A coleta mudou durante o processamento; atualize a revisão')
        baseline = review.revision(queue, result, db)
    new_id = 'drc-'+operation
    payload = {'revision':baseline, 'revision_hash':review.digest(baseline), 'documents':documents,
        'identity':list(review.identity(result)), 'selected_document_sha256':artifact.sha256,
        'created_at':time.time(), 'extraction_method_version':METHOD_VERSION}
    result = store.put_run_if_absent(result)
    with queue._db(write=True) as db:
        if review.revision(queue, result, db) != baseline:
            raise HTTPException(409, 'A coleta mudou; a nova extração permanece sem aprovação')
        review._schema(db)
        db.execute('INSERT OR IGNORE INTO document_effect_cases VALUES (?,?,?,?,NULL,NULL)',
            (new_id,result.owner_user_id,result.run_id,json.dumps(payload,ensure_ascii=False)))
    return result
