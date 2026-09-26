"""TenderProof Fase 3 — orquestração do fluxo ponta a ponta (sem tocar o catálogo).

Fluxo: discovery → seleção explícita → processamento do edital → comparação.
Nenhum método aqui escreve em ``concursos``, ``concurso_versions``,
``notifications`` ou qualquer tabela canônica. A baseline é sempre lida
(snapshot explícito ou SELECT read-only de um ``Concurso`` existente).
"""

from __future__ import annotations

import threading
import time
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from app.tenderproof.acquisition import (
    LISTING_URL,
    AcquisitionService,
    choose_edital,
    confirm_identity,
    filter_structured_observations,
    new_run_id,
    parse_document_candidates,
    parse_listing_candidates,
)
from app.tenderproof.compare import compare
from app.tenderproof.contracts import (
    SUPPORTED_SOURCE,
    Artifact,
    SupplementaryDocument,
    ComparisonResult,
    SessionRecord,
    DiscoveredCandidate,
    ExecutionStatus,
    TenderProofRun,
    ValidationStatus,
)
from app.tenderproof.fields import extract_fields, semantic_hash
from app.tenderproof.pdf_text import extract_pages
from app.tenderproof.processing import extract_pages_isolated, pinned_page_limit, is_pinned_id8
from app.tenderproof.security import TenderProofSettings
from app.tenderproof.solari_adapter import SolariDriver, SolariBrowserAdapter, collect_session_info
from app.tenderproof.store import TenderProofStore
from app.tenderproof.validation import validate_identity
from app.tenderproof.sources import SOURCE_LISTINGS
from app.tenderproof.source_adapters import get_source_adapter


class TenderProofBusy(Exception):
    """Outra execução TenderProof em andamento (concorrência máxima = 1)."""


class _ExecutionLease:
    """Coordinate API and workers that share the durable operational store."""
    def __init__(self, store, driver, *, wait_s=0):
        if not 0 <= wait_s <= 60:
            raise ValueError('espera pela aquisição deve estar entre zero e 60 segundos')
        self.store = store
        deadline = time.monotonic() + wait_s
        self.token = store.acquire_execution_lease(ttl_seconds=120)
        while self.token is None and time.monotonic() < deadline:
            time.sleep(min(0.25, max(0, deadline-time.monotonic())))
            self.token = store.acquire_execution_lease(ttl_seconds=120)
        if self.token is None:
            try:
                driver.close()
            except Exception:
                pass
            raise TenderProofBusy("outra aquisição TenderProof em andamento")
        self.stopped = threading.Event()
        self.lost = threading.Event()
        self.thread = threading.Thread(target=self._renew, daemon=True, name="tenderproof-acquisition-lease")
        self.thread.start()

    def _renew(self):
        while not self.stopped.wait(30):
            try:
                if not self.store.renew_execution_lease(self.token, ttl_seconds=120):
                    self.lost.set()
                    return
            except Exception:
                self.lost.set()
                return

    def check(self):
        if self.lost.is_set():
            raise TenderProofBusy("coordenação da aquisição perdida; resultado exige retomada")

    def release(self):
        self.stopped.set()
        self.thread.join(timeout=5)
        self.store.release_execution_lease(self.token)


def _sync_driver_info(run: TenderProofRun, driver: SolariDriver) -> None:
    """Associa sessões por etapa + diagnósticos ao run (qualquer driver).

    Idempotente: registros já presentes (mesma etapa + sessão) não duplicam,
    pois a coleta acontece antes e depois do ``close()``.
    """
    records, notes = collect_session_info(driver)
    seen = {(s.phase, s.session_id) for s in run.sessions}
    for record in records:
        if (record.phase, record.session_id) not in seen:
            run.sessions.append(SessionRecord.model_validate(record, from_attributes=True))
            seen.add((record.phase, record.session_id))
        else:  # atualiza estado (ex.: replay resolvido no close)
            for current in run.sessions:
                if (current.phase, current.session_id) == (record.phase, record.session_id):
                    current.replay_url = record.replay_url or current.replay_url
                    current.replay_status = record.replay_status
                    current.replay_note = record.replay_note or current.replay_note
                    current.closed = record.closed or current.closed
                    current.close_requested = record.close_requested or current.close_requested
    run.diagnostics.extend(note for note in notes if note not in run.diagnostics)
    if records:
        latest = records[-1]
        run.session_id = latest.session_id or run.session_id
        if latest.replay_url:
            run.replay_url = latest.replay_url
            run.replay_available = latest.replay_status == "available"
    else:  # compatibilidade com drivers sem registros
        run.session_id = driver.session_id or run.session_id
        replay = driver.replay_url()
        if replay:
            run.replay_url = replay
            run.replay_available = driver.replay_available


