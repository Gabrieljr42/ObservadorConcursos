"""Controlled TenderProof merge using existing versions and internal notifications.

Each public mutation owns its transaction and rolls back completely on failure.
No network transport is invoked. Outbox draining is an explicit operator action.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from dataclasses import replace
from urllib.parse import quote, urlsplit, urlunsplit

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError, OperationalError

from app.models import Concurso, ConcursoPublication, ConcursoVersion, Source
from app.publications import build_publication_hash
from app.notifications import create_notifications_for_version
from app.tenderproof import canonical
from app.tenderproof.contracts import FieldState, TenderProofRun, PageText
from app.tenderproof.fields import extract_fields
from app.tenderproof.processing import ProcessingError, extract_pages_isolated, pinned_page_limit, is_pinned_id8
from app.tenderproof.publication_models import PublicationOutbox, PublicationProposal
from app.tenderproof.security import TenderProofSettings
from app.tenderproof.source_adapters import get_source_adapter
from app.tenderproof.validation import validate_identity, document_identity_ids
from app.versioning import VERSIONED_FIELDS, build_change_summary, classify_change, diff_concurso, jsonable

PUBLISHABLE = ("titulo", "orgao", "edital_numero", "inscricao_inicio", "inscricao_fim", "prova_data", "taxa", "cargos")


def _hash(value):
    return hashlib.sha256(json.dumps(jsonable(value), sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def _error(code, message):
    raise HTTPException(status_code=code, detail=message)


def authorize(user):
    allowed = {s.strip() for s in os.getenv("TENDERPROOF_PUBLISHER_USER_IDS", "").split(",") if s.strip()}
    if not user.is_active or str(user.id) not in allowed:
        _error(403, "TenderProof: usuário sem permissão de revisão/publicação")


def _writes_enabled():
    if os.getenv("TENDERPROOF_PUBLICATION_ENABLED", "false").lower() != "true":
        _error(403, "TenderProof: publicação desabilitada; habilite somente no ambiente autorizado")


def _snapshot(contest):
    return {field: jsonable(getattr(contest, field)) for field in VERSIONED_FIELDS}


def _revision(db, contest):
    return {"values": _snapshot(contest), "updated_at": jsonable(contest.updated_at),
            "latest_version_id": db.scalar(select(func.max(ConcursoVersion.id)).where(ConcursoVersion.concurso_id == contest.id)),
            "source_id": contest.source_id, "external_id": contest.external_id, "link_pagina": contest.link_pagina}


def _same_url(left, right):
    def canonical(raw):
        p = urlsplit(raw or "")
        return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"), p.query, ""))
    return canonical(left) == canonical(right)


def _same_revision(current, recorded):
    # Pre-migration proposals omitted the nullable jobs column. Only an actual
    # NULL is compatible; a later job publication must still invalidate them.
    previous = dict(recorded)
    previous['values'] = {'cargos': None, **recorded['values']}
    return current == previous


def _revalidate(run, contest, source, store):
    _assert_document_review_clear(run)
    if len(run.fields) != len({f.field_name for f in run.fields}):
        _error(422, "TenderProof: campos duplicados na observação")
    if (run.is_synthetic_sample or run.mode == "mock") and os.getenv("TENDERPROOF_PUBLICATION_ALLOW_SYNTHETIC", "false").lower() != "true":
        _error(422, "TenderProof: material sintético permitido somente em ambiente isolado explicitamente configurado")
    if run.execution_status.value != "completed" or not run.artifact or not run.document:
        _error(422, "TenderProof: observação sem documento concluído")
    candidate = next((c for c in run.candidates if c.candidate_id == run.selected_candidate_id), None)
    if (not candidate or source.source_type != run.source or candidate.source != run.source
            or not candidate.external_id or candidate.external_id != contest.external_id
            or not _same_url(candidate.detail_url_observed, contest.link_pagina)):
        _error(422, "TenderProof: identidade exige fonte, identificador externo e URL de detalhe correspondentes")
    settings = TenderProofSettings.from_env()
    from app.tenderproof.continuous_store import SourcePolicy, get_continuous_store
    configuration = get_continuous_store().configuration(run.owner_user_id, run.source)
    if configuration:
        # Apply the current owner's source limits also when re-reading preserved
        # bytes. A paused collector may still have documents awaiting review.
        policy = SourcePolicy.model_validate(configuration['policy'])
        settings = replace(settings, limits=replace(settings.limits,
            max_download_bytes=policy.max_download_bytes,
            max_pages=policy.max_pdf_pages, max_documents=policy.max_documents))
    adapter = get_source_adapter(run.source)
    try:
        adapter.validate_detail_url(candidate.detail_url_observed)
        expected = adapter.candidate_from_url(candidate.detail_url_observed, candidate.title_observed)
        if expected.external_id != candidate.external_id:
            raise ValueError("candidate external identity differs from URL")
        for url in (run.document.url_requested, run.artifact.url_requested, run.artifact.url_final):
            adapter.validate_document_url(url, candidate)
        request_validator = getattr(adapter, 'validate_document_request', None)
        if run.document.acquisition_request is not None or callable(request_validator):
            if not callable(request_validator):
                raise ValueError('source has no document request contract')
            request_validator(run.document, candidate)
    except Exception:
        _error(422, "TenderProof: origem documental ou identidade fora do contrato da fonte")
    # The review gate above already requires an approved, current manifest and
    # exact selected bytes for a consolidated notice. Do not reject that same
    # reviewed document merely because its title describes the consolidation.
    invalid_title = r"anexo|gabarito|resultado" if run.document.kind == 'consolidado' else r"anexo|gabarito|resultado|retifica|consolidad"
    if run.document.kind not in ("edital", "consolidado") or re.search(invalid_title, run.document.title, re.I):
        _error(422, "TenderProof: documento não é edital principal")
    if not _same_url(run.document.url_requested, run.artifact.url_requested):
        _error(422, "TenderProof: artefato não corresponde ao documento selecionado")
    content = store.load_artifact_bytes(run.artifact)
    if (not content or len(content) > settings.limits.max_download_bytes or len(content) != run.artifact.byte_len
            or hashlib.sha256(content).hexdigest() != run.artifact.sha256):
        _error(422, "TenderProof: bytes ausentes, limite excedido ou hash documental inválido")
    try:
        if (run.source == 'ufu_selection' and candidate.external_id == '1843'
                and run.artifact.sha256 == '72d8f9c6c18c734e8227a14c036ca32b8b9f705b2db507c8cd0169f939dc0daf'
                and run.artifact.byte_len == 26619):
            # The accepted UFU artifact is an official detail HTML page, not a
            # PDF.  It is already byte/hash pinned above; preserve one logical
            # page so the normal identity/evidence/revalidation path applies.
            pages = [PageText(artifact_id=run.artifact.artifact_id, page_number=1,
                              text=content.decode('utf-8'))]
            errors = []
        else:
            pages, _, _, _, errors = extract_pages_isolated(content, artifact_id=run.artifact.artifact_id,
                                                       owner_id=str(run.owner_user_id),
                                                       max_pages=pinned_page_limit(run.source, candidate.external_id,
                                                                                    run.artifact.sha256, run.artifact.byte_len,
                                                                                    settings.limits.max_pages),
                                                       max_bytes=settings.limits.max_download_bytes,
                                                       capacity_wait_s=15, reuse_completed=True)
    except ProcessingError as exc:
        if str(exc) == 'concurrency_limit':
            _error(409, "TenderProof: processamento ocupado; tente a revalidação novamente")
        _error(422, "TenderProof: processamento documental falhou ou excedeu limites")
    except ValueError:
        _error(422, "TenderProof: processamento documental falhou ou excedeu limites")
    if (pinned_page_limit(run.source, candidate.external_id, run.artifact.sha256,
                          run.artifact.byte_len) == 75
            and not is_pinned_id8(run.source, candidate.external_id,
                                  run.artifact.sha256, run.artifact.byte_len, len(pages))):
        _error(422, "TenderProof: ID8 pinado exige exatamente 75 páginas")
    if errors:
        _error(422, "TenderProof: PDF incompleto ou ilegível na revalidação")
    from app.tenderproof.selection_scope import document_scope
    scope = document_scope(run.source, run.artifact, pages)
    if scope:
        _error(422, 'TenderProof: ' + scope['reason'])
    identity = validate_identity(candidate=candidate, pages=pages, document_title=run.document.title, document_url=run.artifact.url_final, document_kind=run.document.kind)
    if identity.status.value != "valid":
        _error(422, "TenderProof: identidade documental não validada")
    fresh_fields = extract_fields(candidate=candidate, artifact=run.artifact, pages=pages)
    artifacts = {run.artifact.artifact_id: run.artifact}
    if run.supplementary_documents:
        from app.tenderproof.supplementary_fields import supplement_fields
        try:
            for extra in run.supplementary_documents:
                if extra.artifact.artifact_id in artifacts:
                    raise ValueError('identificador de artefato adicional duplicado')
                artifacts[extra.artifact.artifact_id] = extra.artifact
            fresh_fields = supplement_fields(candidate, fresh_fields, run.supplementary_documents,
                store, settings, run.owner_user_id)
        except (ValueError, ProcessingError):
            _error(422, 'TenderProof: anexo não reproduzível ou identidade adicional inválida')
    fresh = {f.field_name: f for f in fresh_fields}
    # Title overlap alone is insufficient. Explicit portal ID in PDF OR matching
    # organization AND main edital number must tie the bytes to the baseline.
    full_text = "\n".join(p.text for p in pages)
    explicit_ids = document_identity_ids(adapter,candidate,pages)
    strong_id = explicit_ids == {candidate.external_id}
    # IMESO's verified per-contest bucket layout is independent of title text.
    # Require exact canonical main-document URL as well, never just any PDF in
    # that directory. Identity cannot be rescued if the PDF names another ID.
    if run.source == "imeso_open" and not explicit_ids and contest.link_edital:
        strong_id = bool(_same_url(contest.link_edital, run.artifact.url_final)
                         and re.search(r"/edital/1/" + re.escape(candidate.external_id) + r"/", urlsplit(run.artifact.url_final).path))
    org = fresh.get("orgao")
    edital = fresh.get("edital_numero")
    if not strong_id:
        strong_id = bool(not explicit_ids and org and edital and org.state == edital.state == FieldState.SUPPORTED
                         and contest.orgao and contest.edital_numero
                         and str(org.value).casefold() == contest.orgao.casefold()
                         and str(edital.value) == contest.edital_numero)
    if not strong_id:
        _error(422, "TenderProof: vínculo documental forte ausente (código explícito ou órgão e edital correspondentes)")
    page_map = {p.page_number: p.text for p in pages}
    eligible, blocked = {}, {}
    for field in run.fields:
        name = field.field_name
        reason = None
        fresh_field = fresh.get(name)
        if name not in PUBLISHABLE:
            reason = "escopo observado não equivale à faixa salarial canônica; merge não suportado"
        elif field.state != FieldState.SUPPORTED:
            reason = field.reason or field.state.value
        elif not field.validation.ok or not field.evidence:
            reason = "evidência ausente ou inválida"
        elif not fresh_field or fresh_field.state != FieldState.SUPPORTED or fresh_field.value != field.value:
            reason = "valor não reproduzido pelo extrator sobre os bytes preservados"
        elif not all(_reproduced_evidence(e, fresh_field, artifacts) for e in field.evidence):
            reason = "trecho, página, origem ou vínculo documental inválido"
        elif (not isinstance(field.value, list) or not field.value) if name == "cargos" else (not isinstance(field.value, str) or not field.value.strip()):
            reason = "exclusão implícita/valor inválido não permitido"
        if reason:
            blocked[name] = reason
        else:
            eligible[name] = field.value
    for name in PUBLISHABLE:
        if name not in eligible and name not in blocked:
            blocked[name] = "campo não extraído; preservar baseline"
    return eligible, blocked


def _reproduced_evidence(evidence, fresh_field, artifacts):
    """Exact match against extraction rerun on each verified artifact's bytes."""
    artifact = artifacts.get(evidence.artifact_id)
    return bool(artifact and evidence.validation.ok and evidence.snippet
        and evidence.document_sha256 == artifact.sha256
        and _same_url(evidence.source_url, artifact.url_final)
        and any(fresh.validation.ok and fresh.artifact_id == evidence.artifact_id
                and fresh.document_sha256 == evidence.document_sha256
                and _same_url(fresh.source_url, evidence.source_url)
                and fresh.page_number == evidence.page_number and fresh.snippet == evidence.snippet
                for fresh in fresh_field.evidence))


