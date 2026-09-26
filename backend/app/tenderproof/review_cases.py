"""Document effect reviews bound to preserved bytes and a precise queue revision."""
import hashlib
import json
import re
import time
import uuid
import httpx
from urllib.parse import urlsplit
from datetime import datetime, timezone
from dataclasses import replace
from pydantic import ValidationError

from fastapi import HTTPException
from app.tenderproof.contracts import Artifact, FieldState
from app.tenderproof.continuous_store import candidate_key
from app.tenderproof.document_identity import document_manifest, document_identity
from app.tenderproof.http_driver import BoundedHTTPDriver
from app.tenderproof.processing import extract_pages_isolated, ProcessingError
from app.tenderproof.security import TenderProofSettings
from app.tenderproof.fields import extract_fields, METHOD_VERSION
from app.tenderproof.selection_scope import document_scope
from app.tenderproof.validation import validate_identity, title_is_corroborated


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _review_value(value):
    """Accept JSON field values, including structured cargo rows."""
    if isinstance(value, (str, int, float, type(None), bool, list, dict)):
        try:
            json.dumps(value, ensure_ascii=False)
            return True
        except (TypeError, ValueError):
            return False
    return False


def review_fields(candidate, artifact, pages, document=None):
    # The APTA amendment is a separate one-page documentary artifact. Keep
    # the principal 20-page parser strict and do not promote amendment fields.
    if (candidate.source == 'apta_open' and candidate.external_id == '708'
            and (document or {}).get('kind') == 'retificacao'):
        from app.tenderproof.apta_aragarcas_parser import validate_retification
        validate_retification(artifact, pages, source=candidate.source,
                              external_id=candidate.external_id, document=document or {})
        return []
    if (candidate.source == 'klc_open' and candidate.external_id == '632'
            and (document or {}).get('kind') == 'retificacao'):
        from pathlib import Path
        from app.tenderproof.store import artifact_dir
        from app.tenderproof.klc_retificacao_t012 import dispatch as dispatch_klc_ret
        stored = Path(artifact.storage_path or '')
        if not stored.is_absolute():
            stored = artifact_dir() / stored.name
        parsed = dispatch_klc_ret(candidate=candidate, artifact=artifact, pages=pages,
                                  content=stored.read_bytes(), document=document or {})
        return [field.model_dump(mode='json') for field in parsed]
    # OCR reading order can interleave unrelated acts in multi-column gazettes.
    # Keep recognized pages available to reviewers without treating them as
    # native-text evidence or claiming their unextracted fields are unpublished.
    fields = extract_fields(candidate=candidate, artifact=artifact,
                            pages=[p for p in pages if p.extraction_method == 'pdf_text'],
                            document=document)
    if any(p.extraction_method == 'ocr_tesseract' for p in pages):
        for field in fields:
            if field.state == FieldState.UNKNOWN:
                field.state = FieldState.FAILED
                field.reason = 'Extração de campos das páginas digitalizadas pendente; confira o OCR e o PDF oficial.'
    return [f.model_dump(mode='json') for f in fields]


def identity(run):
    candidate = next(c for c in run.candidates if c.candidate_id == run.selected_candidate_id)
    return (run.owner_user_id, run.source, run.mode, candidate_key(candidate))


def revision(queue, run, db):
    row = db.execute('SELECT manifest,pending_documents FROM document_review_state WHERE owner=? AND source=? AND mode=? AND candidate_key=?', identity(run)).fetchone()
    if not row:
        raise HTTPException(409, 'Coleta documental completa necessária antes da revisão')
    result = {'manifest':json.loads(row['manifest']), 'pending':json.loads(row['pending_documents']),
              'artifact_sha256':run.artifact.sha256 if run.artifact else None}
    if run.supplementary_documents:
        result['supplementary_documents'] = [
            {'document':document_manifest(extra.document),'sha256':extra.artifact.sha256}
            for extra in run.supplementary_documents]
    return result


def _schema(db):
    db.execute('CREATE TABLE IF NOT EXISTS document_effect_cases (id TEXT PRIMARY KEY, owner INTEGER NOT NULL, run_id TEXT NOT NULL, payload TEXT NOT NULL, approved_at REAL, decisions TEXT)')


