"""Fresh EPL ReviewedRun round-trip and drift guards, offline only."""
import json
import sys
from pathlib import Path
from datetime import datetime

import pytest
from fastapi import HTTPException

ROOT = Path(__file__).parents[5]
sys.path.insert(0, str(ROOT / "backend" / "tests"))
from test_tenderproof_publication import env  # noqa: E402,F401

from app.models import Source  # noqa: E402
from app.tenderproof import publication as pub  # noqa: E402
from app.tenderproof.contracts import PageText  # noqa: E402
from app.tenderproof.fields import extract_fields as generic_extract  # noqa: E402
from app.tenderproof.reviewed_run_import import ReviewedRun, build_run, import_reviewed_run  # noqa: E402
from app.tenderproof.store import TenderProofStore  # noqa: E402
from epl_parser_r3 import DETAIL_URL, DOCUMENT_URL, extract_identity  # noqa: E402


ENVELOPE = Path(__file__).with_name("live-envelope-ready-r1.json")
ARTIFACT = ROOT / "backend" / ".tenderproof" / "r60rec" / "artifacts" / "art-8c5dbef058-b040f8c3ff74845185dfdfec2096b70da84a7ee10c54d228afe7b82ed205805f.pdf"


def payload():
    value = json.loads(ENVELOPE.read_text(encoding="utf-8"))
    value["artifact"]["content_path"] = str(ARTIFACT.resolve())
    return value


def test_fresh_reviewed_run_import_and_revalidate_round_trip(env, monkeypatch):
    db, _, user, contest, _, store = env
    value = payload()
    value["owner_user_id"] = user.id
    value["concurso_id"] = contest.id
    model = ReviewedRun.model_validate(value)
    content = ARTIFACT.read_bytes()
    run = build_run(model, content)
    saved = store.save_artifact_file(run.artifact, content)
    run.artifact = saved
    source = db.get(Source, contest.source_id)
    source.source_type = "epl_open"
    contest.external_id = "52"
    contest.link_pagina = DETAIL_URL
    contest.link_edital = DOCUMENT_URL
    contest.orgao = "Fundação Hospitalar Santa Terezinha de Erechim (FHSTE)"
    contest.edital_numero = "01/2023"
    db.commit()

    def dispatch(*, candidate, artifact, pages):
        generic = generic_extract(candidate=candidate, artifact=artifact, pages=pages)
        identity = extract_identity(artifact, pages, source=candidate.source, external_id=candidate.external_id)
        return generic + identity

    monkeypatch.setattr(pub, "extract_fields", dispatch)
    eligible, blocked = pub._revalidate(run, contest, source, store)
    assert set(eligible) == {"orgao", "edital_numero"}
    assert eligible["edital_numero"] == "01/2023"
    assert "cargos" not in eligible
    assert "cargos" in blocked
    assert import_reviewed_run({**value, "concurso_id": contest.id}, TenderProofStore(), dry_run=True)["status"] == "validated"


@pytest.mark.parametrize("mutate", ["url", "bytes"])
def test_fresh_run_rejects_stale_or_artifact_drift(env, monkeypatch, mutate):
    db, _, user, contest, _, store = env
    value = payload()
    value["owner_user_id"] = user.id
    value["concurso_id"] = contest.id
    model = ReviewedRun.model_validate(value)
    content = ARTIFACT.read_bytes()
    run = build_run(model, content)
    saved = store.save_artifact_file(run.artifact, content)
    run.artifact = saved
    source = db.get(Source, contest.source_id)
    source.source_type = "epl_open"
    contest.external_id = "52"
    contest.link_pagina = DETAIL_URL
    contest.link_edital = DOCUMENT_URL
    contest.orgao = "Fundação Hospitalar Santa Terezinha de Erechim (FHSTE)"
    contest.edital_numero = "01/2023"
    db.commit()
    if mutate == "url":
        run.document.url_requested = DOCUMENT_URL.replace("00052", "00099")
    else:
        run.artifact.sha256 = "0" * 64
    with pytest.raises(HTTPException):
        pub._revalidate(run, contest, source, store)