def _cast(name, value):
    return datetime.fromisoformat(value) if value is not None and name in ("inscricao_inicio", "inscricao_fim", "prova_data") else value


def _owned(db, proposal_id, user, lock=False):
    authorize(user)
    q = select(PublicationProposal).where(PublicationProposal.id == proposal_id, PublicationProposal.owner_user_id == user.id)
    if lock:
        q = q.with_for_update()
    proposal = db.scalar(q.execution_options(populate_existing=True))
    if not proposal:
        _error(404, "TenderProof: proposta não encontrada")
    return proposal


def _check_hash(proposal, expected):
    if expected != proposal.proposal_hash or _hash(proposal.payload) != proposal.proposal_hash:
        _error(409, "TenderProof: conteúdo revisado mudou; recarregue e revise")


def _assert_baseline(db, proposal, contest):
    if proposal.payload.get("action") == "create":
        if contest is not None:
            _error(409, "TenderProof: criação já possui alvo; recarregue")
        return
    if not contest or not _same_revision(_revision(db, contest), proposal.payload["baseline"]):
        _error(409, "TenderProof: baseline desatualizada; crie nova proposta e revise novamente")


def _publication_document_url(run):
    """A POST endpoint alone cannot identify/open the selected official PDF."""
    if run.document and run.document.acquisition_request is not None:
        candidate = next(c for c in run.candidates if c.candidate_id == run.selected_candidate_id)
        return candidate.detail_url_observed
    return run.artifact.url_final


