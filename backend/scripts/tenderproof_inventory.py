"""Generate the 99-source matrix; --live performs bounded public read-only GETs."""
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tenderproof.inventory import build_inventory, probe_inventory, write_inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--listing-only", action="store_true", help="Do not inspect a sample detail page")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[2] / "docs/tenderproof-sources-99.json")
    args = parser.parse_args()
    audit = Path(__file__).resolve().parents[1] / "audit_live_99.json"
    inventory = build_inventory(json.loads(audit.read_text(encoding="utf-8")) if audit.exists() else None)
    if args.live:
        completed = 0
        def progress(row):
            nonlocal completed
            completed += 1
            if completed % 10 == 0 or completed == inventory["total_sources"]:
                print(json.dumps({"completed_sources": completed, "total_sources": inventory["total_sources"]}), flush=True)
        inventory = asyncio.run(probe_inventory(inventory, sample_details=not args.listing_only, progress=progress))
    write_inventory(inventory, args.output)
    print(json.dumps({"sources": inventory["total_sources"], "categories": inventory["categories"], "probes": inventory.get("probe_counts"), "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
