"""Minimal local runner for a prepared field-changing notice.

The input JSON is the contract accepted by ``app.tenderproof.amendment``.
Preparation only records a review proposal.  ``--approve`` and ``--apply``
are separate explicit steps; this example never downloads a URL and never
changes the pilot unless ``--apply`` is supplied.

Example input (values abbreviated)::

  {
    "concurso_id": 3,
    "base_document": {"sha256": "...", "url": "...", "identity":
      {"source_id": 1, "external_id": "129", "edital_numero": "01/2026"}},
    "amendment_document": {"sha256": "...", "url": "...", "identity":
      {"source_id": 1, "external_id": "129", "edital_numero": "01/2026"}},
    "changes": {"inscricao_fim": {"previous": "...", "new": "...",
      "reason": "...", "provenance": {"sha256": "...", "page": 1,
      "snippet": "literal excerpt", "source_url": "..."}}},
    "reason": "Ato posterior altera o cronograma.",
    "periods": {"original": {}, "reopenings": [], "current": {}},
    "events": [],
    "authorization": {"actor_kind": "delegated_automation", "human_read": false,
      "delegation_reference": "review-id", "delegation_sha256": "..."}
  }

Run from ``backend`` with the configured database environment::

  .venv/Scripts/python scripts/amendment_example.py review.json --user-id 1
  .venv/Scripts/python scripts/amendment_example.py review.json --user-id 1 --approve
  .venv/Scripts/python scripts/amendment_example.py review.json --user-id 1 --apply --proposal-id tpa-...
"""
from __future__ import annotations

import argparse
import json
import sys

from app.database import SessionLocal
from app.models import User
from app.tenderproof import amendment
from app.tenderproof.continuous_store import get_continuous_store
from app.tenderproof.store import get_store
from app.tenderproof.contracts import TenderProofRun


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON contract for one retification")
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--proposal-id")
    parser.add_argument("--approve", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    with open(args.input, encoding="utf-8") as stream:
        payload = json.load(stream)
    store = get_store()
    queue = get_continuous_store()
    # The persisted run is deliberately resolved by id.  A caller may also
    # provide a serialized run in a local fixture, but it is validated before
    # entering the amendment service.
    if isinstance(payload.get("run"), dict):
        payload["run"] = TenderProofRun.model_validate(payload["run"])
    with SessionLocal() as db:
        user = db.get(User, args.user_id)
        if not user:
            raise SystemExit(f"usuário {args.user_id} não encontrado")
        if args.apply:
            if not args.proposal_id:
                raise SystemExit("--apply exige --proposal-id de uma proposta aprovada")
            proposal = amendment.get_proposal(db, args.proposal_id, user)
            result = amendment.apply_proposal(db, proposal_id=proposal["id"], proposal_hash=proposal["proposal_hash"], user=user,
                                              queue=queue, store=store)
        else:
            proposal = amendment.create_proposal(db, user=user, queue=queue, store=store, **payload)
            result = proposal
            if args.approve:
                result = amendment.approve_proposal(db, proposal_id=proposal["id"], proposal_hash=proposal["proposal_hash"],
                                                    fields=payload.get("fields"), user=user, queue=queue, store=store)
        print(json.dumps(result, ensure_ascii=False, default=str, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