def outdated_approval(run, db):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='document_effect_cases'").fetchone():
        return None
    for row in db.execute('SELECT payload FROM document_effect_cases WHERE owner=? AND approved_at IS NOT NULL ORDER BY approved_at DESC, rowid DESC', (run.owner_user_id,)):
        payload = json.loads(row['payload'])
        if payload['identity'] == list(identity(run)) and run.artifact and payload['selected_document_sha256'] == run.artifact.sha256:
            return payload if payload.get('extraction_method_version') != METHOD_VERSION else None
    return None


def prepare(queue, store, run, *, driver_factory=BoundedHTTPDriver):
    if run.execution_status != 'completed' or not run.artifact or not run.document:
        raise HTTPException(409, 'Conclua a aquisição e extração do edital antes de revisar seus efeitos')
    with queue._db() as db:
        baseline = revision(queue, run, db)
        outdated = outdated_approval(run, db)
    if not baseline['pending'] and not outdated:
        raise HTTPException(409, 'Não há pendências documentais para esta observação')
    candidate = next(c for c in run.candidates if c.candidate_id == run.selected_candidate_id)
    # A prepared case is already a source/identity-bound review of preserved
    # bytes.  It remains replayable when the live listing later drops a
    # pending amendment; verify every blob/hash and URL host before returning
    # it, so this cannot become an arbitrary-URL bypass.
    existing = current(queue, run)
    if existing and existing.get('documents'):
        allowed_hosts = {urlsplit(candidate.detail_url_observed).netloc,
                         urlsplit(run.artifact.url_final or run.artifact.url_requested).netloc}
        preserved = existing.get('identity') == list(identity(run))
        try:
            expected = sorted(repr(document_identity(document)) for document in baseline['pending'])
            actual = sorted(repr(document_identity(item['document'])) for item in existing['documents'])
            # Compare the complete canonical multiset: no missing, extra, or
            # duplicate document may be replayed from a persisted case.
            preserved = preserved and actual == expected
            for item in existing['documents']:
                document_url = item.get('document', {}).get('url')
                artifact = Artifact.model_validate(item['artifact'])
                if (not document_url
                        or urlsplit(document_url).netloc not in allowed_hosts
                        or document_url not in {artifact.url_requested, artifact.url_final}):
                    preserved = False
                    break
                content = store.load_artifact_bytes(artifact)
                if (not content or len(content) != artifact.byte_len
                        or hashlib.sha256(content).hexdigest() != artifact.sha256):
                    preserved = False
                    break
        except (KeyError, TypeError, ValueError, ValidationError):
            preserved = False
        if preserved:
            return existing
    configuration=queue.configuration(run.owner_user_id,run.source)
    if not configuration:
        raise HTTPException(409,'Configure os limites da fonte antes de preparar os documentos')
    policy=configuration['policy']
    settings=TenderProofSettings.from_env()
    settings=replace(settings,limits=replace(settings.limits,max_pages=policy['max_pdf_pages'],
        max_download_bytes=policy['max_download_bytes'],max_documents=policy['max_documents'],
        max_navigations=4*(policy['max_documents']+4),total_timeout_s=policy['job_timeout_s']))
    if len(baseline['manifest'])>settings.limits.max_documents:
        raise HTTPException(409,'Manifesto excede os limites configurados; amplie a cobertura antes da revisão')
    driver = driver_factory(run.source,settings)
    from app.tenderproof.service import _ExecutionLease, TenderProofBusy
    try:
        lease = _ExecutionLease(store, driver, wait_s=30)
    except TenderProofBusy as exc:
        raise HTTPException(409, 'Outra coleta ou conferência está em andamento. Aguarde sua conclusão antes de preparar os documentos.') from exc
    documents = []
    try:
        bind_candidate=getattr(driver,'set_candidate',None)
        if callable(bind_candidate):
            bind_candidate(candidate)
        html = driver.open_detail(candidate.detail_url_observed)
        driver.adapter.confirm_identity(candidate, html, candidate.detail_url_observed)
        observed = driver.adapter.documents(html, candidate)
        expected = {document_identity(d) for d in baseline['manifest']}
        if {document_identity(document_manifest(d)) for d in observed} != expected:
            raise HTTPException(409, 'A lista oficial mudou. Execute nova coleta antes da revisão')
        wanted = {document_identity(d) for d in baseline['pending']}
        if outdated:
            wanted.update(document_identity(d) for d in baseline['manifest'])
        wanted.add(document_identity(document_manifest(run.document)))
        supplementary_hashes = {document_identity(document_manifest(extra.document)):extra.artifact.sha256
                                for extra in run.supplementary_documents}
        wanted.update(supplementary_hashes)
        for document in observed:
            lease.check()
            if document_identity(document_manifest(document)) not in wanted:
                continue
            if documents:
                time.sleep(policy['min_request_gap_s'])
            download = (driver.download_document(document,candidate,max_bytes=driver.settings.limits.max_download_bytes)
                        if document.acquisition_request else driver.download(document.url_requested,max_bytes=driver.settings.limits.max_download_bytes))
            artifact = Artifact(artifact_id='review-'+uuid.uuid4().hex,sha256=download.sha256,byte_len=len(download.content),
                url_requested=download.url_requested,url_final=download.url_final,downloaded_at=datetime.now(timezone.utc))
            store.save_artifact_file(artifact,download.content)
            if document_identity(document_manifest(document)) == document_identity(document_manifest(run.document)) and artifact.sha256 != run.artifact.sha256:
                raise HTTPException(409,'Os bytes do edital mudaram. Recolha e extraia novamente')
            expected_extra = supplementary_hashes.get(document_identity(document_manifest(document)))
            if expected_extra is not None and artifact.sha256 != expected_extra:
                raise HTTPException(409,'Os bytes do anexo mudaram. Recolha e extraia novamente')
            pages,total,processed,truncated,errors = extract_pages_isolated(download.content,artifact_id=artifact.artifact_id,
                owner_id=str(run.owner_user_id),max_bytes=driver.settings.limits.max_download_bytes,max_pages=settings.limits.max_pages,
                capacity_wait_s=15,reuse_completed=True)
            if pages and any(len(''.join(p.text.split())) < 40 for p in pages):
                lease.check()
                pages,total,processed,truncated,errors = extract_pages_isolated(download.content,
                    artifact_id=artifact.artifact_id, owner_id=str(run.owner_user_id),
                    max_bytes=driver.settings.limits.max_download_bytes,max_pages=settings.limits.max_pages,
                    capacity_wait_s=15,operation='ocr_pdf',ocr_timeout_s=settings.limits.total_timeout_s,reuse_completed=True)
            if truncated or errors or total != processed or not pages:
                raise HTTPException(409,'Documento preservado, mas sua extração ainda exige tratamento')
            documents.append({'document':document_manifest(document),'artifact':artifact.model_dump(mode='json'),
                              'pages':[p.model_dump(mode='json') for p in pages],
                              'ocr_review_required':any(p.extraction_method == 'ocr_tesseract' for p in pages),
                              'scope':document_scope(run.source, artifact, pages),
                              'fields':review_fields(candidate, artifact, pages,
                                                      document=document_manifest(document))})
        if {document_identity(d['document']) for d in documents} != wanted:
            raise HTTPException(409,'Documento pendente não está mais disponível na lista oficial')
        lease.check()
    except TenderProofBusy as exc:
        raise HTTPException(409, 'A coordenação da conferência foi perdida. Documentos preservados; prepare novamente antes de aprovar.') from exc
    except (TimeoutError, httpx.TimeoutException) as exc:
        raise HTTPException(409, 'O prazo desta preparação terminou. Prepare novamente para retomar: processamentos concluídos serão reutilizados se os bytes oficiais e os limites continuarem iguais. Nenhuma revisão foi aprovada.') from exc
    except ProcessingError as exc:
        if str(exc) == 'concurrency_limit':
            raise HTTPException(409, 'Processamento ocupado. Aguarde a coleta em andamento e prepare a conferência novamente; documentos já preservados não foram apagados.') from exc
        raise HTTPException(409, 'Documento preservado, mas o processamento isolado exige tratamento; nenhuma revisão foi aprovada.') from exc
    except ValueError as exc:
        raise HTTPException(409, 'Documento preservado falhou na validação específica; nenhuma revisão foi aprovada.') from exc
    finally:
        try:
            driver.close()
        finally:
            lease.release()
    payload={'revision':baseline,'revision_hash':digest(baseline),'documents':documents,'identity':list(identity(run)),
             'selected_document_sha256':run.artifact.sha256,'created_at':time.time(),
             'extraction_method_version':METHOD_VERSION}
    case_id='drc-'+uuid.uuid4().hex
    with queue._db(write=True) as db:
        if revision(queue,run,db) != baseline:
            raise HTTPException(409,'A coleta mudou durante a preparação. Atualize a revisão')
        _schema(db)
        db.execute('INSERT INTO document_effect_cases VALUES (?,?,?,?,NULL,NULL)',(case_id,run.owner_user_id,run.run_id,json.dumps(payload,ensure_ascii=False)))
    return {'id':case_id,**payload,'approved_at':None}


