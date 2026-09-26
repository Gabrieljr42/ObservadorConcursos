"""TenderProof Fase 3 — endpoints de comparação e revisão (sem publicação).

Proteção: todos os endpoints exigem autenticação (mesmo JWT do app). Não há
endpoint público que consuma recursos pagos (Solari) sem controle. Artefatos
(PDF) só via endpoint autenticado explícito — nunca no checkpoint mobile.

Execuções e artefatos só podem ser acessados pelo usuário que iniciou o run.
"""

from __future__ import annotations

from datetime import datetime
from dataclasses import replace
import os
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Concurso, User
from app.tenderproof.acquisition import LISTING_URL
from app.tenderproof.contracts import SUPPORTED_SOURCE, TenderProofRun
from app.tenderproof.mock_demo import (
    MOCK_BASELINE,
    MOCK_BASELINE_COLLECTED_AT,
    MOCK_BASELINE_ORIGIN,
    build_mock_driver,
)
from app.tenderproof.security import TenderProofSettings
from app.tenderproof.service import (
    TenderProofBusy,
    TenderProofService,
    read_only_baseline_from_concurso,
)
from app.tenderproof.solari_adapter import SolariBrowserAdapter, SolariConfig, SolariNotConfigured
from app.tenderproof.store import get_store
from app.tenderproof.sources import SOURCE_LISTINGS, IMESO_SOURCE, build_imeso_mock_driver
from app.tenderproof.source_adapters import SOURCE_ADAPTERS

router = APIRouter(prefix="/tenderproof", tags=["tenderproof"])


def _service(source: str = SUPPORTED_SOURCE) -> TenderProofService:
    settings = replace(TenderProofSettings.from_env(), allowlist_hosts=SOURCE_ADAPTERS[source].allowed_hosts)
    return TenderProofService(get_store(), settings)


class StartRunIn(BaseModel):
    source: str = SUPPORTED_SOURCE
    # "mock": demonstração offline com material sintético explícito.
    # "real": sessão Solari real (exige SOLARI_API_KEY + solari-browser).
    mode: Literal["mock", "real"] = "mock"
    listing_url: str | None = None
    # Baseline opcional já conhecida pelo cliente (ex.: snapshot exibido).
    baseline_snapshot: dict[str, Any] | None = None


class SelectIn(BaseModel):
    candidate_id: str
    mode: Literal["mock", "real"] = "mock"
    # Quando informado, a baseline é lida do banco (somente leitura).
    baseline_concurso_id: int | None = None
    baseline_snapshot: dict[str, Any] | None = None
    baseline_origin: str = ""


def _driver_for(mode: str, source: str = SUPPORTED_SOURCE):
    if mode == "mock":
        if source not in (SUPPORTED_SOURCE, IMESO_SOURCE):
            raise HTTPException(422, "fonte sem demonstração sintética registrada")
        return (build_imeso_mock_driver() if source == IMESO_SOURCE else build_mock_driver()), True
    if source not in (SUPPORTED_SOURCE, IMESO_SOURCE):
        from app.tenderproof.http_driver import build_continuous_driver
        return build_continuous_driver(source, TenderProofSettings.from_env(), allow_browser=False), False
    config = SolariConfig.from_env()
    if not config.configured:
        raise HTTPException(
            status_code=503,
            detail="Verificação real pendente: SOLARI_API_KEY ausente. "
            "Use mode='mock' para a demonstração offline com material sintético.",
        )
    if os.getenv("TENDERPROOF_BROWSER_LIVE_ENABLED", "false").lower() != "true":
        raise HTTPException(status_code=403, detail="TenderProof: novas sessões pagas exigem habilitação operacional após autorização de orçamento")
    try:
        import solari_browser  # noqa: F401
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Verificação real pendente: pacote 'solari-browser' não instalado. "
            "Use mode='mock' para a demonstração offline.",
        )
    settings = TenderProofSettings.from_env()
    return SolariBrowserAdapter(config, settings, source=source), False


@router.post("/runs", response_model=TenderProofRun, status_code=201)
def start_run(
    payload: StartRunIn,
    current_user: User = Depends(get_current_user),
) -> TenderProofRun:
    _ = current_user
    if payload.source not in SOURCE_ADAPTERS:
        raise HTTPException(status_code=422, detail="fonte TenderProof não suportada")
    adapter = SOURCE_ADAPTERS[payload.source]
    listing_url = payload.listing_url or SOURCE_LISTINGS.get(payload.source, adapter.listing_urls[0])
    if listing_url not in adapter.listing_urls:
        raise HTTPException(status_code=422, detail="URL de listagem diverge da fonte selecionada")
    driver, is_synthetic = _driver_for(payload.mode, payload.source)
    try:
        run = _service(payload.source).start_discovery(
            driver,
            source=payload.source,
            listing_url=listing_url,
            is_synthetic=is_synthetic,
            mode=payload.mode,
            owner_user_id=current_user.id,
        )
    except SolariNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except TenderProofBusy as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return run


