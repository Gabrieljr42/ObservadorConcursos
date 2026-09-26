"""Authenticated, explicitly authorized TenderProof review/publication API."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.tenderproof import publication as service
from app.tenderproof.store import get_store

router = APIRouter(prefix="/tenderproof/publications", tags=["TenderProof publication"])


class ProposalIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str = Field(min_length=1, max_length=128)
    concurso_id: int | None = Field(default=None, gt=0)
    source_id: int | None = Field(default=None, gt=0)
    authorization: dict | None = None

    @model_validator(mode="after")
    def create_requires_source(self):
        if self.concurso_id is None and self.source_id is None:
            raise ValueError("CREATE exige source_id explícito")
        return self


class ApplyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    proposal_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class NormalizedLinkProposalIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    concurso_ids: list[int] = Field(min_length=1, max_length=32)
    authorization: dict | None = None


class NormalizedLinkApproveIn(ApplyIn):
    fields: list[str] = Field(min_length=1, max_length=1)
    authorization: dict | None = None


class ApproveIn(ApplyIn):
    # Initial composed publication may explicitly approve the three identity
    # fields, useful base dates, and amendment effects in one proposal.
    fields: list[str] = Field(min_length=1, max_length=30)
    authorization: dict | None = None


class RollbackIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(min_length=1, max_length=2000)


class RejectIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(min_length=1, max_length=2000)


class AmendmentProposalIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    # Null targets are valid only for an initial composed proposal; the
    # amendment service still requires a reviewed run and two corroborated
    # documents before persisting it.
    concurso_id: int | None = Field(default=None, gt=0)
    source_id: int | None = Field(default=None, gt=0)
    run_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(min_length=1, max_length=128)
    review_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    base_document: dict
    amendment_document: dict
    changes: dict
    reason: str = Field(min_length=10, max_length=2000)
    authorization: dict
    periods: dict | None = None
    events: list[dict] = Field(default_factory=list, max_length=30)


@router.post('/amendments/proposals', status_code=201)
def create_amendment(payload: AmendmentProposalIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.tenderproof import amendment
    service.authorize(user)
    return amendment.create_proposal(db, user=user, **payload.model_dump())


@router.post("/proposals", status_code=201)
def create(payload: ProposalIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service.authorize(user)
    # A null target is CREATE, never an implicit source/ID lookup.  Requiring
    # the source selector at the boundary keeps identity resolution explicit;
    # canonical.resolve still verifies the run candidate/external URL and the
    # actual Source row before persisting the proposal.
    if payload.concurso_id is None and payload.source_id is None:
        raise HTTPException(422, "TenderProof: CREATE exige source_id explícito")
    run = get_store().get_run(payload.run_id)
    if not run or run.owner_user_id != user.id:
        raise HTTPException(404, "TenderProof: observação não encontrada")
    return service.create_proposal(db, run=run, concurso_id=payload.concurso_id, source_id=payload.source_id, user=user, store=get_store(), authorization=payload.authorization)


@router.get("/proposals/{proposal_id}")
def get(proposal_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.get_proposal(db, proposal_id, user)


@router.post("/proposals/{proposal_id}/approve")
def approve(proposal_id: str, payload: ApproveIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.approve_proposal(db, proposal_id=proposal_id, proposal_hash=payload.proposal_hash,
                                    fields=payload.fields, user=user, store=get_store(), authorization=payload.authorization)


@router.post("/proposals/{proposal_id}/apply")
def apply(proposal_id: str, payload: ApplyIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.apply_proposal(db, proposal_id=proposal_id, proposal_hash=payload.proposal_hash, user=user, store=get_store())


@router.post("/normalized-link/proposals", status_code=201)
def create_normalized_link_proposal(payload: NormalizedLinkProposalIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.create_normalized_link_proposal(db, concurso_ids=payload.concurso_ids, user=user, authorization=payload.authorization)


@router.post("/normalized-link/proposals/{proposal_id}/approve")
def approve_normalized_link_proposal(proposal_id: str, payload: NormalizedLinkApproveIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.approve_normalized_link_proposal(db, proposal_id=proposal_id, proposal_hash=payload.proposal_hash,
        fields=payload.fields, user=user, authorization=payload.authorization)


@router.post("/normalized-link/proposals/{proposal_id}/apply")
def apply_normalized_link_proposal(proposal_id: str, payload: ApplyIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.apply_normalized_link_proposal(db, proposal_id=proposal_id, proposal_hash=payload.proposal_hash, user=user)


@router.post("/normalized-link/repair/proposals", status_code=201)
def create_normalized_link_repair(payload: NormalizedLinkProposalIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.create_normalized_link_repair_proposal(db, concurso_ids=payload.concurso_ids, user=user, authorization=payload.authorization)


@router.post("/normalized-link/repair/proposals/{proposal_id}/approve")
def approve_normalized_link_repair(proposal_id: str, payload: NormalizedLinkApproveIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.approve_normalized_link_repair_proposal(db, proposal_id=proposal_id, proposal_hash=payload.proposal_hash,
        fields=payload.fields, user=user, authorization=payload.authorization)


@router.post("/normalized-link/repair/proposals/{proposal_id}/apply")
def apply_normalized_link_repair(proposal_id: str, payload: ApplyIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.apply_normalized_link_repair_proposal(db, proposal_id=proposal_id, proposal_hash=payload.proposal_hash, user=user)


@router.post("/proposals/{proposal_id}/rollback")
def rollback(proposal_id: str, payload: RollbackIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.rollback_proposal(db, proposal_id=proposal_id, reason=payload.reason, user=user)


@router.post("/proposals/{proposal_id}/reject")
def reject(proposal_id: str, payload: RejectIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.reject_proposal(db, proposal_id=proposal_id, reason=payload.reason, user=user)


@router.post("/outbox/{outbox_id}/deliver")
def deliver(outbox_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.drain_outbox(db, outbox_id=outbox_id, user=user)