def prepare_preserved(queue, store, run, *, document, artifact, expected_page_count):
    """Create a review case from one already-preserved local artifact.

    This is the authenticated recovery path when an official listing drops a
    pending document after acquisition.  It deliberately accepts no URL
    fetch: the blob must already be registered in the TenderProof store.
    """
    if run.execution_status != 'completed' or not run.artifact or not run.document:
        raise HTTPException(409, 'Conclua a aquisição e extração do edital antes de revisar seus efeitos')
    if artifact.content_type is None or artifact.content_type.split(';')[0].strip().lower() != 'application/pdf':
        raise HTTPException(422, 'A revisão preservada exige um artefato PDF')
    with queue._db() as db:
        baseline = revision(queue, run, db)
    existing = current(queue, run)
    if existing:
        same = (existing.get('identity') == list(identity(run))
                and len(existing.get('documents', [])) == 1
                and existing['documents'][0].get('document')
                and document_identity(existing['documents'][0]['document']) == document_identity(document)
                and existing['documents'][0].get('artifact', {}).get('sha256') == artifact.sha256)
        if same:
            preserved = Artifact.model_validate(existing['documents'][0]['artifact'])
            if store.load_artifact_bytes(preserved) is not None:
                return existing
        raise HTTPException(409, 'Já existe uma revisão preservada diferente para esta pendência')
    matches = [item for item in baseline['pending'] if document_identity(item) == document_identity(document)]
    if len(matches) != 1:
        raise HTTPException(409, 'Documento não corresponde exatamente ao manifesto pendente')
    pending_document = matches[0]
    pending_url = pending_document['url']
    if artifact.url_requested != pending_url or artifact.url_final != pending_url:
        raise HTTPException(409, 'URL do artefato não corresponde ao documento pendente')
    candidate = next(c for c in run.candidates if c.candidate_id == run.selected_candidate_id)
    allowed_hosts = {urlsplit(candidate.detail_url_observed).netloc,
                     urlsplit(run.artifact.url_final or run.artifact.url_requested).netloc}
    if urlsplit(pending_url).netloc not in allowed_hosts:
        raise HTTPException(409, 'Host do documento não pertence à observação')
    content = store.load_artifact_bytes(artifact)
    if content is None or len(content) != artifact.byte_len or hashlib.sha256(content).hexdigest() != artifact.sha256:
        raise HTTPException(409, 'Artefato preservado ausente ou divergente')
    configuration = queue.configuration(run.owner_user_id, run.source)
    if not configuration:
        raise HTTPException(409, 'Configure os limites da fonte antes de preparar os documentos')
    policy = configuration['policy']
    settings = TenderProofSettings.from_env()
    settings = replace(settings, limits=replace(settings.limits,
        max_pages=policy['max_pdf_pages'], max_download_bytes=policy['max_download_bytes']))
    if expected_page_count > settings.limits.max_pages:
        raise HTTPException(409, 'Quantidade de páginas excede o limite configurado')
    main_content = store.load_artifact_bytes(run.artifact)
    if (main_content is None or len(main_content) != run.artifact.byte_len
            or hashlib.sha256(main_content).hexdigest() != run.artifact.sha256):
        raise HTTPException(409, 'Artefato principal preservado ausente ou divergente')
    main_pages, main_total, main_processed, main_truncated, main_errors = extract_pages_isolated(
        main_content, artifact_id=run.artifact.artifact_id, owner_id=str(run.owner_user_id),
        max_bytes=settings.limits.max_download_bytes, max_pages=settings.limits.max_pages,
        reuse_completed=True)
    if (main_truncated or main_errors or main_total != main_processed or not main_pages
            or any(page.artifact_id != run.artifact.artifact_id or page.error or page.truncated for page in main_pages)):
        raise HTTPException(409, 'Extração do edital principal incompleta ou divergente')
    main_validation = validate_identity(candidate=candidate, pages=main_pages,
        document_title=run.document.title, document_url=run.artifact.url_final,
        document_kind=run.document.kind)
    if main_validation.errors:
        raise HTTPException(409, 'Edital principal não passou na revalidação de identidade')
    pages, total, processed, truncated, errors = extract_pages_isolated(
        content, artifact_id=artifact.artifact_id, owner_id=str(run.owner_user_id),
        max_bytes=settings.limits.max_download_bytes, max_pages=settings.limits.max_pages,
        reuse_completed=True)
    if (truncated or errors or total != processed or total != expected_page_count or len(pages) != expected_page_count or not pages
            or any(page.artifact_id != artifact.artifact_id or page.error or page.truncated for page in pages)):
        raise HTTPException(409, 'Extração preservada incompleta ou divergente')
    text = '\n'.join(page.text for page in pages)
    if (pending_document.get('kind') in ('retificacao', 'prorrogacao')
            and not re.search(r'retifica|prorrog', text, re.IGNORECASE)):
        raise HTTPException(409, 'Documento retificador não comprovado no texto preservado')
    try:
        amendment_validation = validate_identity(candidate=candidate, pages=pages,
            document_title=candidate.title_observed, document_url=pending_url, document_kind='edital')
        identity_error = bool(amendment_validation.errors)
    except (KeyError, ValueError):
        # Some source-specific targeted parsers intentionally have no generic
        # adapter.  Their bounded textual identity still requires the
        # candidate title and the principal edital number to be present.
        identity_error = False
    edital_numbers = re.findall(r'\b\d{2,4}/\d{4}\b', run.document.title or '')
    if (identity_error or not title_is_corroborated(candidate.title_observed, text)
            or any(number not in text for number in edital_numbers)):
        raise HTTPException(409, 'Documento preservado não corresponde ao candidato da observação')
    try:
        reviewed_fields = review_fields(candidate, artifact, pages, document=pending_document)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(409, 'Documento preservado falhou na validação específica; nenhuma revisão foi aprovada.') from exc
    payload = {'revision': baseline, 'revision_hash': digest(baseline),
               'documents': [{'document': pending_document, 'artifact': artifact.model_dump(mode='json'),
                              'pages': [page.model_dump(mode='json') for page in pages],
                              'ocr_review_required': any(page.extraction_method == 'ocr_tesseract' for page in pages),
                              'scope': document_scope(run.source, artifact, pages),
                              'fields': reviewed_fields}],
               'identity': list(identity(run)), 'selected_document_sha256': run.artifact.sha256,
               'created_at': run.updated_at.isoformat(), 'extraction_method_version': METHOD_VERSION}
    operation = digest({'identity': payload['identity'], 'run_id': run.run_id,
                        'revision_hash': payload['revision_hash'], 'artifact_sha256': artifact.sha256,
                        'document': pending_document, 'method': METHOD_VERSION,
                        'expected_page_count': expected_page_count})
    case_id = 'drc-preserved-' + operation[:32]
    with queue._db(write=True) as db:
        if revision(queue, run, db) != baseline:
            raise HTTPException(409, 'A coleta mudou durante a preparação; tente novamente')
        _schema(db)
        db.execute('INSERT OR IGNORE INTO document_effect_cases VALUES (?,?,?,?,NULL,NULL)',
                   (case_id, run.owner_user_id, run.run_id, json.dumps(payload, ensure_ascii=False)))
        row = db.execute('SELECT payload FROM document_effect_cases WHERE id=? AND owner=? AND run_id=?',
                         (case_id, run.owner_user_id, run.run_id)).fetchone()
    if not row:
        raise HTTPException(409, 'Não foi possível persistir a revisão preservada')
    stored_payload = json.loads(row['payload'])
    if json.dumps(stored_payload, sort_keys=True, ensure_ascii=False, separators=(',', ':')) != \
            json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',', ':')):
        raise HTTPException(409, 'Conflito na revisão preservada; nenhuma decisão foi reaproveitada')
    return {'id': case_id, **stored_payload, 'approved_at': None}


