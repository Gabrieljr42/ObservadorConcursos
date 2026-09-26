"""Independent, application-owned adversarial suite. Proposal cannot set criteria."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.tenderproof.recovery import RecoveryPolicy, Snapshot, Strategy, VerifiedDocument, run_strategy

FIXTURES = Path(__file__).resolve().parent / "resources" / "recovery"
HOST = "novo.ibgpconcursos.com.br"
POLICY = RecoveryPolicy(hosts=(HOST,), expected_identity="ibgp:704:001/2026")


def load_snapshot(name: str) -> Snapshot:
    # Only fixed, application-owned fixture identifiers. No user paths.
    if name not in {f.stem for f in FIXTURES.glob("*.json")}:
        raise ValueError("unknown fixture")
    data = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    documents = {}
    for url, doc in data.pop("documents").items():
        content = doc.pop("content").encode()
        documents[url] = VerifiedDocument(content=content, sha256=hashlib.sha256(content).hexdigest(), **doc)
    data.pop("expected", None)
    data.pop("label", None)
    return Snapshot(documents=documents, **data)


def validate_strategy(strategy: Strategy) -> dict:
    if strategy.source != "ibgp":
        return {"passed": False, "reason": "source suite unavailable", "cases": []}
    cases = []
    for path in sorted(FIXTURES.glob("*.json")):
        expected = json.loads(path.read_text(encoding="utf-8"))["expected"]
        report = run_strategy(strategy, load_snapshot(path.stem), POLICY)
        cases.append({"name": path.stem, "expected": expected,
                      "actual": report["diagnosis"], "passed": report["diagnosis"] == expected})
    return {"passed": len(cases) == 10 and all(c["passed"] for c in cases),
            "strategy_hash": strategy.digest, "cases": cases, "is_synthetic": True}