def _document_access(run):
    if not run.document or not run.artifact or run.document.acquisition_request is None:
        return None
    return {'mode': 'preserved_pdf', 'official_page_url': _publication_document_url(run),
            'artifact_download_path': f'/tenderproof/runs/{quote(run.run_id, safe="")}/artifacts/{quote(run.artifact.artifact_id, safe="")}',
            'artifact_id': run.artifact.artifact_id, 'sha256': run.artifact.sha256,
            'requires_authentication': True}


def proposal_view(db, proposal):
    if proposal.payload.get('kind') == 'field_amendment':
        from app.tenderproof.amendment import proposal_view as amendment_view
        return amendment_view(proposal)
    # Normalized-link proposals intentionally have no TenderProofRun.  Keep
    # their GET contract parallel to the regular proposal shape without
    # attempting to validate a missing ``payload.run``.
    if proposal.payload.get('kind') in {'normalized_link_reference', 'normalized_link_repair'}:
        return {
            'id': proposal.id, 'run_id': proposal.run_id, 'concurso_id': proposal.concurso_id,
            'proposal_hash': proposal.proposal_hash, 'state': proposal.state,
            'action': proposal.payload['kind'], 'identity': None,
            'creation_metadata': None, 'document_access': None,
            'required_fields': ['publications'],
            'document_review': {'pending': False, 'reason': None},
            'blockers': [], 'rollback_effect': None,
            'baseline': None, 'proposed': proposal.payload.get('targets', []),
            'eligible_fields': proposal.approved_fields or ['publications'],
            'blocked_fields': [], 'evidences': [],
            'approved_fields': proposal.approved_fields, 'approved_by': proposal.approved_by,
            'approved_at': jsonable(proposal.approved_at),
            'authorization': proposal.payload.get('authorization'),
            'stale': False, 'version_id': proposal.version_id, 'result': proposal.result,
            'rollback_version_id': proposal.rollback_version_id, 'rollback_reason': proposal.rollback_reason,
            'rollback_by': proposal.rollback_by, 'rollback_at': jsonable(proposal.rollback_at),
            'rejection_reason': proposal.rejection_reason, 'rejected_by': proposal.rejected_by,
            'rejected_at': jsonable(proposal.rejected_at),
            'synthetic': False, 'targets': proposal.payload.get('targets', []),
            'requested_ids': proposal.payload.get('requested_ids', []),
        }
    from app.tenderproof.continuous_store import get_continuous_store
    run = TenderProofRun.model_validate(proposal.payload['run'])
    document_review = get_continuous_store().review_for_run(run)
    document_access = _document_access(run)
    outdated_document_link = bool(document_access and proposal.payload.get('action') == 'create'
        and proposal.state in ('proposed', 'approved')
        and proposal.payload.get('creation_metadata', {}).get('link_edital') != _publication_document_url(run))
    contest = db.get(Concurso, proposal.concurso_id, populate_existing=True) if proposal.concurso_id else None
    new_stale = False
    if proposal.payload.get("action") == "create" and proposal.state in ("proposed", "approved"):
        from app.tenderproof.publication_models import CanonicalIdentity
        identity = proposal.payload["identity"]
        new_stale = any(db.get(CanonicalIdentity, key) is not None for key, _ in identity["keys"])
        new_stale = new_stale or db.scalar(select(Concurso.id).where(Concurso.source_id == identity["source_id"], Concurso.external_id == identity["external_id"]).limit(1)) is not None
    return {"id": proposal.id, "run_id": proposal.run_id, "concurso_id": proposal.concurso_id,
            "proposal_hash": proposal.proposal_hash, "state": proposal.state,
            "action": proposal.payload.get("action", "update"), "identity": proposal.payload.get("identity"),
            "creation_metadata": proposal.payload.get("creation_metadata"),
            "document_access": document_access,
            "required_fields": list(canonical.REQUIRED) if proposal.payload.get("action") == "create" else [],
            "document_review": document_review,
            "blockers": ([document_review['reason']] if document_review['pending'] else []) +
                (["O acesso ao edital foi atualizado. Prepare uma nova proposta para revisar o vínculo com a página oficial."] if outdated_document_link else []),
            "rollback_effect": "Arquivar o concurso, preservando o histórico" if proposal.payload.get("action") == "create" else "Restaurar os valores anteriores",
            "baseline": proposal.payload["baseline"], "proposed": proposal.payload["proposed"],
            "eligible_fields": list(proposal.payload["proposed"]), "blocked_fields": proposal.payload["blocked_fields"],
            "evidences": proposal.payload["evidences"], "approved_fields": proposal.approved_fields,
            "approved_by": proposal.approved_by, "approved_at": jsonable(proposal.approved_at),
            "authorization": proposal.payload.get("authorization"),
            "stale": outdated_document_link or new_stale or (proposal.state in ("proposed", "approved") and proposal.payload.get("action") != "create" and (not contest or not _same_revision(_revision(db, contest), proposal.payload["baseline"]))),
            "version_id": proposal.version_id, "result": proposal.result,
            "rollback_version_id": proposal.rollback_version_id, "rollback_reason": proposal.rollback_reason,
            "rollback_by": proposal.rollback_by, "rollback_at": jsonable(proposal.rollback_at),
            "rejection_reason": proposal.rejection_reason, "rejected_by": proposal.rejected_by,
            "rejected_at": jsonable(proposal.rejected_at),
            "synthetic": proposal.payload["run"]["is_synthetic_sample"] or proposal.payload["run"]["mode"] == "mock"}


def get_proposal(db, proposal_id, user):
    return proposal_view(db, _owned(db, proposal_id, user))


def _assert_document_review_clear(run, *, queue=None, connection=None):
    from app.tenderproof.continuous_store import get_continuous_store
    queue = queue or get_continuous_store()
    review = queue.review_for_run(run, db=connection)
    if run.document and run.document.kind == 'consolidado' and not review['pending']:
        from app.tenderproof.review_cases import approved_case
        if connection is None:
            with queue._db() as read_connection:
                cleared = approved_case(queue,run,read_connection)
        else:
            cleared = approved_case(queue,run,connection)
        if not cleared:
            _error(409, 'TenderProof: edital consolidado exige revisão explícita dos efeitos das retificações')
    if review['pending']:
        _error(409, 'TenderProof: ' + review['reason'])