@router.get("/runs/{run_id}", response_model=TenderProofRun)
def get_run(run_id: str, current_user: User = Depends(get_current_user)) -> TenderProofRun:
    _ = current_user
    run = get_store().get_run(run_id)
    if run is None or run.owner_user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Execução TenderProof não encontrada")
    return run


@router.post("/runs/{run_id}/select", response_model=TenderProofRun)
def select_candidate(
    run_id: str,
    payload: SelectIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TenderProofRun:
    _ = current_user
    existing = get_run(run_id, current_user)
    if payload.mode != existing.mode:
        raise HTTPException(
            status_code=409,
            detail=f"modo divergente: execução iniciada em '{existing.mode}', seleção em '{payload.mode}'",
        )
    baseline: dict[str, Any] | None = None
    collected_at: datetime | None = None
    origin = payload.baseline_origin
    if payload.baseline_concurso_id is not None:
        # Somente leitura: SELECT sem add/commit; nunca CrawlService.
        concurso = db.get(Concurso, payload.baseline_concurso_id)
        if concurso is None:
            raise HTTPException(status_code=404, detail="Concurso baseline não encontrado")
        baseline, collected_at, origin = read_only_baseline_from_concurso(concurso)
    elif payload.baseline_snapshot is not None:
        baseline = payload.baseline_snapshot
        origin = origin or "snapshot informado pelo cliente"
    elif payload.mode == "mock" and existing.source == SUPPORTED_SOURCE:
        baseline, collected_at, origin = MOCK_BASELINE, MOCK_BASELINE_COLLECTED_AT, MOCK_BASELINE_ORIGIN
    driver, _ = _driver_for(payload.mode, existing.source)
    try:
        return _service(existing.source).select_and_process(
            run_id,
            payload.candidate_id,
            driver,
            mode=payload.mode,
            baseline=baseline,
            baseline_collected_at=collected_at,
            baseline_origin=origin,
        )
    except TenderProofBusy as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        # Inclui troca de modo no meio da execução.
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/runs/{run_id}/result", response_model=TenderProofRun)
def get_result(run_id: str, current_user: User = Depends(get_current_user)) -> TenderProofRun:
    return get_run(run_id, current_user)


@router.post("/runs/{run_id}/replay/refresh", response_model=TenderProofRun)
def refresh_replay(run_id: str, current_user: User = Depends(get_current_user)) -> TenderProofRun:
    """Reconsulta replays pendentes só pelo control-plane (sem novo browser)."""
    get_run(run_id, current_user)
    try:
        return _service().refresh_replay(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/runs/{run_id}/sessions/reconcile", response_model=TenderProofRun)
def reconcile_sessions(run_id: str, current_user: User = Depends(get_current_user)) -> TenderProofRun:
    """Confere o estado remoto das sessões (control-plane; sem browser)."""
    get_run(run_id, current_user)
    try:
        return _service().reconcile_sessions(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/runs/{run_id}/artifacts/{artifact_id}")
def get_artifact(
    run_id: str,
    artifact_id: str,
    current_user: User = Depends(get_current_user),
):
    _ = current_user
    run = get_store().get_run(run_id)
    if run is None or run.owner_user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Artefato não encontrado nesta execução")
    artifacts = ([run.artifact] if run.artifact else []) + [extra.artifact for extra in run.supplementary_documents]
    matching = [artifact for artifact in artifacts if artifact.artifact_id == artifact_id]
    if len(matching) != 1:
        raise HTTPException(status_code=404, detail="Artefato não encontrado nesta execução")
    data = get_store().load_artifact_bytes(matching[0])
    if data is None:
        raise HTTPException(status_code=404, detail="Bytes do artefato indisponíveis")
    workbook = (matching[0].content_type or '').split(';')[0].strip().lower() == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return Response(
        content=data,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if workbook else 'application/pdf',
        headers={"Content-Disposition": f'attachment; filename="{artifact_id}.xlsx"' if workbook else f'inline; filename="{artifact_id}.pdf"'},
    )
