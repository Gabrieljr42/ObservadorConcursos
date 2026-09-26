"""Bounded continuous acquisition, always producing review observations only."""
from __future__ import annotations

from app.tenderproof.document_identity import document_manifest

from dataclasses import asdict, replace
import hashlib
import json
import logging
import os
import sqlite3
import time

from app.tenderproof.continuous_store import ContinuousStore, JobLease, LeaseLost, candidate_key, get_continuous_store
from app.tenderproof.contracts import DiscoveredCandidate, ExecutionStatus, SessionRecord, TenderProofRun
from app.tenderproof.http_driver import build_continuous_driver
from app.tenderproof.mock_demo import build_mock_driver
from app.tenderproof.security import TenderProofSettings
from app.tenderproof.service import TenderProofBusy, TenderProofService, _merge_session_records
from app.tenderproof.solari_adapter import collect_session_info
from app.tenderproof.source_adapters import get_source_adapter
from app.tenderproof.sources import build_imeso_mock_driver
from app.tenderproof.store import get_store


def continuous_enabled():
    return os.getenv("TENDERPROOF_CONTINUOUS_ENABLED", "false").lower() == "true"


def operator_authorized(owner):
    configured=os.getenv("TENDERPROOF_CONTINUOUS_OPERATOR_USER_IDS", "")
    return owner is not None and str(owner) in {value.strip() for value in configured.split(",") if value.strip().isdigit()}


class CollectionPaused(RuntimeError):
    pass


class CheckpointDriver:
    """Preserve the observed detail before PDF processing under the service lease."""
    def __init__(self, driver, engine, lease):
        self.driver, self.engine, self.lease = driver,engine,lease
        self.adapter=get_source_adapter(lease.source)
        self.started=time.monotonic()
        self.last_request=0.0
        request_guard_setter=getattr(driver,'set_request_guard',None)
        if callable(request_guard_setter):
            request_guard_setter(self._before)

    def __getattr__(self,name):
        return getattr(self.driver,name)

    def _before(self):
        self.engine.queue.check_lease(self.lease)
        config=self.engine.queue.configuration(self.lease.owner_user_id,self.lease.source)
        if not continuous_enabled() or not operator_authorized(self.lease.owner_user_id) or not config or not config["enabled"]:
            raise CollectionPaused("coleta contínua pausada")
        remaining=min(self.lease.policy.job_timeout_s-(time.monotonic()-self.started),self.lease.cycle_deadline-time.time())
        gap=max(0,self.last_request+self.lease.policy.min_request_gap_s-time.monotonic())
        if remaining<=gap:
            raise TimeoutError("prazo total de aquisição esgotado")
        if gap:
            time.sleep(gap)
        self.last_request=time.monotonic()

    def open_listing(self,url):
        self._before()
        self.adapter.validate_listing_url(url)
        return self.driver.open_listing(url)

    def open_detail(self,url):
        self._before()
        self.adapter.validate_detail_url(url)
        candidate=DiscoveredCandidate.model_validate(self.lease.payload)
        bind_candidate=getattr(self.driver,'set_candidate',None)
        if callable(bind_candidate):
            bind_candidate(candidate)
        html=self.driver.open_detail(url)
        self.adapter.confirm_identity(candidate,html,url)
        docs=self.adapter.documents(html,candidate)
        manifest=[document_manifest(doc) for doc in docs[:self.lease.policy.max_documents]]
        self.engine.queue.detail_checkpoint(self.lease,html,manifest,truncated=len(docs)>self.lease.policy.max_documents)
        return html

    def download(self,url,*,max_bytes):
        self._before()
        candidate=DiscoveredCandidate.model_validate(self.lease.payload)
        self.adapter.validate_document_url(url,candidate)
        return self.driver.download(url,max_bytes=min(max_bytes,self.lease.policy.max_download_bytes))

    def download_workbook(self,document,candidate,*,max_bytes):
        self._before()
        expected=DiscoveredCandidate.model_validate(self.lease.payload)
        if candidate!=expected:raise ValueError('Planilha fora do candidato da concessão')
        return self.driver.download_workbook(document,candidate,max_bytes=min(max_bytes,self.lease.policy.max_download_bytes))

    def download_document(self, document, candidate, *, max_bytes):
        self._before()
        expected=DiscoveredCandidate.model_validate(self.lease.payload)
        if (candidate.source,candidate.external_id,candidate.detail_url_observed)!=(expected.source,expected.external_id,expected.detail_url_observed):
            raise ValueError('candidato POST fora da concessão ativa')
        validator=getattr(self.adapter,'validate_document_request',None)
        download=getattr(self.driver,'download_document',None)
        if not callable(validator) or not callable(download):
            raise ValueError('driver não suporta exportação POST')
        validator(document,candidate)
        return download(document,candidate,max_bytes=min(max_bytes,self.lease.policy.max_download_bytes))


