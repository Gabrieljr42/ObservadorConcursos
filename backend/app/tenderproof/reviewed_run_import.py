"""Offline, guarded import of a reviewed document into the TenderProof ledger.

This is deliberately not a catalogue writer.  It creates the persisted run
which the normal proposal endpoint already consumes.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .contracts import (
    Artifact,
    DiscoveredCandidate,
    DocumentCandidate,
    Evidence,
    ExtractedField,
    FieldState,
    TenderProofRun,
    ValidationResult,
    ValidationStatus,
    ExecutionStatus,
)
from .store import TenderProofStore


class ReviewedArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    artifact_id: str = Field(min_length=1, max_length=128)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_len: int = Field(ge=0)
    url_requested: str = Field(min_length=1)
    url_final: str = Field(min_length=1)
    content_type: str | None = None
    downloaded_at: str
    content_path: str | None = None
    content_base64: str | None = None

    @model_validator(mode="after")
    def one_content(self):
        if bool(self.content_path) == bool(self.content_base64):
            raise ValueError("artifact exige exatamente content_path ou content_base64")
        return self


class ReviewedField(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field_name: str = Field(min_length=1, max_length=80)
    value: Any
    original_value: Any | None = None
    evidence: list[Evidence] = Field(min_length=1)
    units: dict[str, Any] | None = None


class ReviewedRun(BaseModel):
    """Versioned import envelope; ``pending_fields`` must be explicit empty."""
    model_config = ConfigDict(extra="forbid")
    schema: str = Field(pattern=r"^tenderproof\.reviewed-run\.v1$")
    source: str = Field(min_length=1, max_length=80)
    # ``None`` is the explicit, reviewed CREATE target.  The proposal/apply
    # transaction is the only allocator of the local Concurso primary key.
    # Positive IDs remain required for an envelope targeting an existing row;
    # zero/negative values are still rejected by the constrained type.
    concurso_id: int | None = Field(default=None, gt=0)
    external_id: str = Field(min_length=1, max_length=256)
    title: str = Field(min_length=1)
    detail_url: str = Field(min_length=1)
    artifact: ReviewedArtifact
    fields: list[ReviewedField] = Field(min_length=1)
    pending_fields: list[str] = Field(default_factory=list)
    reference_only: bool = True
    owner_user_id: int = Field(gt=0)
    observed_at: str

    @model_validator(mode="after")
    def checked(self):
        if self.pending_fields:
            raise ValueError("pending_fields não pode ser promovido por este importador")
        names = [f.field_name for f in self.fields]
        if len(names) != len(set(names)):
            raise ValueError("campo revisado duplicado")
        if not self.reference_only:
            raise ValueError("importação documental exige reference_only=true")
        for field in self.fields:
            if field.field_name == "cargos" and not isinstance(field.value, list):
                raise ValueError("cargos deve ser uma lista canônica")
        return self


def _content(spec: ReviewedArtifact) -> bytes:
    if spec.content_base64:
        try:
            return base64.b64decode(spec.content_base64, validate=True)
        except ValueError as exc:
            raise ValueError("content_base64 inválido") from exc
    return Path(spec.content_path).read_bytes()  # type: ignore[arg-type]


def _run_id(model: ReviewedRun) -> str:
    # Stable across retries/runtimes: only immutable acquisition identity and
    # reviewed values participate.  content_path/content_base64 are transport
    # locations/representations and downloaded_at is acquisition metadata, so
    # neither may split a run across Windows, Docker, or a sandbox volume.
    def semantic(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: semantic(item) for key, item in value.items()
                    if key not in {"evidence_id", "content_path", "content_base64", "downloaded_at"}}
        if isinstance(value, list):
            return [semantic(item) for item in value]
        return value

    artifact_identity = semantic(model.artifact.model_dump(mode="json"))
    # ReviewedRun v1 does not carry a separate page_count field; preserve the
    # physical page references as part of the semantic evidence identity.
    artifact_identity["reviewed_page_numbers"] = sorted({
        evidence.page_number
        for field in model.fields for evidence in field.evidence
        if evidence.page_number is not None
    })
    identity = {
        "source": model.source,
        # Owner is part of the import identity.  Without this boundary, the
        # same reviewed bytes could deterministically collide across operators
        # and an owner-1 handoff could appear to be owner-901's run. Existing
        # persisted runs remain readable by their stored ids; new imports use
        # this owner-scoped derivation and never take them over.
        "owner_user_id": model.owner_user_id,
        "concurso_id": model.concurso_id,
        "external_id": model.external_id,
        "artifact": artifact_identity,
        "fields": [semantic(f.model_dump(mode="json")) for f in model.fields],
    }
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:32]
    return f"tp-reviewed-{digest}"


def _semantic_run(run: TenderProofRun) -> dict[str, Any]:
    def clean(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: clean(item) for key, item in value.items()
                    if key not in {"run_id", "evidence_id", "storage_path", "downloaded_at"}}
        if isinstance(value, list):
            return [clean(item) for item in value]
        return value
    return clean(run.model_dump(mode="json", exclude={"created_at", "updated_at"}))


def _legacy_run_id(model: ReviewedRun) -> str:
    """Pre-path-independent ID used before artifact metadata was included."""
    def semantic(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: semantic(item) for key, item in value.items() if key != "evidence_id"}
        if isinstance(value, list):
            return [semantic(item) for item in value]
        return value
    identity = {"source": model.source, "owner_user_id": model.owner_user_id,
                "concurso_id": model.concurso_id, "external_id": model.external_id,
                "artifact_sha256": model.artifact.sha256,
                "fields": [semantic(f.model_dump(mode="json")) for f in model.fields]}
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:32]
    return f"tp-reviewed-{digest}"


def build_run(model: ReviewedRun, content: bytes) -> TenderProofRun:
    digest = hashlib.sha256(content).hexdigest()
    if digest != model.artifact.sha256 or len(content) != model.artifact.byte_len:
        raise ValueError("bytes do artefato não correspondem a sha256/byte_len declarados")
    artifact = Artifact(**model.artifact.model_dump(exclude={"content_path", "content_base64"}))
    candidate = DiscoveredCandidate(
        candidate_id=f"reviewed-{model.external_id}", title_observed=model.title,
        detail_url_observed=model.detail_url, external_id=model.external_id,
        observed_at=model.observed_at, source=model.source,
    )
    fields = [ExtractedField(field_name=f.field_name, state=FieldState.SUPPORTED,
                             value=f.value, original_value=f.original_value, evidence=f.evidence,
                             units=f.units)
              for f in model.fields]
    return TenderProofRun(
        run_id=_run_id(model), owner_user_id=model.owner_user_id, source=model.source,
        mode="real", execution_status=ExecutionStatus.COMPLETED,
        validation_status=ValidationStatus.VALID, candidates=[candidate],
        selected_candidate_id=candidate.candidate_id,
        document=DocumentCandidate(doc_id=artifact.artifact_id, title=model.title,
                                   url_requested=artifact.url_requested, url_final=artifact.url_final,
                                   kind="edital"), artifact=artifact, fields=fields,
        validation=ValidationResult(status=ValidationStatus.VALID),
        coverage={"concurso_id": model.concurso_id, "reference_only": True,
                  "reviewed_import": "tenderproof.reviewed-run.v1"},
    )


def import_reviewed_run(payload: dict[str, Any] | ReviewedRun, store: TenderProofStore, *, dry_run: bool = True) -> dict[str, Any]:
    model = payload if isinstance(payload, ReviewedRun) else ReviewedRun.model_validate(payload)
    content = _content(model.artifact)
    run = build_run(model, content)
    existing = store.get_run(run.run_id)
    if existing is None:
        # A deploy may encounter a run written by the pre-path-independent
        # algorithm.  Reuse it only after a full semantic comparison; never
        # overwrite/take over it and never silently accept divergent content.
        legacy_id = _legacy_run_id(model)
        if legacy_id != run.run_id:
            legacy = store.get_run(legacy_id)
            if legacy is not None:
                if _semantic_run(legacy) != _semantic_run(run):
                    raise ValueError("conflito forte: run legado diverge do conteúdo revisado")
                return {"run_id": legacy_id, "status": "idempotent_legacy", "dry_run": dry_run}
    if existing is not None:
        # ``save_artifact_file`` fills the deployment-local storage_path; it
        # is deliberately excluded from the content identity used for retry.
        left = existing.model_copy(deep=True)
        right = run.model_copy(deep=True)
        if left.artifact:
            left.artifact.storage_path = None
        if right.artifact:
            right.artifact.storage_path = None
        left_data = _semantic_run(left)
        right_data = _semantic_run(right)
        if left_data != right_data:
            raise ValueError("conflito forte: run_id determinístico já aponta para outro conteúdo")
        return {"run_id": run.run_id, "status": "idempotent", "dry_run": dry_run}
    if dry_run:
        return {"run_id": run.run_id, "status": "validated", "dry_run": True,
                "fields": [f.field_name for f in run.fields]}
    committed = store.commit_run_artifact(run, content)
    committed_artifact = committed.artifact.model_copy(deep=True) if committed.artifact else None
    expected_artifact = run.artifact.model_copy(deep=True) if run.artifact else None
    if committed_artifact:
        committed_artifact.storage_path = None
    if expected_artifact:
        expected_artifact.storage_path = None
    committed.artifact = committed_artifact
    run.artifact = expected_artifact
    if _semantic_run(committed) != _semantic_run(run):
        raise ValueError("conflito forte durante commit concorrente")
    return {"run_id": run.run_id, "status": "imported", "dry_run": False,
            "fields": [f.field_name for f in run.fields]}