def _commit_with_document_gate(db, run):
    from app.tenderproof.continuous_store import get_continuous_store
    queue = get_continuous_store()
    # Revalidation/isolated PDF processing happens before this short lock.
    # Checkpoints cannot publish a new manifest between this check and the
    # canonical commit, including when the proposal predates the new document.
    with queue._db(write=True) as connection:
        _assert_document_review_clear(run, queue=queue, connection=connection)
        db.commit()


def create_proposal(db, *, run, concurso_id=None, source_id=None, user, store, authorization=None):
    authorize(user)
    if run.owner_user_id != user.id:
        _error(404, "TenderProof: observação não encontrada")
    contest, source, proxy, eligible, blocked, identity = canonical.resolve(db, run, store, concurso_id, source_id)
    concurso_id = contest.id if contest else None
    payload = {"action": "update" if contest else "create", "identity": identity,
               "creation_metadata": {"banca": source.name, "link_edital": _publication_document_url(run)} if not contest else None,
               "baseline": _revision(db, contest) if contest else {"values": {k: None for k in VERSIONED_FIELDS}},
               "proposed": eligible, "blocked_fields": blocked,
               "evidences": {f.field_name: {"value": f.value, "state": f.state.value, "reason": f.reason,
                                            "document_sha256": next(iter({e.document_sha256 for e in f.evidence}))
                                                if len({e.document_sha256 for e in f.evidence}) == 1 else None,
                                            "items": [e.model_dump(mode="json") for e in f.evidence]} for f in run.fields},
               "run": run.model_dump(mode="json")}
    if authorization is not None:
        from app.tenderproof.amendment import normalize_authorization
        payload['authorization'] = normalize_authorization(authorization)
    digest = _hash(payload)
    criteria = (PublicationProposal.owner_user_id == user.id, PublicationProposal.run_id == run.run_id,
                PublicationProposal.concurso_id == concurso_id, PublicationProposal.proposal_hash == digest)
    existing = db.scalar(select(PublicationProposal).where(*criteria))
    if existing:
        return proposal_view(db, existing)
    proposal = PublicationProposal(id="tpp-" + _hash([user.id, run.run_id, concurso_id, digest])[:32], owner_user_id=user.id, run_id=run.run_id,
                                   concurso_id=concurso_id, proposal_hash=digest, payload=payload)
    try:
        db.add(proposal)
        _commit_with_document_gate(db, run)
    except IntegrityError:
        db.rollback()
        existing = db.scalar(select(PublicationProposal).where(*criteria))
        if not existing:
            raise
        proposal = existing
    except Exception:
        db.rollback()
        raise
    return proposal_view(db, proposal)


def approve_proposal(db, *, proposal_id, proposal_hash, fields, user, store, authorization=None):
    try:
        proposal = _owned(db, proposal_id, user, lock=True)
        _check_hash(proposal, proposal_hash)
        if proposal.payload.get('kind') == 'field_amendment':
            from app.tenderproof.amendment import approve_proposal as approve_amendment
            from app.tenderproof.continuous_store import get_continuous_store
            return approve_amendment(db, proposal_id=proposal_id, proposal_hash=proposal_hash,
                                     fields=fields, user=user, authorization=authorization,
                                     queue=get_continuous_store(), store=store)
        if authorization is not None:
            from app.tenderproof.amendment import normalize_authorization
            if normalize_authorization(authorization) != proposal.payload.get('authorization'):
                _error(409, 'TenderProof: autorização diverge da proposta; prepare nova proposta com a referência correta')
        if proposal.state not in ("proposed", "approved"):
            _error(409, "TenderProof: proposta já aplicada ou revertida")
        contest = db.get(Concurso, proposal.concurso_id, populate_existing=True) if proposal.concurso_id else None
        _assert_baseline(db, proposal, contest)
        run = TenderProofRun.model_validate(proposal.payload["run"])
        target, source, _, eligible, _, identity = canonical.resolve(db, run, store, proposal.concurso_id, proposal.payload.get("identity", {}).get("source_id"))
        if proposal.payload.get("action") == "create" and target:
            _error(409, "TenderProof: concurso cadastrado após comparação; crie nova proposta")
        if proposal.payload.get("action") == "create" and proposal.payload["creation_metadata"] != {"banca": source.name, "link_edital": _publication_document_url(run)}:
            _error(409, "TenderProof: metadados de criação mudaram; recomparação necessária")
        if proposal.payload.get("action") == "create" and not set(canonical.REQUIRED).issubset(fields):
            _error(422, "TenderProof: aprove título, órgão e número do edital para criar")
        if not fields or len(fields) != len(set(fields)) or not set(fields).issubset(eligible):
            _error(422, "TenderProof: aprove explicitamente apenas campos elegíveis")
        changed = db.execute(update(PublicationProposal).where(
            PublicationProposal.id == proposal.id, PublicationProposal.state == proposal.state,
            PublicationProposal.approved_at == proposal.approved_at,
        ).values(approved_fields=sorted(fields), approved_by=user.id, approved_at=datetime.utcnow(), state="approved")
                             .execution_options(synchronize_session=False))
        if changed.rowcount != 1:
            _error(409, "TenderProof: revisão concorrente; recarregue a proposta")
        _commit_with_document_gate(db, run)
        db.refresh(proposal)
        return proposal_view(db, proposal)
    except Exception:
        db.rollback()
        raise


def _canonical_write(db, contest, values, expected_revision):
    # Guard every canonical value plus revision timestamp, so concurrent crawler
    # changes cannot be silently overwritten even when they do not use this API.
    conditions = [Concurso.id == contest.id, Concurso.updated_at == contest.updated_at,
                  Concurso.source_id == contest.source_id, Concurso.external_id == contest.external_id,
                  Concurso.link_pagina == contest.link_pagina]
    conditions.extend(getattr(Concurso, k) == getattr(contest, k) for k in VERSIONED_FIELDS)
    latest = select(func.max(ConcursoVersion.id)).where(ConcursoVersion.concurso_id == contest.id).scalar_subquery()
    conditions.append(latest == expected_revision["latest_version_id"] if expected_revision["latest_version_id"] is not None else latest.is_(None))
    result = db.execute(update(Concurso).where(*conditions).values(**values, updated_at=datetime.utcnow()).execution_options(synchronize_session=False))
    if result.rowcount != 1:
        _error(409, "TenderProof: baseline alterada concorrentemente; recomparação obrigatória")
    db.expire(contest)


def _version(db, proposal, contest, diff, action):
    version = ConcursoVersion(concurso_id=contest.id, content_hash=contest.content_hash,
                              change_type=classify_change(diff, is_created=action == "create"), changed_fields=diff,
                              change_summary=build_change_summary(diff, is_created=action == "create"),
                              raw_data_snapshot=jsonable({"canonical": contest.raw_data or {}, "tenderproof": {
                                  "proposal_id": proposal.id, "run_id": proposal.run_id, "action": action,
                                  "approved_by": proposal.approved_by, "authorization": proposal.payload.get('authorization'),
                                  "document_sha256": proposal.payload["run"]["artifact"]["sha256"]}}))
    db.add(version)
    db.flush()
    db.add(PublicationOutbox(version_id=version.id, proposal_id=proposal.id))
    return version