class ContinuousEngine:
    def __init__(self,queue=None,run_store=None,driver_factory=None,service_factory=None):
        self.queue=queue or get_continuous_store()
        self.runs=run_store or get_store()
        self.driver_factory=driver_factory
        self.service_factory=service_factory or TenderProofService

    def enqueue(self,owner,source,*,force=False,now=None):
        if not continuous_enabled():
            raise CollectionPaused("TENDERPROOF_CONTINUOUS_ENABLED está desativado")
        if not operator_authorized(owner):
            raise CollectionPaused("usuário sem autorização operacional de coleta contínua")
        adapter=get_source_adapter(source)
        for url in adapter.listing_urls:
            adapter.validate_listing_url(url)
        return self.queue.enqueue(owner,source,adapter.listing_urls,force=force,now=now)

    def schedule_due(self,*,now=None):
        if not continuous_enabled():
            return []
        now=time.time() if now is None else now
        self.queue.ready_jobs(now=now)  # reclaim expired leases before scheduling
        cycles=[]
        for config in self.queue.configurations():
            if config["enabled"] and operator_authorized(config["owner"]) and config["next_due"]<=now:
                try:
                    cycle=self.enqueue(config["owner"],config["source"],now=now)
                except (ValueError, CollectionPaused):
                    # One obsolete source configuration must not stop dispatch
                    # of existing jobs or scheduling the remaining sources.
                    logging.getLogger(__name__).warning("source scheduling refused: %s", config["source"])
                    continue
                if cycle:
                    cycles.append(cycle)
        return cycles

    def ready_jobs(self,*,limit=100):
        return [job for job in self.queue.ready_jobs(limit=limit)
                if operator_authorized(self.queue.owner_for_job(job))]

    def track(self,owner,source,url,title=None):
        if not operator_authorized(owner):
            raise CollectionPaused("usuário sem autorização operacional de coleta contínua")
        adapter=get_source_adapter(source)
        candidate=adapter.candidate_from_url(url,title=title)
        return self.queue.track(owner,source,candidate)

    def _settings(self,policy,*,remaining_s=None):
        settings=TenderProofSettings.from_env()
        return replace(settings,limits=replace(settings.limits,max_candidates=policy.max_candidates,
            max_navigations=4*(policy.max_documents+4),
            max_attempts=1,max_documents=policy.max_documents,max_download_bytes=policy.max_download_bytes,
            max_pages=policy.max_pdf_pages,total_timeout_s=min(policy.job_timeout_s,remaining_s) if remaining_s else policy.job_timeout_s,
            replay_deadline_s=0))

    def _driver(self,lease,settings):
        if self.driver_factory:
            driver=self.driver_factory(lease.source,settings,allow_browser=lease.allow_browser)
        elif lease.policy.mode=="mock":
            driver=build_imeso_mock_driver() if lease.source=="imeso_open" else build_mock_driver()
        else:
            driver=build_continuous_driver(lease.source,settings,allow_browser=lease.allow_browser)
        if lease.allow_browser and lease.policy.mode=="real":
            setter=getattr(driver,"set_session_observer",None)
            if not callable(setter):
                driver.close()
                raise RuntimeError("browser contínuo exige journal de criação/encerramento")
            pending=[]
            sessions={}
            def observer(event,session_id=None):
                if event=="creating":
                    if not continuous_enabled() or not operator_authorized(lease.owner_user_id):
                        raise CollectionPaused("criação de browser sem autorização operacional")
                    pending.append(self.queue.browser_creating(lease))
                elif event=="created":
                    if not pending:
                        raise ValueError("sessão sem intenção registrada")
                    attempt=pending.pop(0)
                    self.queue.browser_created(attempt,session_id)
                    sessions[session_id]=attempt
                elif event=="closed":
                    if session_id not in sessions:
                        raise ValueError("sessão encerrada sem journal")
                    self.queue.browser_closed(sessions[session_id],session_id)
                else:
                    raise ValueError("evento de sessão desconhecido")
            setter(observer)
        return CheckpointDriver(driver,self,lease)

    def _record_sessions(self,lease,driver,run):
        records,notes=collect_session_info(driver)
        observed=run.model_copy(deep=True)
        observed.sessions=[SessionRecord.model_validate(r,from_attributes=True) for r in records]
        observed.diagnostics.extend(note for note in notes if note not in observed.diagnostics)
        def merge(current):
            _merge_session_records(current,observed)
        try:
            persisted=self.runs.update_run(run.run_id,merge)
        except KeyError:
            _merge_session_records(run,observed)
            self.runs.put_run(run)
            persisted=run
        if lease.policy.mode=="real" and any(s.session_id and not s.closed for s in persisted.sessions):
            # Closure requested is not evidence of closure. Preserve the run for
            # control-plane reconciliation and prohibit another paid attempt.
            self.queue.hold_browser(lease.owner_user_id,lease.source,"run:"+run.run_id)
        return persisted

    def _finish_detail(self,lease,run):
        snapshot=self.queue.snapshot(lease.job_id,lease.owner_user_id)
        if not snapshot:
            raise ValueError("resultado sem checkpoint documental")
        metadata=snapshot["metadata"]
        manifest=sorted(metadata.get("documents",[]),key=lambda doc:(doc["url"],doc["title"]))
        summary={"title":lease.payload.get("title_observed"),"validation_status":run.validation_status.value,
            "artifact_sha256":run.artifact.sha256 if run.artifact else None,"semantic_hash":run.semantic_hash,
            "documents":manifest,"documents_truncated":metadata.get("documents_truncated",False),
            "is_synthetic_sample":run.is_synthetic_sample,"truncated_pdf":run.truncated}
        if run.supplementary_documents:
            summary['supplementary_documents'] = [
                {'document': document_manifest(extra.document), 'artifact_sha256': extra.artifact.sha256}
                for extra in run.supplementary_documents]
        from app.tenderproof.document_identity import observation_signature
        extractors={(e.method,e.method_version) for field in run.fields for e in field.evidence}
        signature=observation_signature(summary,run.validation.model_dump(mode='json'),extractors)
        # Old raw-URL signatures are compared in place: never migrate/delete
        # observations, overwrite their bytes, or merge different PDF hashes.
        if run.artifact:
            for previous in self.queue.document_signature_history(lease,signature,run.artifact.sha256):
                if not all(key in previous['summary'] for key in summary):
                    continue
                old_summary={key:previous['summary'][key] for key in summary}
                old=self.runs.get_run(previous['run_id'])
                if (old is None or old.owner_user_id!=lease.owner_user_id or old.source!=lease.source
                        or old.mode!=lease.policy.mode or old.execution_status!=ExecutionStatus.COMPLETED
                        or not old.artifact or old.artifact.sha256!=run.artifact.sha256):
                    continue
                old_candidate=next((c for c in old.candidates if c.candidate_id==old.selected_candidate_id),None)
                current_candidate=DiscoveredCandidate.model_validate(lease.payload)
                if (old_candidate is None or old_candidate.source!=lease.source or current_candidate.source!=lease.source
                        or candidate_key(old_candidate)!=candidate_key(current_candidate)):
                    continue
                old_extractors={(e.method,e.method_version) for field in old.fields for e in field.evidence}
                validation=old.validation.model_dump(mode='json')
                normalized=observation_signature(old_summary,validation,old_extractors)
                legacy=observation_signature(old_summary,validation,old_extractors,normalize=False)
                if normalized==signature and previous['signature'] in (legacy,normalized):
                    self.queue.record_document_signature_match(lease,previous,signature)
                    signature=previous['signature']
                    break
        # Association metadata complements the already signed manifest/hash;
        # exclude this additive field from signatures to preserve old dedup IDs.
        if run.document:
            summary['selected_document']=document_manifest(run.document)
        return self.queue.complete_detail(lease,run.run_id,signature,summary)

    def _parse_listing(self,lease,html):
        adapter=get_source_adapter(lease.source)
        page=adapter.parse_listing(html,lease.payload["url"],limit=lease.policy.max_candidates)
        for url in page.next_urls:
            adapter.validate_listing_url(url)
        for candidate in page.candidates:
            if candidate.source!=lease.source:
                raise ValueError("candidato de outra fonte")
            adapter.validate_detail_url(candidate.detail_url_observed)
        if not page.candidates and not page.next_urls and not page.empty_evidence:
            raise ValueError("listagem vazia sem evidência explícita")
        return page

    def process_job(self,job_id):
        if not continuous_enabled():
            return {"status":"paused"}
        if not operator_authorized(self.queue.owner_for_job(job_id)):
            return {"status":"operator_revoked"}
        lease=self.queue.claim(job_id)
        if not lease:
            return {"status":"not_claimed"}
        driver=None
        run=None
        execution_token=None
        try:
            # Crash after the run commit but before the queue commit: adopt the
            # durable completed run without opening a second network session.
            previous=self.runs.get_run(lease.previous_run_id) if lease.previous_run_id else None
            if (previous and previous.execution_status==ExecutionStatus.COMPLETED
                    and previous.owner_user_id==lease.owner_user_id and previous.source==lease.source
                    and previous.mode==lease.policy.mode):
                run=previous
                if lease.policy.mode=="real" and any(s.session_id and not s.closed for s in previous.sessions):
                    self.queue.hold_browser(lease.owner_user_id,lease.source,"run:"+previous.run_id)
                if lease.kind=="detail":
                    return {"status":"succeeded","observation_id":self._finish_detail(lease,previous),"recovered":True}
                snapshot=self.queue.snapshot(lease.job_id,lease.owner_user_id)
                if (snapshot and snapshot["url"]==lease.payload["url"] and
                        hashlib.sha256(snapshot["html"].encode("utf-8")).hexdigest()==snapshot["sha256"]):
                    page=self._parse_listing(lease,snapshot["html"])
                    page.sessions=[s.model_dump(mode="json") for s in previous.sessions]
                    self.queue.complete_listing(lease,snapshot["html"],page)
                    return {"status":"succeeded","kind":"listing","candidates":len(page.candidates),"recovered":True}
                raise ValueError("checkpoint de listagem concluída ausente ou corrompido")
            if lease.recovery_only:
                self.queue.fail(lease,"worker_lease_expired_without_completed_result",retryable=False)
                return {"status":"failed","error":"worker_lease_expired_without_completed_result"}
            settings=self._settings(lease.policy,remaining_s=max(0.01,lease.cycle_deadline-time.time()))
            settings=replace(settings, allowlist_hosts=get_source_adapter(lease.source).allowed_hosts)
            if lease.kind=="listing":
                # Detail processing uses the service's acquisition lease. Only
                # standalone listing work must claim it here.
                execution_token=self.runs.acquire_execution_lease(lease.policy.job_timeout_s+120)
                if not execution_token:
                    raise TenderProofBusy("outra aquisição em andamento")
            driver=self._driver(lease,settings)
            run=TenderProofRun(run_id=f"tp-{lease.job_id}-{lease.fence}",owner_user_id=lease.owner_user_id,
                source=lease.source,mode=lease.policy.mode,is_synthetic_sample=lease.policy.mode=="mock",
                sample_note="Coleta contínua limitada pelo ciclo; observação para revisão, sem publicação.",
                execution_status=ExecutionStatus.AWAITING_SELECTION)
            if lease.payload.get('_refresh_parent_run_id'):
                run.coverage = {'scope':'targeted_recollection', 'complete':False,
                                'parent_run_id':lease.payload['_refresh_parent_run_id']}
            self.queue.set_run_id(lease,run.run_id)
            if lease.kind=="listing":
                html=driver.open_listing(lease.payload["url"])
                self.queue.listing_checkpoint(lease,html)
                page=self._parse_listing(lease,html)
                driver.close()
                run.candidates=page.candidates
                run.execution_status=ExecutionStatus.COMPLETED
                run=self._record_sessions(lease,driver,run)
                page.sessions=[s.model_dump(mode="json") for s in run.sessions]
                self.queue.complete_listing(lease,html,page)
                return {"status":"succeeded","kind":"listing","candidates":len(page.candidates)}
            candidate=DiscoveredCandidate.model_validate(lease.payload)
            run.candidates=[candidate]
            self.runs.put_run(run)
            run=self.service_factory(self.runs,settings).select_and_process(run.run_id,candidate.candidate_id,driver,
                mode=lease.policy.mode,baseline_origin="Coleta contínua para revisão; catálogo não alterado")
            if run.execution_status!=ExecutionStatus.COMPLETED:
                if run.artifact and run.document:
                    self.queue.acquired_document_checkpoint(lease,run.run_id,{
                        'artifact_sha256':run.artifact.sha256,
                        'selected_document':document_manifest(run.document),
                        'supplementary_documents': [
                            {'document':document_manifest(extra.document),'artifact_sha256':extra.artifact.sha256}
                            for extra in run.supplementary_documents]})
                if run.error == 'ProcessingError: concurrency_limit' and not lease.allow_browser:
                    # HTTP contention is internal capacity, not a source error.
                    # Paid attempts retain existing accounting/closure handling.
                    raise TenderProofBusy('processamento local ocupado')
                raise ValueError("aquisição/processamento não concluído; consulte execução "+run.run_id)
            run=self._record_sessions(lease,driver,run)
            return {"status":"succeeded","observation_id":self._finish_detail(lease,run)}
        except LeaseLost:
            return {"status":"lease_lost"}
        except TenderProofBusy:
            try:
                self.queue.defer_busy(lease)
            except LeaseLost:
                return {"status":"lease_lost"}
            return {"status":"acquisition_busy"}
        except Exception as exc:
            # Persist operational codes, never arbitrary provider messages or
            # request credentials. The review run carries its sanitized detail.
            code=exc.__class__.__name__
            # Adapter contract ValueErrors are deterministic observations (for
            # example an ambiguous edital), so retrying the same bytes only
            # burns attempts and hides the review action needed to resume.
            known_contract_prefixes = {
                'fafipa_open': (
                    'ValueError: links de edital ambíguos',
                    'ValueError: nenhum edital principal inequívoco',
                ),
                'fapesb_selection': (
                    'ValueError: Original REDA', 'ValueError: PDF REDA',
                    'ValueError: Identidade REDA', 'ValueError: Identidade editorial mudou',
                    'ValueError: Anexos da aba',
                ),
            }
            contract_blocked = isinstance(exc, ValueError) and bool(run and run.error and
                any(str(run.error).startswith(prefix)
                    for prefix in known_contract_prefixes.get(run.source, ())))
            if run and run.execution_status!=ExecutionStatus.COMPLETED:
                run.execution_status=ExecutionStatus.FAILED
                run.error=run.error or code
            try:
                if run and run.execution_status==ExecutionStatus.COMPLETED and isinstance(exc,(OSError,sqlite3.Error)):
                    self.queue.finalize_pending(lease)
                else:
                    self.queue.fail(lease,run.error if contract_blocked else code,
                                    retryable=(not lease.recovery_only and not contract_blocked))
            except LeaseLost:
                return {"status":"lease_lost"}
            return {"status":"review_required" if contract_blocked else "retry_or_failed",
                    "error":run.error if contract_blocked else code}
        finally:
            try:
                if driver:
                    try:
                        driver.close()
                    finally:
                        if run:
                            self._record_sessions(lease,driver,run)
            finally:
                if execution_token:
                    self.runs.release_execution_lease(execution_token)

    def reconcile_browser(self,owner,source):
        if not operator_authorized(owner):
            raise CollectionPaused("usuário sem autorização operacional de coleta contínua")
        config=self.queue.configuration(owner,source)
        if not config or not config["browser_hold"]:
            return {"status":"no_hold"}
        hold=config["browser_hold"]
        if hold=="journal":
            attempts=self.queue.open_browser_attempts(owner,source)
            if any(item["job_status"]=="running" and (item["lease_until"] or 0)>time.time() for item in attempts):
                return {"status":"active_acquisition"}
            unknown=[item["attempt_id"] for item in attempts if not item["session_id"]]
            for attempt in attempts:
                if not attempt["session_id"]:
                    continue
                run=TenderProofRun(run_id="tp-reconcile-"+attempt["attempt_id"],owner_user_id=owner,source=source,
                    mode="real",execution_status=ExecutionStatus.FAILED,error="coleta interrompida; reconciliação de sessão",
                    sample_note="Reconciliação de sessão sem nova aquisição.",
                    sessions=[SessionRecord(phase="detail",session_id=attempt["session_id"])])
                self.runs.put_run(run)
                reconciled=self.service_factory(self.runs).reconcile_sessions(run.run_id)
                if all(session.closed for session in reconciled.sessions):
                    self.queue.browser_closed(attempt["attempt_id"],attempt["session_id"])
            remaining=self.queue.open_browser_attempts(owner,source)
            return {"status":"confirmed_closed" if not remaining else "still_unconfirmed",
                    "unknown_launch_attempts":unknown,"pending_sessions":len(remaining)}
        if not hold.startswith("run:"):
            raise ValueError("suspensão requer investigação operacional")
        run=self.runs.get_run(hold[4:])
        if not run or run.owner_user_id!=owner or run.source!=source:
            raise ValueError("execução para reconciliação não encontrada")
        run=self.service_factory(self.runs).reconcile_sessions(run.run_id)
        confirmed=bool(run.sessions) and all(not session.session_id or session.closed for session in run.sessions)
        if confirmed:
            self.queue.clear_browser_hold(owner,source,hold)
        return {"status":"confirmed_closed" if confirmed else "still_unconfirmed","run_id":run.run_id}
