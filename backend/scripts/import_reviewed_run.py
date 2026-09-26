"""Validate/import one reviewed TenderProof run; dry-run is the default."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from app.tenderproof.reviewed_run_import import import_reviewed_run
from app.tenderproof.store import TenderProofStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("envelope", type=Path, help="JSON tenderproof.reviewed-run.v1")
    parser.add_argument("--artifact", type=Path, help="override artifact.content_path")
    parser.add_argument("--apply", action="store_true", help="persist run and artifact (otherwise dry-run)")
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.envelope.read_text(encoding="utf-8"))
        if args.artifact:
            payload.setdefault("artifact", {})["content_path"] = str(args.artifact)
            payload["artifact"].pop("content_base64", None)
        result = import_reviewed_run(payload, TenderProofStore(), dry_run=not args.apply)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
