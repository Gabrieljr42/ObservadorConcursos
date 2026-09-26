"""Additive TenderProof publication migration, compatible with MVP schema boot.

Revision: tenderproof-publication-002. Downgrade intentionally does not drop an
audit ledger: disable publication routes/flags to roll application code back.
"""
from app.tenderproof.publication_models import ensure_publication_schema
from app import models as _canonical_models  # register referenced canonical tables for CLI

REVISION = "tenderproof-publication-002"


def upgrade(engine):
    ensure_publication_schema(engine)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TenderProof additive publication schema")
    parser.add_argument("--apply", action="store_true", help="Apply to the explicitly configured authorized database")
    args = parser.parse_args()
    if not args.apply:
        parser.error("use --apply only after configuring the intended authorized database")
    from app.database import engine
    upgrade(engine)
    print(f"TenderProof migration {REVISION}: applied")
