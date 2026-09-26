"""Authenticated synthetic recovery demonstration and human review API."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.auth import get_current_user
from app.models import User
from app.tenderproof.recovery import Strategy
from app.tenderproof.recovery_store import RecoveryConflict, RecoveryStore
from app.tenderproof.recovery_validation import POLICY, load_snapshot
from app.tenderproof.store import artifact_dir

router = APIRouter(prefix="/tenderproof/recovery", tags=["tenderproof"])


def get_recovery_store():
    return RecoveryStore(artifact_dir().parent / "recovery.sqlite3")


class ReviewIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    approve: bool
    reason: str = Field(min_length=1, max_length=1000)


class RollbackIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(min_length=1, max_length=1000)


def invoke(fn, *args):
    try:
        return fn(*args)
    except KeyError as exc:
        raise HTTPException(404, "proposal not found") from exc
    except RecoveryConflict as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/proposals", status_code=201)
def propose(payload: Strategy, user: User = Depends(get_current_user), store=Depends(get_recovery_store)):
    return store.propose(user.id, payload)


@router.get("/proposals/{proposal}")
def get(proposal: str, user: User = Depends(get_current_user), store=Depends(get_recovery_store)):
    return invoke(store.get, user.id, proposal)


@router.post("/proposals/{proposal}/validate")
def validate(proposal: str, user: User = Depends(get_current_user), store=Depends(get_recovery_store)):
    return invoke(store.validate, user.id, proposal)


@router.post("/proposals/{proposal}/observe-offline")
def observe(proposal: str, user: User = Depends(get_current_user), store=Depends(get_recovery_store)):
    return invoke(store.observe, user.id, proposal, load_snapshot("09_recovered_navigation"), POLICY)


@router.post("/proposals/{proposal}/review")
def review(proposal: str, payload: ReviewIn, user: User = Depends(get_current_user), store=Depends(get_recovery_store)):
    return invoke(store.review, user.id, proposal, payload.approve, payload.reason)


@router.post("/proposals/{proposal}/activate")
def activate(proposal: str, user: User = Depends(get_current_user), store=Depends(get_recovery_store)):
    return invoke(store.activate, user.id, proposal)


@router.post("/proposals/{proposal}/rollback")
def rollback(proposal: str, payload: RollbackIn, user: User = Depends(get_current_user), store=Depends(get_recovery_store)):
    return invoke(store.rollback, user.id, proposal, payload.reason)