def apply_proposal(db, *, proposal_id, proposal_hash, user, store):
    _writes_enabled()
    try:
        proposal = _owned(db, proposal_id, user, lock=True)
        _check_hash(proposal, proposal_hash)
        if proposal.payload.get('kind') == 'field_amendment':
            from app.tenderproof.amendment import apply_proposal as apply_amendment
            from app.tenderproof.continuous_store import get_continuous_store
            return apply_amendment(db, proposal_id=proposal_id, proposal_hash=proposal_hash, user=user,
                                   queue=get_continuous_store(), store=store)
        if proposal.state in ("applied", "no_change", "rolled_back"):
            return proposal_view(db, proposal)
        if proposal.state != "approved" or not proposal.approved_fields:
            _error(409, "TenderProof: aprovação explícita necessária")
        creating = proposal.payload.get("action") == "create"
        operation = _hash([proposal.run_id, proposal.concurso_id if not creating else proposal.payload["identity"]["keys"][0][0]])
        previous = db.scalar(select(PublicationProposal).where(PublicationProposal.applied_observation == operation))
        if previous:
            # A distinct proposal hash may be produced by harmless run
            # metadata changes.  Recognize only an exact, same-owner replay;
            # never disclose or reuse another target/user's proposal.
            contest = db.get(Concurso, proposal.concurso_id, populate_existing=True) if proposal.concurso_id else None
            same_fields = sorted(previous.approved_fields or []) == sorted(proposal.approved_fields or [])
            proposed_equal = all(
                _hash(previous.payload.get("proposed", {}).get(field)) ==
                _hash(proposal.payload.get("proposed", {}).get(field))
                for field in (proposal.approved_fields or [])
            )
            same_replay = (
                previous.owner_user_id == user.id and previous.run_id == proposal.run_id
                and previous.concurso_id == proposal.concurso_id
                and previous.state in ("applied", "no_change")
                and same_fields and proposed_equal
            )
            if same_replay:
                _assert_baseline(db, proposal, contest)
                replay = proposal_view(db, previous)
                replay.update({"idempotent_replay": True,
                               "original_proposal_id": previous.id,
                               "requested_proposal_id": proposal.id})
                return replay
            _error(409, "TenderProof: concorrência/idempotência; recarregue e tente novamente")
        # CAS serializes duplicate requests on SQLite too; persisted unique key is
        # the final arbiter across distinct proposals/processes.
        claimed = db.execute(update(PublicationProposal).where(PublicationProposal.id == proposal.id, PublicationProposal.state == "approved", PublicationProposal.approved_at == proposal.approved_at).values(state="applying", applied_observation=operation).execution_options(synchronize_session=False))
        if claimed.rowcount != 1:
            _error(409, "TenderProof: operação concorrente; recarregue a proposta")
        contest = db.scalar(select(Concurso).where(Concurso.id == proposal.concurso_id).with_for_update().execution_options(populate_existing=True))
        _assert_baseline(db, proposal, contest)
        run = TenderProofRun.model_validate(proposal.payload["run"])
        target, source, proxy, eligible, _, identity = canonical.resolve(db, run, store, proposal.concurso_id, proposal.payload.get("identity", {}).get("source_id"))
        if creating and target:
            _error(409, "TenderProof: concurso cadastrado após revisão; recomparação necessária")
        if identity != proposal.payload.get("identity", identity):
            _error(409, "TenderProof: identidade mudou; recomparação necessária")
        if creating:
            if proposal.payload["creation_metadata"] != {"banca": source.name, "link_edital": _publication_document_url(run)}:
                _error(409, "TenderProof: metadados de criação mudaram; recomparação necessária")
            if not set(canonical.REQUIRED).issubset(proposal.approved_fields):
                _error(422, "TenderProof: campos mínimos não aprovados")
            contest = Concurso(source_id=source.id, external_id=proxy.external_id, banca=source.name,
                               titulo=eligible["titulo"], link_pagina=proxy.link_pagina,
                               link_edital=_publication_document_url(run), content_hash=_hash({}), raw_data={})
            db.add(contest)
            db.flush()
            proposal.concurso_id = contest.id
        canonical.bind(db, contest, identity, proposal)
        if not set(proposal.approved_fields).issubset(eligible):
            _error(422, "TenderProof: evidência aprovada deixou de ser elegível")
        values = {k: _cast(k, eligible[k]) for k in proposal.approved_fields}
        # A date-only extraction preserves time already known for that day.
        for name in ("inscricao_inicio", "inscricao_fim"):
            if (name in values and re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(eligible[name]))
                    and getattr(contest, name) and getattr(contest, name).date() == values[name].date()):
                values[name] = getattr(contest, name)
        merged = {k: getattr(contest, k) for k in VERSIONED_FIELDS} | values
        if merged.get("inscricao_inicio") and merged.get("inscricao_fim") and merged["inscricao_inicio"].date() > merged["inscricao_fim"].date():
            _error(422, "TenderProof: intervalo de inscrições inválido após merge")
        diff = diff_concurso(contest, merged)
        if creating:
            for name, value in values.items():
                setattr(contest, name, value)
            db.flush()
            db.refresh(contest)
            from types import SimpleNamespace
            diff = diff_concurso(SimpleNamespace(**{k: None for k in VERSIONED_FIELDS}), _snapshot(contest))
            proposal.version_id = _version(db, proposal, contest, diff, "create").id
        elif diff:
            _canonical_write(db, contest, values, proposal.payload["baseline"])
            proposal.version_id = _version(db, proposal, contest, diff, "apply").id
        proposal.state = "applied" if diff else "no_change"
        proposal.applied_observation = operation
        proposal.applied_at = datetime.utcnow()
        proposal.result = {"diff": diff, "after_revision": _revision(db, contest),
                           "notification_status": "outbox_pending" if diff else "not_required"}
        _commit_with_document_gate(db, run)
        return proposal_view(db, proposal)
    except (IntegrityError, OperationalError):
        db.rollback()
        _error(409, "TenderProof: concorrência/idempotência; recarregue e tente novamente")
    except Exception:
        db.rollback()
        raise


