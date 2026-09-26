"""Approve and apply only the reviewed IBAM Caruaru cargo field.

This uses the normal publication controls and records an idempotency/outbox
receipt.  It does not mutate canonical tables directly.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.database import SessionLocal
from app.models import User
from app.tenderproof.publication_models import PublicationOutbox, PublicationProposal
from app.tenderproof import publication
from app.tenderproof.store import get_store


AUTHORIZATION = {
    "actor_kind": "delegated_automation",
    "human_read": False,
    "delegation_reference": "user-attachment:6b86284b-154e-4ef6-88a1-6318513307e3/pasted-text-1.txt",
    "delegation_sha256": "a8d5f58a652eaed76d186385e12dadf9cbc4acf71cca71d5535a1797aca059f6",
}
RUN_ID = "delivery-roles-ibam-caruaru-20260909-fe050e7f31d9bc59-v3"
FIELDS = ["cargos"]


def apply(*, proposal_id: str, proposal_hash: str, output: Path) -> dict:
    store = get_store()
    with SessionLocal() as db:
        record = db.get(PublicationProposal, proposal_id)
        if record is None or record.proposal_hash != proposal_hash:
            raise RuntimeError("proposal IBAM ausente ou hash divergente")
        if record.run_id != RUN_ID:
            raise RuntimeError("proposal não está vinculado ao run IBAM v3")
        user = db.get(User, record.owner_user_id)
        if user is None:
            raise RuntimeError("owner da proposta ausente")
        publication.authorize(user)
        before = publication.get_proposal(db, proposal_id, user)
        if set(FIELDS) - set(before["eligible_fields"]):
            raise RuntimeError("cargos não está elegível no proposal IBAM v3")
        if before["state"] == "proposed":
            approved = publication.approve_proposal(
                db, proposal_id=proposal_id, proposal_hash=proposal_hash,
                fields=FIELDS, user=user, store=store, authorization=AUTHORIZATION,
            )
        else:
            approved = before
        if approved["approved_fields"] != FIELDS:
            raise RuntimeError(f"aprovação não ficou cargos-only: {approved['approved_fields']}")
        result = publication.apply_proposal(
            db, proposal_id=proposal_id, proposal_hash=proposal_hash,
            user=user, store=store,
        )
        repeated = publication.apply_proposal(
            db, proposal_id=proposal_id, proposal_hash=proposal_hash,
            user=user, store=store,
        )
        if result["version_id"] != repeated["version_id"]:
            raise RuntimeError("reaplicação não idempotente")
        outbox = db.scalar(select(PublicationOutbox).where(
            PublicationOutbox.proposal_id == proposal_id,
        ).order_by(PublicationOutbox.id.desc()))
        notifications = publication.drain_outbox(
            db, outbox_id=outbox.id, user=user,
        ) if outbox and outbox.state == "pending" else None
        receipt = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "proposal_id": proposal_id,
            "proposal_hash": proposal_hash,
            "run_id": RUN_ID,
            "authorization": AUTHORIZATION,
            "approved_fields": FIELDS,
            "application": result,
            "idempotent_version": repeated["version_id"],
            "outbox_id": outbox.id if outbox else None,
            "outbox_state": outbox.state if outbox else None,
            "notifications": notifications,
        }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal-id", required=True)
    parser.add_argument("--proposal-hash", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = apply(proposal_id=args.proposal_id, proposal_hash=args.proposal_hash, output=args.output)
    print(json.dumps({
        "receipt": str(args.output),
        "proposal_id": receipt["proposal_id"],
        "state": receipt["application"]["state"],
        "concurso_id": receipt["application"]["concurso_id"],
        "version_id": receipt["application"]["version_id"],
        "idempotent_version": receipt["idempotent_version"],
        "outbox_id": receipt["outbox_id"],
        "outbox_state": receipt["outbox_state"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