def _merge_session_records(target: TenderProofRun, observed: TenderProofRun) -> None:
    """Merge operational facts monotonically; never replace acquisition fields."""
    for update in observed.sessions:
        current = next((item for item in target.sessions if (item.phase, item.session_id) == (update.phase, update.session_id)), None)
        if current is None:
            target.sessions.append(update.model_copy(deep=True))
            continue
        current.closed = current.closed or update.closed
        current.close_requested = current.close_requested or update.close_requested
        if update.replay_status == "available" or current.replay_status != "available":
            current.replay_status = update.replay_status
            current.replay_url = update.replay_url or current.replay_url
            current.replay_note = update.replay_note or current.replay_note
    available = next((item for item in reversed(target.sessions) if item.replay_status == "available" and item.replay_url), None)
    if available:
        target.replay_available, target.replay_url = True, available.replay_url
    target.diagnostics.extend(note for note in observed.diagnostics if note not in target.diagnostics)


class TenderProofService:
    def __init__(
        self,
        store: TenderProofStore,
        settings: TenderProofSettings | None = None,
    ) -> None:
        self.store = store
        self.settings = settings or TenderProofSettings.from_env()
        self.acquisition = AcquisitionService(self.settings)

    def _save_acquisition(self, run):
        def merge(current):
            fresh = run.model_copy(deep=True)
            _merge_session_records(fresh, current)
            for name in TenderProofRun.model_fields:
                setattr(current, name, getattr(fresh, name))
        try:
            return self.store.update_run(run.run_id, merge)
        except KeyError:
            self.store.put_run(run)
            return run

    def _save_operational(self, snapshot):
        def merge(current):
            _merge_session_records(current, snapshot)
            current.updated_at = datetime.now(timezone.utc)
        return self.store.update_run(snapshot.run_id, merge)

    # -- discovery ------------------------------------------------------
    def start_discovery(
        self,
        driver: SolariDriver,
        *,
        source: str = SUPPORTED_SOURCE,
        listing_url: str = LISTING_URL,
        is_synthetic: bool = False,
        mode: str = "mock",
        owner_user_id: int | None = None,
    ) -> TenderProofRun:
        get_source_adapter(source)
        if mode not in ("mock", "real"):
            raise ValueError("modo deve ser 'mock' ou 'real'")
        lease = _ExecutionLease(self.store, driver)
        run = TenderProofRun(
            run_id=new_run_id(),
            owner_user_id=owner_user_id,
            source=source,
            mode=mode,  # type: ignore[arg-type]
            execution_status=ExecutionStatus.DISCOVERING,
            is_synthetic_sample=is_synthetic,
        )
        try:
            self._save_acquisition(run)
            candidates, _observed = self.acquisition.discover(driver, listing_url=listing_url, source=source, owner_user_id=owner_user_id)
            lease.check()
            if self.acquisition.last_recovery_report:
                run.diagnostics.append("recovery: " + json.dumps(self.acquisition.last_recovery_report, ensure_ascii=False))
            run.candidates = candidates
            page = self.acquisition.last_listing_page
            if page is not None:
                run.coverage = {"scope": "sample", "complete": False,
                                "truncated": page.truncated, "empty_evidence": page.empty_evidence,
                                "terminal_evidence": page.terminal_evidence, "next_urls": page.next_urls}
                run.diagnostics.extend(page.diagnostics)
            _sync_driver_info(run, driver)
            run.execution_status = ExecutionStatus.AWAITING_SELECTION if candidates else ExecutionStatus.COMPLETED
            run.updated_at = datetime.now(timezone.utc)
            return run
        except Exception as exc:
            run.execution_status = ExecutionStatus.FAILED
            run.error = SolariBrowserAdapter._safe_error(exc)
            _sync_driver_info(run, driver)
            run.updated_at = datetime.now(timezone.utc)
            return run
        finally:
            try:
                try:
                    driver.close()
                except Exception:
                    pass
                _sync_driver_info(run, driver)
                run.updated_at = datetime.now(timezone.utc)
                self._save_acquisition(run)
            finally:
                lease.release()

    # -- selection + processing -----------------------------------------
    def select_and_process(
        self,
        run_id: str,
        candidate_id: str,
        driver: SolariDriver,
        *,
        mode: str | None = None,
        baseline: dict[str, Any] | None = None,
        baseline_collected_at: datetime | None = None,
        baseline_origin: str = "",
    ) -> TenderProofRun:
        run = self.store.get_run(run_id)
        if run is None:
            raise KeyError(f"execução {run_id} não encontrada")
        if mode is not None and mode != run.mode:
            raise ValueError(
                f"modo divergente: execução iniciada em '{run.mode}', seleção em '{mode}'"
            )
        candidate = next((c for c in run.candidates if c.candidate_id == candidate_id), None)
        if candidate is None:
            raise KeyError(f"candidato {candidate_id} não está nesta execução (amostra limitada)")
        lease = _ExecutionLease(self.store, driver)
        try:
            # Another process may have consumed this run after our first read.
            run = self.store.get_run(run_id)
            if run is None:
                raise KeyError(f"execução {run_id} não encontrada")
        except Exception:
            try:
                driver.close()
            finally:
                lease.release()
            raise
        if run.execution_status != ExecutionStatus.AWAITING_SELECTION:
            try:
                driver.close()
            finally:
                lease.release()
            raise ValueError("execução não está aguardando seleção; crie outra execução")
        run.selected_candidate_id = candidate_id
        run.execution_status = ExecutionStatus.PROCESSING
        run.updated_at = datetime.now(timezone.utc)
        try:
            self._save_acquisition(run)
            document, downloaded, _observed = self.acquisition.select_and_fetch(
                driver, candidate=candidate
            )
            lease.check()
            run.document = document
            artifact = Artifact(
                artifact_id=f"art-{uuid.uuid4().hex[:10]}",
                sha256=downloaded.sha256,
                byte_len=len(downloaded.content),
                url_requested=downloaded.url_requested,
                url_final=downloaded.url_final,
                content_type=downloaded.content_type,
                downloaded_at=downloaded.downloaded_at,
            )
            self.store.save_artifact_file(artifact, downloaded.content)
            run.artifact = artifact
            adapter = get_source_adapter(candidate.source)
            supplementary = getattr(adapter, 'supplementary_documents', None)
            if callable(supplementary):
                selected = supplementary(self.acquisition.last_documents, document)
                if not isinstance(selected, list) or len(selected) > self.settings.limits.max_documents:
                    raise ValueError('seleção de documentos adicionais excede limites')
                for extra in selected:
                    lease.check()
                    acquired = self.acquisition.fetch_document(driver, candidate=candidate, document=extra)
                    extra_artifact = Artifact(artifact_id=f'art-{uuid.uuid4().hex[:10]}',
                        sha256=acquired.sha256, byte_len=len(acquired.content),
                        url_requested=acquired.url_requested, url_final=acquired.url_final,
                        content_type=acquired.content_type, downloaded_at=acquired.downloaded_at)
                    self.store.save_artifact_file(extra_artifact, acquired.content)
                    run.supplementary_documents.append(SupplementaryDocument(document=extra, artifact=extra_artifact))
                    self._save_acquisition(run)
            # Paid acquisition ends before local PDF work; parser time must not
            # keep the remote browser alive beyond the acquisition reservation.
            try:
                driver.close()
            except Exception as exc:
                run.diagnostics.append(f"encerramento antes do processamento: {type(exc).__name__}")
            _sync_driver_info(run, driver)
            self._save_acquisition(run)

            pages, total, processed, truncated, page_errors = extract_pages_isolated(
                downloaded.content,
                artifact_id=artifact.artifact_id,
                owner_id=str(run.owner_user_id),
                max_bytes=self.settings.limits.max_download_bytes,
                max_pages=pinned_page_limit(candidate.source, candidate.external_id,
                                             artifact.sha256, artifact.byte_len,
                                             self.settings.limits.max_pages),
                capacity_wait_s=15,
            )
            run.total_pages = total
            run.processed_pages = processed
            run.truncated = truncated
            run.page_errors = page_errors
            if (pinned_page_limit(candidate.source, candidate.external_id, artifact.sha256,
                                  artifact.byte_len) == 75
                    and not is_pinned_id8(candidate.source, candidate.external_id,
                                          artifact.sha256, artifact.byte_len, total)):
                raise ValueError('ID8 pinado exige exatamente 75 páginas')

            validation = validate_identity(
                candidate=candidate,
                pages=pages,
                document_title=document.title,
                document_url=document.url_final or document.url_requested,
                document_kind=document.kind,
            )
            run.validation = validation
            run.validation_status = validation.status

            run.fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
            if run.supplementary_documents:
                from app.tenderproof.supplementary_fields import supplement_fields
                run.fields = supplement_fields(candidate, run.fields, run.supplementary_documents,
                    self.store, self.settings, run.owner_user_id)
                if any(extra.reading and extra.reading.get('review_required') for extra in run.supplementary_documents):
                    if run.validation.status==ValidationStatus.VALID:
                        run.validation.status=ValidationStatus.PARTIAL
                    run.validation_status=run.validation.status
                    run.validation.warnings.append('Planilhas lidas por célula; interpretação e conferência documental pendentes.')
            run.semantic_hash = semantic_hash(run.fields)
            lease.check()

            run.comparison = compare(
                baseline=baseline,
                baseline_collected_at=baseline_collected_at,
                baseline_origin=baseline_origin or "Baseline correspondente não fornecida",
                fields=run.fields,
            )
            run.comparison_status = "compared"

            run.execution_status = ExecutionStatus.COMPLETED
            run.updated_at = datetime.now(timezone.utc)
            return run
        except Exception as exc:
            run.execution_status = ExecutionStatus.FAILED
            run.error = SolariBrowserAdapter._safe_error(exc)
            _sync_driver_info(run, driver)
            run.updated_at = datetime.now(timezone.utc)
            return run
        finally:
            try:
                try:
                    driver.close()
                except Exception:
                    pass
                _sync_driver_info(run, driver)
                run.updated_at = datetime.now(timezone.utc)
                self._save_acquisition(run)
            finally:
                lease.release()

    def attach_comparison(
        self,
        run_id: str,
        *,
        baseline: dict[str, Any] | None,
        baseline_collected_at: datetime | None,
        baseline_origin: str,
    ) -> TenderProofRun:
        def update(current):
            current.comparison = compare(baseline=baseline, baseline_collected_at=baseline_collected_at,
                                         baseline_origin=baseline_origin, fields=current.fields)
            current.comparison_status = "compared"
            current.updated_at = datetime.now(timezone.utc)
        return self.store.update_run(run_id, update)

    # -- replay / sessões sem browser ----------------------------------
    def refresh_replay(self, run_id: str, *, budget_s: float = 20.0) -> TenderProofRun:
        """Reconsulta replays pendentes só pelo control-plane (sem browser)."""
        from app.tenderproof.solari_adapter import SolariConfig, poll_replay_url

        run = self.store.get_run(run_id)
        if run is None:
            raise KeyError(f"execução {run_id} não encontrada")
        if run.is_synthetic_sample:
            return run
        import asyncio

        config = SolariConfig.from_env()
        if not config.configured:
            raise ValueError("SOLARI_API_KEY ausente para reconsultar o replay")
        interval = self.settings.limits.replay_poll_interval_s
        for record in run.sessions:
            if record.replay_url or not record.session_id:
                continue
            try:
                status, url, note = asyncio.run(
                    poll_replay_url(config, record.session_id, budget_s=budget_s, interval_s=interval)
                )
            except Exception as exc:  # noqa: BLE001
                record.replay_status = "failed"
                record.replay_note = f"reconsulta falhou: {exc.__class__.__name__}"
                continue
            record.replay_status = status  # type: ignore[assignment]
            record.replay_url = url
            record.replay_note = note
            if status == "available" and url:
                run.replay_url = url
                run.replay_available = True
        run.updated_at = datetime.now(timezone.utc)
        return self._save_operational(run)

    def reconcile_sessions(self, run_id: str) -> TenderProofRun:
        """Confere o estado remoto das sessões (control-plane; sem browser).

        Diferencia: confirmação do release_and_wait,
        solicitado e desconhecido. Nunca marca como encerrada só por expiração
        presumida; sem comprovação, registra a limitação.
        """
        from app.tenderproof.solari_adapter import SolariConfig, _get_solari_class

        run = self.store.get_run(run_id)
        if run is None:
            raise KeyError(f"execução {run_id} não encontrada")
        if run.is_synthetic_sample:
            run.diagnostics.append("reconcile: execução sintética, sem sessão remota")
            return self._save_operational(run)
        import asyncio

        config = SolariConfig.from_env()
        if not config.configured:
            raise ValueError("SOLARI_API_KEY ausente para reconciliar sessões")

        async def _check(session_id: str) -> str:
            cls = _get_solari_class()
            kwargs: dict[str, Any] = {"api_key": config.api_key, "region": config.region}
            if config.base_url:
                kwargs["base_url"] = config.base_url
            client = cls(**kwargs)
            try:
                await client.__aenter__()
                try:
                    try:
                        await asyncio.wait_for(client.sessions.get(session_id), timeout=10)
                    except Exception as exc:
                        return f"desconhecido(get falhou: {exc.__class__.__name__})"
                    try:
                        await asyncio.wait_for(client.sessions.release_and_wait(session_id), timeout=15)
                        from app.tenderproof.solari_adapter import confirm_browser_released
                        if await confirm_browser_released(client, session_id, timeout=8):
                            return "confirmado-encerrada(GET provider released/expired)"
                        return "solicitado(GET provider não confirmou encerramento)"
                    except Exception as exc:
                        return f"solicitado(sem confirmação: {exc.__class__.__name__})"

                finally:
                    try:
                        await client.__aexit__(None, None, None)
                    except BaseException:  # noqa: BLE001
                        pass
            except BaseException as exc:  # noqa: BLE001
                return f"desconhecido(cliente falhou: {exc.__class__.__name__})"

        for record in run.sessions:
            if not record.session_id or record.closed:
                continue
            try:
                outcome = asyncio.run(_check(record.session_id))
            except Exception as exc:  # noqa: BLE001
                outcome = f"desconhecido({exc.__class__.__name__})"
            if outcome.startswith(("confirmado", "solicitado")):
                record.close_requested = True
            if outcome.startswith("confirmado"):
                record.closed = True
            record.replay_note = ((record.replay_note or "") + f" | reconcile: {outcome}").strip(" |")
        run.updated_at = datetime.now(timezone.utc)
        return self._save_operational(run)