def create_normalized_link_proposal(db, *, concurso_ids, user, authorization=None):
    """Create a reviewable, explicit-ID plan for existing edital references."""
    authorize(user)
    ids = list(dict.fromkeys(concurso_ids))
    if not ids or len(ids) > 32:
        _error(422, "Referências documentais: informe de 1 a 32 concurso_ids explícitos")
    contests = db.scalars(select(Concurso).where(Concurso.id.in_(ids))).all()
    by_id = {contest.id: contest for contest in contests}
    if len(by_id) != len(ids):
        _error(404, "Referência documental: concurso inexistente na seleção explícita")
    targets = []
    for contest in (by_id[id_] for id_ in ids):
        link = contest.link_edital
        if not isinstance(link, str) or not urlsplit(link).scheme.lower() in {"http", "https"} or not urlsplit(link).netloc:
            continue
        documents = []
        tenderproof = (contest.raw_data or {}).get("tenderproof", {}) if isinstance(contest.raw_data, dict) else {}
        for amendment in tenderproof.get("amendments", []) if isinstance(tenderproof, dict) else []:
            candidates = []
            if isinstance(amendment, dict):
                candidates.append(amendment.get("base_document"))
                candidates.extend(amendment.get("amendment_documents") or [])
                if amendment.get("amendment_document"):
                    candidates.append(amendment.get("amendment_document"))
            for document in candidates:
                if not isinstance(document, dict) or not document.get("sha256") or not document.get("url") or not document.get("title"):
                    continue
                if any(existing.get("sha256") == document["sha256"] for existing in documents):
                    continue
                documents.append({"sha256": document["sha256"], "url": document["url"],
                                  "title": document["title"], "kind": document.get("kind", "outro"),
                                  "provenance": {"source": "raw_data.tenderproof.amendments",
                                                  "reference_only": False,
                                                  "human_read": False}})
        targets.append({
            "concurso_id": contest.id, "source_id": contest.source_id,
            "external_id": contest.external_id, "link_pagina": contest.link_pagina,
            "link_edital": link, "edital_numero": contest.edital_numero,
            "titulo": contest.titulo, "edital_data": jsonable(contest.edital_data),
            "documents": documents,
            "latest_version_id": db.scalar(select(func.max(ConcursoVersion.id)).where(ConcursoVersion.concurso_id == contest.id)),
        })
    if authorization is not None:
        from app.tenderproof.amendment import normalize_authorization
        authorization = normalize_authorization(authorization)
    payload = {"kind": "normalized_link_reference", "authorization": authorization,
               "targets": targets, "requested_ids": ids}
    proposal_hash = _hash(payload)
    proposal_id = "tpr-" + proposal_hash[:32]
    proposal = PublicationProposal(id=proposal_id, owner_user_id=user.id,
        run_id="normalized-link:" + proposal_hash[:32], concurso_id=None,
        proposal_hash=proposal_hash, payload=payload, state="proposed")
    db.add(proposal)
    db.commit()
    return {"id": proposal.id, "proposal_hash": proposal_hash, "state": proposal.state,
            "targets": targets, "rejected_ids": [id_ for id_ in ids if id_ not in {t["concurso_id"] for t in targets}]}


def _normalized_link_reference(target):
    """Build the same reference-only row as the crawler fallback.

    A normalized-link proposal may have no preserved amendment/document bytes.
    It still has an explicit, reviewed ``link_edital`` and must apply that
    reference atomically instead of silently becoming ``no_change``.
    """
    link = target["link_edital"].strip()
    title = str(target.get("edital_numero") or target.get("titulo") or "").strip()[:500]
    publication_type = "edital" if re.search(r"\.pdf(?:$|[?#])", link, re.I) else "outro"
    publication_date = target.get("edital_data")
    # SQLite round-trips timezone-aware columns as a naive datetime; the
    # crawler fallback hashes the original ISO value with ``+00:00``. Keep
    # proposal/apply hashes stable across both persistence dialects.
    if isinstance(publication_date, str) and "T" in publication_date and not re.search(r"(?:Z|[+-]\d\d:\d\d)$", publication_date):
        publication_date += "+00:00"
    content_hash = build_publication_hash(title, publication_date, link, publication_type)
    return {
        "title": title,
        "publication_type": publication_type,
        "publication_date": publication_date,
        "link": link,
        "content_hash": content_hash,
        "source": "concurso.link_edital",
        "provenance": {"kind": "normalized_link_fallback", "field": "link_edital", "reference_only": True},
    }


def approve_normalized_link_proposal(db, *, proposal_id, proposal_hash, fields, user, authorization=None):
    authorize(user)
    proposal = _owned(db, proposal_id, user, lock=True)
    _check_hash(proposal, proposal_hash)
    if proposal.payload.get("kind") != "normalized_link_reference" or proposal.state != "proposed":
        _error(409, "Referência documental: proposta não está pendente de aprovação")
    expected_authorization = proposal.payload.get("authorization")
    if expected_authorization is not None:
        from app.tenderproof.amendment import normalize_authorization
        if authorization is None or normalize_authorization(authorization) != expected_authorization:
            _error(409, "Referência documental: autorização diverge da proposta; prepare nova proposta")
    if set(fields) != {"publications"}:
        _error(422, "Referência documental: apenas o campo publications pode ser aprovado")
    proposal.approved_fields = ["publications"]
    proposal.approved_by = user.id
    proposal.approved_at = datetime.utcnow()
    proposal.state = "approved"
    db.commit()
    return {"id": proposal.id, "proposal_hash": proposal.proposal_hash, "state": proposal.state,
            "approved_fields": proposal.approved_fields, "approved_by": user.id}