def current(queue, run):
    """Return a prepared, unapproved case for this exact live revision."""
    with queue._db() as db:
        exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='document_effect_cases'").fetchone()
        if not exists:
            return None
        rows=db.execute('SELECT id,payload FROM document_effect_cases WHERE owner=? AND run_id=? AND approved_at IS NULL ORDER BY rowid DESC',
                        (run.owner_user_id,run.run_id)).fetchall()
        if not rows:
            return None
        baseline=revision(queue,run,db)
        for row in rows:
            payload=json.loads(row['payload'])
            if payload['revision']==baseline and payload.get('extraction_method_version') == METHOD_VERSION:
                return {'id':row['id'],**payload,'approved_at':None}
    return None


def read(queue, case_id, owner):
    with queue._db() as db:
        exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='document_effect_cases'").fetchone()
        row=db.execute('SELECT * FROM document_effect_cases WHERE id=? AND owner=?',(case_id,owner)).fetchone() if exists else None
    if not row:
        raise HTTPException(404,'Revisão não encontrada')
    return {'id':row['id'],'run_id':row['run_id'],**json.loads(row['payload']),'approved_at':row['approved_at'],
            'decisions':json.loads(row['decisions']) if row['decisions'] else None}


def approve(queue,store,run,case_id,review_hash,decisions):
    from app.tenderproof.ocr_regions import decision_text
    case=read(queue,case_id,run.owner_user_id)
    if case['run_id'] != run.run_id or review_hash != case['revision_hash']:
        raise HTTPException(409,'Revisão não corresponde à observação e aos documentos apresentados')
    if case.get('extraction_method_version') != METHOD_VERSION:
        raise HTTPException(409,'A interpretação dos campos foi atualizada. Prepare e confira os documentos novamente antes de aprovar.')
    expected={d['artifact']['sha256'] for d in case['documents']}
    if len(decisions)!=len(expected) or {d['sha256'] for d in decisions}!=expected:
        raise HTTPException(422,'Confira e explique o efeito de cada documento')
    by_hash={d['sha256']:d for d in decisions}
    for document in case['documents']:
        artifact=Artifact.model_validate(document['artifact'])
        content=store.load_artifact_bytes(artifact)
        if content is None or hashlib.sha256(content).hexdigest()!=artifact.sha256:
            raise HTTPException(409,'Evidência preservada ausente ou divergente')
        decision=by_hash[artifact.sha256]
        page=next((p for p in document['pages'] if p['page_number']==decision['page']),None)
        if (decision['effect'] not in ('reflected_in_selected_document','no_field_change','field_changes') or len(decision['reason'].strip())<20
                or len(decision['snippet'].strip())<20 or not page
                or decision['snippet'] not in decision_text(case,document,page,decision)):
            raise HTTPException(422,'Informe efeito, justificativa e trecho literal da página de cada documento')
        if decision['effect'] == 'field_changes':
            changes = decision.get('changes')
            if not isinstance(changes, list) or not changes:
                raise HTTPException(422,'Informe explicitamente os campos alterados na retificação')
            names = [item.get('field_name') for item in changes if isinstance(item, dict)]
            if (len(names) != len(changes) or len(set(names)) != len(names) or any(not name for name in names)
                    or any(not _review_value(item.get('previous'))
                           or not _review_value(item.get('new'))
                           or not item.get('provenance') for item in changes)):
                raise HTTPException(422,'Campos alterados da retificação inválidos ou repetidos')
    with queue._db(write=True) as db:
        row=db.execute('SELECT approved_at,decisions FROM document_effect_cases WHERE id=? AND owner=?',(case_id,run.owner_user_id)).fetchone()
        if row['approved_at'] is not None:
            if json.loads(row['decisions'])!=decisions:
                raise HTTPException(409,'Esta revisão já possui outra decisão registrada')
            return {'id':case_id,'approved_at':row['approved_at']}
        if revision(queue,run,db)!=case['revision']:
            raise HTTPException(409,'Documentos ou bytes alterados; prepare nova revisão')
        approved=time.time()
        db.execute('UPDATE document_effect_cases SET approved_at=?,decisions=? WHERE id=?',(approved,json.dumps(decisions,ensure_ascii=False),case_id))
        # A field-changing notice remains pending until the corresponding
        # canonical amendment is applied.  Clearing it here would allow a
        # reviewer to mark evidence as resolved without changing the catalog.
        if not any(d.get('effect') == 'field_changes' for d in decisions):
            db.execute("UPDATE document_review_state SET pending_documents='[]',detected_at=NULL WHERE owner=? AND source=? AND mode=? AND candidate_key=?",identity(run))
    return {'id':case_id,'approved_at':approved}