def read_only_baseline_from_concurso(concurso: Any) -> tuple[dict[str, Any], datetime | None, str]:
    """Monta a baseline a partir de um ``Concurso`` já persistido (só leitura).

    Nunca invoca ``CrawlService.crawl_source`` (que persistiria resultados).
    """
    baseline = {
        "titulo": getattr(concurso, "titulo", None),
        "orgao": getattr(concurso, "orgao", None),
        "edital_numero": getattr(concurso, "edital_numero", None),
        "inscricao_inicio": getattr(concurso, "inscricao_inicio", None),
        "inscricao_fim": getattr(concurso, "inscricao_fim", None),
        "prova_data": getattr(concurso, "prova_data", None),
        "salario_min": getattr(concurso, "salario_min", None),
        "salario_max": getattr(concurso, "salario_max", None),
        "cargos": getattr(concurso, "cargos", None),
    }
    collected = getattr(concurso, "updated_at", None) or getattr(concurso, "fetched_at", None)
    origin = (
        f"banco existente: concurso id={getattr(concurso, 'id', '?')} "
        f"(leitura somente leitura; coletado em {collected})"
    )
    return baseline, collected, origin


def run_connector_baseline_readonly(*, source_type: str = SUPPORTED_SOURCE) -> dict[str, Any]:
    """Helper opt-in: executa o conector diretamente, sem persistir.

    Nunca chama ``CrawlService.crawl_source``. Requer rede; não é usado pelos
    endpoints padrão (que preferem baseline do banco/snapshot com timestamp).
    """
    from app.connectors.registry import get_connector

    connector = get_connector(source_type)
    result = connector.crawl_with_diagnostics()
    return {
        "items": result.items,
        "candidates_found": result.run_data.candidates_found,
        "status": result.run_data.status,
    }