def apply_normalized_link_proposal(db, *, proposal_id, proposal_hash, user):
    authorize(user)
    _writes_enabled()
    proposal = _owned(db, proposal_id, user, lock=True)
    _check_hash(proposal, proposal_hash)
    if proposal.state in ("applied", "no_change"):
        return proposal.result or {"id": proposal.id, "state": proposal.state}
    if proposal.state != "approved" or proposal.approved_fields != ["publications"]:
        _error(409, "Referência documental: aprovação explícita necessária")
    operation = _hash([proposal.id, proposal.proposal_hash])
    claimed = db.execute(update(PublicationProposal).where(
        PublicationProposal.id == proposal.id, PublicationProposal.state == "approved"
    ).values(state="applying", applied_observation=operation).execution_options(synchronize_session=False))
    if claimed.rowcount != 1:
        _error(409, "Referência documental: aplicação concorrente")
    from app.services import CrawlService
    applied, skipped = [], []
    try:
        for target in proposal.payload["targets"]:
            contest = db.scalar(select(Concurso).where(Concurso.id == target["concurso_id"]).with_for_update())
            current_latest = db.scalar(select(func.max(ConcursoVersion.id)).where(ConcursoVersion.concurso_id == contest.id)) if contest else None
            if (not contest or any(getattr(contest, key) != target[key] for key in ("source_id", "external_id", "link_pagina", "link_edital", "edital_numero", "titulo"))
                    or jsonable(contest.edital_data) != target["edital_data"]
                    or current_latest != target["latest_version_id"]):
                _error(409, "Referência documental: registro mudou desde o dry-run")
            publications = [{
                "title": document["title"],
                "publication_type": "edital" if document.get("kind") == "edital" else ("errata" if document.get("kind") in {"retificacao", "prorrogacao"} else "outro"),
                "publication_date": None, "link": document["url"],
                "content_hash": document["sha256"], "source": "raw_data.tenderproof.amendments",
                "provenance": document.get("provenance", {}),
                "document_sha256": document["sha256"],
            } for document in target.get("documents", [])]
            # A normalized-link target without preserved documents is still a
            # valid reference-only publication.  The old path passed an empty
            # list to _sync_publications, which returned no rows and caused the
            # approved proposal to be recorded as no_change.
            if not publications:
                publications = [_normalized_link_reference(target)]
            item = {"raw_data": {"publications": publications}, "link_edital": contest.link_edital,
                    "edital_numero": contest.edital_numero, "titulo": contest.titulo,
                    "edital_data": contest.edital_data}
            created = CrawlService(db)._sync_publications(contest, item)
            reconciled = created
            if not reconciled:
                # The crawler may already have committed this exact fallback
                # before the proposal was applied.  Reuse that row for the
                # audit version; never invent a second row or a document event.
                hashes = {p["content_hash"] for p in publications}
                existing = db.scalars(select(ConcursoPublication).where(
                    ConcursoPublication.concurso_id == contest.id,
                    ConcursoPublication.content_hash.in_(hashes),
                )).all()
                if existing and all(((row.raw_data or {}).get("provenance") or {}).get("kind") == "normalized_link_fallback" for row in existing):
                    reconciled = [{"title": row.title, "publication_type": row.publication_type,
                                   "publication_date": jsonable(row.publication_date), "link": row.link,
                                   "content_hash": row.content_hash} for row in existing]
            if reconciled:
                diff = {"publications_added": {"label": "publicações adicionadas", "old": [], "new": jsonable(reconciled)}}
                version = ConcursoVersion(concurso_id=contest.id, content_hash=contest.content_hash,
                    change_type="document_added", changed_fields=diff,
                    change_summary=build_change_summary(diff),
                    raw_data_snapshot=jsonable({"canonical": contest.raw_data or {}, "tenderproof": {
                        "proposal_id": proposal.id, "actor_user_id": user.id,
                        "source": "concurso.link_edital", "reference_only": True}}))
                db.add(version); db.flush()
                db.add(PublicationOutbox(version_id=version.id, proposal_id=proposal.id))
                applied.append({"concurso_id": contest.id, "publication_count": len(reconciled), "version_id": version.id})
            else:
                skipped.append(contest.id)
        proposal.state = "applied" if applied else "no_change"
        proposal.applied_at = datetime.utcnow()
        proposal.result = {"id": proposal.id, "state": proposal.state, "actor_user_id": user.id,
                           "source": "concurso.link_edital", "reference_only": True,
                           "applied": applied, "skipped": skipped}
        db.commit()
        return proposal.result
    except Exception:
        db.rollback()
        raise


def create_normalized_link_repair_proposal(db, *, concurso_ids, user, authorization=None):
    """Plan an audited receipt for fallback rows committed without a version.

    This deliberately consumes only existing rows and records their original
    observation timestamps; it never fabricates a collection event or fetches
    the referenced URL.
    """
    authorize(user)
    ids = list(dict.fromkeys(concurso_ids))
    if not ids or len(ids) > 32:
        _error(422, "Reparo documental: informe de 1 a 32 concurso_ids explícitos")
    if authorization is not None:
        from app.tenderproof.amendment import normalize_authorization
        authorization = normalize_authorization(authorization)
    targets = []
    for contest in db.scalars(select(Concurso).where(Concurso.id.in_(ids))).all():
        rows = db.scalars(select(ConcursoPublication).where(ConcursoPublication.concurso_id == contest.id)).all()
        fallback = [row for row in rows if ((row.raw_data or {}).get('provenance') or {}).get('kind') == 'normalized_link_fallback']
        if not fallback:
            continue
        targets.append({
            'concurso_id': contest.id,
            'latest_version_id': db.scalar(select(func.max(ConcursoVersion.id)).where(ConcursoVersion.concurso_id == contest.id)),
            'source_id': contest.source_id, 'external_id': contest.external_id,
            'link_pagina': contest.link_pagina, 'link_edital': contest.link_edital,
            'edital_numero': contest.edital_numero, 'titulo': contest.titulo,
            'edital_data': jsonable(contest.edital_data),
            'publications': [{
                'id': row.id, 'content_hash': row.content_hash, 'link': row.link,
                'title': row.title, 'publication_type': row.publication_type,
                'created_at': row.created_at.isoformat() if row.created_at else None,
            } for row in fallback],
        })
    if len(targets) != len(ids):
        _error(409, "Reparo documental: algum registro explícito não possui fallback elegível")
    payload = {'kind': 'normalized_link_repair', 'authorization': authorization,
               'targets': targets, 'requested_ids': ids,
               'reason': 'reconciliação tardia de publicação já persistida sem evento'}
    proposal_hash = _hash(payload)
    proposal_id = 'tpr-' + proposal_hash[:32]
    proposal = PublicationProposal(id=proposal_id, owner_user_id=user.id,
        run_id='normalized-link-repair:' + proposal_hash[:32], concurso_id=None,
        proposal_hash=proposal_hash, payload=payload, state='proposed')
    db.add(proposal); db.commit()
    return {'id': proposal.id, 'proposal_hash': proposal.proposal_hash,
            'state': proposal.state, 'targets': targets}


def approve_normalized_link_repair_proposal(db, *, proposal_id, proposal_hash, fields, user, authorization=None):
    authorize(user)
    proposal = _owned(db, proposal_id, user, lock=True)
    _check_hash(proposal, proposal_hash)
    if proposal.payload.get('kind') != 'normalized_link_repair' or proposal.state != 'proposed':
        _error(409, 'Reparo documental: proposta não está pendente de aprovação')
    expected = proposal.payload.get('authorization')
    if expected is not None:
        from app.tenderproof.amendment import normalize_authorization
        if authorization is None or normalize_authorization(authorization) != expected:
            _error(409, 'Reparo documental: autorização diverge da proposta')
    if set(fields) != {'publications'}:
        _error(422, 'Reparo documental: apenas o campo publications pode ser aprovado')
    proposal.approved_fields = ['publications']; proposal.approved_by = user.id
    proposal.approved_at = datetime.utcnow(); proposal.state = 'approved'; db.commit()
    return {'id': proposal.id, 'proposal_hash': proposal.proposal_hash, 'state': proposal.state}