def save_draft(queue, run, case_id, review_hash, draft_revision, decisions):
    from app.tenderproof.ocr_regions import decision_text
    case = read(queue, case_id, run.owner_user_id)
    if case['run_id'] != run.run_id or case['revision_hash'] != review_hash:
        raise HTTPException(409, 'Rascunho não corresponde à revisão apresentada')
    by_hash = {d['artifact']['sha256']:d for d in case['documents']}
    if len({d['sha256'] for d in decisions}) != len(decisions):
        raise HTTPException(422, 'Documento repetido no rascunho')
    for decision in decisions:
        doc = by_hash.get(decision['sha256'])
        if not doc or (decision.get('page') is not None and not any(p['page_number']==decision['page'] for p in doc['pages'])):
            raise HTTPException(422, 'Documento ou página não pertence à conferência')
        if decision.get('region_id'):
            page = next((p for p in doc['pages'] if p['page_number']==decision.get('page')),None)
            if not page:
                raise HTTPException(422, 'Região OCR exige a página da decisão')
            decision_text(case,doc,page,decision)
    with queue._db(write=True) as db:
        row = db.execute('SELECT payload,approved_at FROM document_effect_cases WHERE id=? AND owner=?', (case_id,run.owner_user_id)).fetchone()
        payload = json.loads(row['payload'])
        if row['approved_at'] is not None or payload.get('extraction_method_version') != METHOD_VERSION or revision(queue,run,db) != payload['revision']:
            raise HTTPException(409, 'A revisão mudou ou foi aprovada; o rascunho não foi alterado')
        if payload.get('draft_revision',0) != draft_revision:
            raise HTTPException(409, 'Existe um rascunho mais recente. Reabra a conferência antes de salvar; suas alterações locais não foram enviadas.')
        saved_at = time.time()
        payload.update(draft=decisions, draft_revision=draft_revision+1, draft_saved_at=saved_at)
        db.execute('UPDATE document_effect_cases SET payload=? WHERE id=? AND owner=?', (json.dumps(payload,ensure_ascii=False),case_id,run.owner_user_id))
    return {'draft_revision':draft_revision+1, 'draft_saved_at':saved_at}


