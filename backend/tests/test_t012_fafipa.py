from pathlib import Path

import pytest

from app.tenderproof.fafipa_t012 import EXPECTED_SHA256, parse_file, preflight


FIXTURE = Path(__file__).parent / "fixtures" / "tenderproof_batch30_shared" / "fafipa_open-cycle1-detail-ee88ccd5ee.html"


def test_fafipa_t012_parse_is_bounded_and_proven():
    data = parse_file(FIXTURE)
    assert data["edital_numero"] == "001/2026"
    assert data["prova_data"] == "2026-11-01"
    assert len(data["cargos"]) == 14
    assert sum(x["vagas"] for x in data["cargos"] if isinstance(x["vagas"], int)) == 27


def test_fafipa_t012_fails_closed_on_drift():
    raw = FIXTURE.read_bytes()
    assert preflight(raw)["sha256"] == EXPECTED_SHA256
    with pytest.raises(ValueError):
        preflight(raw.replace(b"Mirador", b"Drifted", 1))


def test_fafipa_t012_fails_closed_on_replacement_bytes():
    with pytest.raises(ValueError):
        preflight(FIXTURE.read_bytes() + b"\n")