def apply_normalized_link_repair_proposal(db, *, proposal_id, proposal_hash, user):
    authorize(user); _writes_enabled()
    proposal = _owned(db, proposal_id, user, lock=True); _check_hash(proposal, proposal_hash)
    if proposal.state in ('applied', 'no_change'):
        return proposal.result or {'id': proposal.id, 'state': proposal.state}
    if proposal.state != 'approved' or proposal.approved_fields != ['publications']:
        _error(409, 'Reparo documental: aprovação explícita necessária')
    applied = []
    try:
        for target in proposal.payload['targets']:
            contest = db.scalar(select(Concurso).where(Concurso.id == target['concurso_id']).with_for_update())
            latest = db.scalar(select(func.max(ConcursoVersion.id)).where(ConcursoVersion.concurso_id == contest.id)) if contest else None
            if not contest or latest != target['latest_version_id']:
                _error(409, 'Reparo documental: registro mudou desde o dry-run')
            rows = [db.get(ConcursoPublication, item['id']) for item in target['publications']]
            if any(row is None or row.concurso_id != contest.id or row.content_hash != item['content_hash'] for row, item in zip(rows, target['publications'])):
                _error(409, 'Reparo documental: publicação mudou desde o dry-run')
            diff = {'publications_added': {'label': 'publicações reconciliadas', 'old': [], 'new': target['publications']}}
            version = ConcursoVersion(concurso_id=contest.id, content_hash=contest.content_hash,
                change_type='document_added', changed_fields=diff, change_summary='Publicação já persistida reconciliada tardiamente; observação original preservada.',
                raw_data_snapshot={'canonical': contest.raw_data or {}, 'tenderproof': {
                    'proposal_id': proposal.id, 'actor_user_id': user.id, 'source': 'normalized_link_repair',
                    'original_observed_at': [item['created_at'] for item in target['publications']],
                    'human_read': False}})
            db.add(version); db.flush(); db.add(PublicationOutbox(version_id=version.id, proposal_id=proposal.id))
            applied.append({'concurso_id': contest.id, 'publication_count': len(rows), 'version_id': version.id})
        proposal.state = 'applied'; proposal.applied_at = datetime.utcnow()
        proposal.result = {'id': proposal.id, 'state': proposal.state, 'actor_user_id': user.id,
                           'source': 'normalized_link_repair', 'applied': applied, 'late_reconciliation': True}
        db.commit(); return proposal.result
    except Exception:
        db.rollback(); raise


def rollback_proposal(db, *, proposal_id, reason, user):
    _writes_enabled()
    try:
        proposal = _owned(db, proposal_id, user, lock=True)
        if proposal.payload.get('kind') == 'field_amendment':
            _error(409, 'TenderProof: retificação exige nova revisão documental para alterar seu efeito; reversão genérica recusada')
        if not reason or not reason.strip() or len(reason) > 2000:
            _error(422, "TenderProof: motivo de reversão obrigatório (até 2000 caracteres)")
        if proposal.state == "rolled_back":
            return proposal_view(db, proposal)
        if proposal.state != "applied":
            _error(409, "TenderProof: somente alteração aplicada pode ser revertida")
        contest = db.scalar(select(Concurso).where(Concurso.id == proposal.concurso_id).with_for_update().execution_options(populate_existing=True))
        if not _same_revision(_revision(db, contest), proposal.result["after_revision"]):
            _error(409, "TenderProof: mudanças posteriores impedem reversão automática")
        values = ({"status": "arquivado"} if proposal.payload.get("action") == "create" else
                  {name: _cast(name, delta["old"]) for name, delta in proposal.result["diff"].items()})
        merged = {k: getattr(contest, k) for k in VERSIONED_FIELDS} | values
        diff = diff_concurso(contest, merged)
        _canonical_write(db, contest, values, proposal.result["after_revision"])
        proposal.rollback_by = user.id
        proposal.rollback_at = datetime.utcnow()
        proposal.rollback_reason = reason.strip()
        proposal.rollback_version_id = _version(db, proposal, contest, diff, "rollback").id
        proposal.state = "rolled_back"
        # Already emitted internal notifications remain audit history. Pending
        # original notifications are suppressed; reversal has its own event.
        db.execute(update(PublicationOutbox).where(PublicationOutbox.version_id == proposal.version_id, PublicationOutbox.state == "pending").values(state="superseded"))
        db.commit()
        return proposal_view(db, proposal)
    except (IntegrityError, OperationalError):
        db.rollback()
        _error(409, "TenderProof: reversão concorrente; recarregue")
    except Exception:
        db.rollback()
        raise


def reject_proposal(db, *, proposal_id, reason, user):
    """Reject a pending proposal without touching canonical publication data."""
    authorize(user)
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 2000:
        _error(422, "TenderProof: motivo de rejeição obrigatório (até 2000 caracteres)")
    try:
        proposal = _owned(db, proposal_id, user, lock=True)
        if proposal.state == "rejected":
            return proposal_view(db, proposal)
        if proposal.state != "proposed":
            _error(409, "TenderProof: somente proposta pendente pode ser rejeitada")
        changed = db.execute(update(PublicationProposal).where(
            PublicationProposal.id == proposal.id,
            PublicationProposal.owner_user_id == user.id,
            PublicationProposal.state == "proposed",
        ).values(state="rejected", rejected_by=user.id, rejected_at=datetime.utcnow(),
                 rejection_reason=reason.strip()).execution_options(synchronize_session=False))
        if changed.rowcount != 1:
            db.rollback()
            current = _owned(db, proposal_id, user)
            if current.state == "rejected":
                return proposal_view(db, current)
            _error(409, "TenderProof: rejeição concorrente; recarregue a proposta")
        db.commit()
        db.refresh(proposal)
        return proposal_view(db, proposal)
    except (IntegrityError, OperationalError):
        db.rollback()
        _error(409, "TenderProof: rejeição concorrente; recarregue a proposta")
    except Exception:
        db.rollback()
        raise


def drain_outbox(db, *, outbox_id, user):
    """Explicit opt-in internal notification delivery. Never email/push/network.

    Claim, Notification rows, and delivery receipt share one transaction. This
    guarantee applies to this DB transport, not to arbitrary external senders.
    """
    authorize(user)
    _writes_enabled()
    try:
        row = db.scalar(select(PublicationOutbox).where(PublicationOutbox.id == outbox_id).with_for_update())
        if not row:
            _error(404, "TenderProof: evento inexistente")
        _owned(db, row.proposal_id, user)
        if row.state != "pending":
            return {"state": row.state, "created": 0}
        claim = db.execute(update(PublicationOutbox).where(PublicationOutbox.id == row.id, PublicationOutbox.state == "pending").values(state="delivering", attempts=PublicationOutbox.attempts + 1).execution_options(synchronize_session=False))
        if claim.rowcount != 1:
            _error(409, "TenderProof: entrega concorrente")
        version = db.get(ConcursoVersion, row.version_id)
        contest = db.get(Concurso, version.concurso_id)
        created = create_notifications_for_version(db, concurso=contest, version=version)
        row.state = "delivered"
        row.delivered_at = datetime.utcnow()
        db.commit()
        return {"state": "delivered", "created": created}
    except Exception:
        db.rollback()
        raise