def approved_case(queue,run,db,*,allow_field_changes=False):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='document_effect_cases'").fetchone():
        return None
    current=revision(queue,run,db)
    if current['pending'] and not allow_field_changes:
        return None
    for row in db.execute('SELECT id,payload,decisions FROM document_effect_cases WHERE owner=? AND approved_at IS NOT NULL ORDER BY approved_at DESC',(run.owner_user_id,)):
        payload=json.loads(row['payload'])
        if (payload.get('extraction_method_version') == METHOD_VERSION
                and payload['identity']==list(identity(run)) and payload['revision']['manifest']==current['manifest']
                and payload['selected_document_sha256']==current['artifact_sha256']
                and payload['revision'].get('supplementary_documents',[])==current.get('supplementary_documents',[])):
            if current['pending'] and allow_field_changes:
                decisions = json.loads(row['decisions'] or '[]')
                if not any(item.get('effect') == 'field_changes' for item in decisions if isinstance(item, dict)):
                    continue
            return row['id']
    return None


def finalize_field_changes(queue, run, case_id, fields, *, db=None):
    """Clear a field-change review only after canonical application succeeded."""
    def finalize(connection):
        nonlocal db
        db = connection
        row = db.execute('SELECT payload,approved_at,decisions FROM document_effect_cases WHERE id=? AND owner=?',
                         (case_id, run.owner_user_id)).fetchone()
        if not row or row['approved_at'] is None:
            raise HTTPException(409, 'Retificação: revisão documental não está aprovada')
        decisions = json.loads(row['decisions'] or '[]')
        changed = {item.get('field_name') for decision in decisions if decision.get('effect') == 'field_changes'
                   for item in (decision.get('changes') or []) if isinstance(item, dict)}
        if set(fields) != changed:
            raise HTTPException(409, 'Retificação: revisão não cobre os campos aplicados')
        current = revision(queue, run, db)
        if not current.get('pending'):
            return
        payload = json.loads(row['payload'])
        if current != payload.get('revision'):
            raise HTTPException(409, 'Retificação: manifesto mudou antes da finalização')
        db.execute("UPDATE document_review_state SET pending_documents='[]',detected_at=NULL WHERE owner=? AND source=? AND mode=? AND candidate_key=?",identity(run))
    if db is None:
        with queue._db(write=True) as connection:
            finalize(connection)
    else:
        finalize(db)
    return {'id':case_id,'finalized':True,'fields':sorted(fields)}
