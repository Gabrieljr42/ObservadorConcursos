from pathlib import Path
import pytest
from app.tenderproof.fafipa_t012_r4 import strong_preflight_file, validate_extracted_text, strong_binding_contract
from app.tenderproof.processing import extract_pages_isolated
from app.tenderproof.contracts import DiscoveredCandidate
from datetime import datetime, timezone
import sqlite3

PDF = Path(__file__).parents[2] / "docs/execucao/evidencias/T012/fafipa_open/artifacts/fafipa-4208-edital.pdf"

def test_fafipa_r4_strong_binding_fresh_extraction():
    result = strong_preflight_file(PDF)
    assert result["document_identity_ids"] == []
    assert result["identity_binding"] == "organization+main_edital"
    assert result["orgao"] == "Município de Mirador - PR"
    assert result["edital_numero"] == "001/2026"

def test_fafipa_r4_rejects_replacement_marker_before_identity():
    with pytest.raises(ValueError, match=r"U\+FFFD"):
        validate_extracted_text("Mirador 001/2026 valid marker \ufffd")
    validate_extracted_text("Mirador 001/2026 valid marker")

def test_fafipa_r4_real_adapter_fallback_contract_ephemeral_sqlite():
    pages, _, _, _, errors = extract_pages_isolated(PDF.read_bytes(), artifact_id="fafipa-4208-edital", owner_id="t012-r4-contract", max_pages=75, max_bytes=20 * 1024 * 1024, capacity_wait_s=15, reuse_completed=False)
    assert not errors
    db = sqlite3.connect(":memory:")
    db.execute("create table contest (external_id text, orgao text, edital_numero text)")
    db.execute("insert into contest values (?,?,?)", ("4208", "Município de Mirador - PR", "001/2026"))
    row = db.execute("select external_id, orgao, edital_numero from contest").fetchone()
    candidate = DiscoveredCandidate(candidate_id="fafipa_open-4208", title_observed="Concurso Público do Município de Mirador - PR", detail_url_observed="https://concursos.fundacaofafipa.org.br/informacoes/4208/", external_id=row[0], observed_at=datetime.now(timezone.utc), source="fafipa_open")
    result = strong_binding_contract(candidate, type("Contest", (), {"orgao": row[1], "edital_numero": row[2]})(), pages)
    assert result == {"document_identity_ids": [], "binding": "organization+main_edital"}
    db.close()

def test_fafipa_r6_round_trip_matches_fresh_source_parser_and_rejects_r3():
    import json
    from app.tenderproof.contracts import Artifact, DiscoveredCandidate
    from app.tenderproof.fields import extract_fields as deployed_extract
    from app.tenderproof.fafipa_t012_r4 import extract_fields as active_fafipa_extract
    from datetime import datetime, timezone
    run = json.loads((PDF.parents[0].parent / "live-envelope-ready-r6.json").read_text(encoding="utf-8"))
    old = json.loads((PDF.parents[0].parent / "T012-fafipa-open-reviewed-run-r3.json").read_text(encoding="utf-8"))
    pages, _, _, _, errors = __import__("app.tenderproof.processing", fromlist=["extract_pages_isolated"]).extract_pages_isolated(PDF.read_bytes(), artifact_id="fafipa-4208-edital", owner_id="t012-r6", max_pages=75, max_bytes=20 * 1024 * 1024, capacity_wait_s=15, reuse_completed=False)
    a = Artifact(**{k: run["artifact"][k] for k in ("artifact_id", "sha256", "byte_len", "url_requested", "url_final", "content_type", "content_path") if k != "content_path"}, downloaded_at=datetime.now(timezone.utc), storage_path=str(PDF.resolve()))
    c = DiscoveredCandidate(candidate_id="fafipa_open-4208", title_observed=run["title"], detail_url_observed=run["detail_url"], external_id="4208", observed_at=datetime.now(timezone.utc), source="fafipa_open")
    fresh = {f.field_name: f for f in deployed_extract(candidate=c, artifact=a, pages=pages)}
    active = {f.field_name: f for f in active_fafipa_extract(candidate=c, artifact=a, pages=pages, content=PDF.read_bytes())}
    assert not errors and set(fresh) >= {f["field_name"] for f in run["fields"]}
    assert len(active["cargos"].evidence) == 14
    assert active["cargos"].value == fresh["cargos"].value
    assert all(fresh[f["field_name"]].value == f["value"] for f in run["fields"])
    assert any(fresh[f["field_name"]].evidence[0].snippet != f["evidence"][0]["snippet"] for f in old["fields"] if f["field_name"] in fresh)


def test_fafipa_active_parser_is_single_exported_implementation():
    import inspect
    from app.tenderproof import fafipa_t012_r4
    assert len([name for name, value in inspect.getmembers(fafipa_t012_r4, inspect.isfunction)
                if name == "extract_fields"]) == 1
    assert fafipa_t012_r4.extract_fields.__code__.co_firstlineno == 63

def test_fafipa_r7_allocation_envelope_has_individual_cargo_evidence_and_rejects_r6_shape():
    import json
    root = PDF.parents[0].parent
    r7 = json.loads((root / "live-envelope-ready-r7.json").read_text(encoding="utf-8"))
    r6 = json.loads((root / "live-envelope-ready-r6.json").read_text(encoding="utf-8"))
    assert r7["concurso_id"] is None and r7["run_id"].startswith("tp-reviewed-r7-")
    cargos = next(f for f in r7["fields"] if f["field_name"] == "cargos")
    assert len(cargos["value"]) == 14 and len(cargos["evidence"]) == 14
    assert all("remuneracao" in item and "vagas" in item for item in cargos["value"])
    old_cargos = next(f for f in r6["fields"] if f["field_name"] == "cargos")
    assert len(old_cargos["evidence"]) != 14

def test_fafipa_r4_fails_closed_on_byte_drift():
    drift = PDF.read_bytes() + b"drift"
    with pytest.raises(ValueError):
        from app.tenderproof.fafipa_t012_r4 import strong_preflight
        strong_preflight(drift)
