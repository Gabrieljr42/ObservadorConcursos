"""Disposable ID16 importer/revalidation/proposal gate; never touches pilot state."""
from __future__ import annotations
import hashlib, json, os, tempfile
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[2]
os.environ["TENDERPROOF_PUBLICATION_ENABLED"] = "true"
os.environ["TENDERPROOF_PUBLISHER_USER_IDS"] = "1"
os.environ["TENDERPROOF_ARTIFACT_DIR"] = str(Path(tempfile.mkdtemp(prefix="id16-tp-root-")) / "artifacts")
os.environ["TENDERPROOF_CONTINUOUS_STORE_DIR"] = str(Path(tempfile.mkdtemp(prefix="id16-tp-continuous-")) / "store")

from app.database import Base
from app.models import Concurso, Source, User
from app.tenderproof.omni_osvaldo_cruz_jobs import build_reviewed_payload
from app.tenderproof.reviewed_run_import import import_reviewed_run
from app.tenderproof.store import TenderProofStore
from app.tenderproof.publication_models import ensure_publication_schema
from app.tenderproof import publication
from app.tenderproof.contracts import Artifact, DiscoveredCandidate, PageText
from app.tenderproof.fields import extract_fields
from app.tenderproof.processing import extract_pages_isolated
from io import BytesIO
from pypdf import PdfReader

content = (ROOT / "docs/execucao/evidencias/T010/id16.pdf").read_bytes()
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
ensure_publication_schema(engine)
Session = sessionmaker(engine, expire_on_commit=False)
store = TenderProofStore()
processing_pages, _, _, _, processing_errors = extract_pages_isolated(content, artifact_id="art-0a483f2ba1", owner_id="1", max_pages=60, max_bytes=30 * 1024 * 1024, reuse_completed=False)
payload = build_reviewed_payload(content, observed_at="2026-09-08T21:27:59.982220Z", page_texts=[page.text for page in processing_pages])
# Production revalidation compares evidence byte-for-byte with the generic
# identity extractor. Reuse those exact snippets for identity fields, while
# keeping the source-specific cargos values/evidence from the pinned parser.
reader = PdfReader(BytesIO(content))
pages = processing_pages
artifact = Artifact(artifact_id=payload["artifact"]["artifact_id"], sha256=payload["artifact"]["sha256"], byte_len=payload["artifact"]["byte_len"], url_requested=payload["artifact"]["url_requested"], url_final=payload["artifact"]["url_final"], downloaded_at=payload["artifact"]["downloaded_at"], storage_path=None)
candidate = DiscoveredCandidate(candidate_id="reviewed-246", title_observed=payload["title"], detail_url_observed=payload["detail_url"], external_id="246", observed_at=payload["observed_at"], source="omni_open")
generic = {f.field_name: f for f in extract_fields(candidate=candidate, artifact=artifact, pages=pages)}
for field in payload["fields"]:
    if field["field_name"] in ("orgao", "edital_numero"):
        field["evidence"] = [e.model_dump(mode="json") for e in generic[field["field_name"]].evidence]
    if field["field_name"] == "cargos":
        for cargo in field["value"]:
            cargo.pop("evidence", None)
imported = import_reviewed_run(payload, store, dry_run=False)
run = store.get_run(imported["run_id"])
fresh_pages, _, _, _, fresh_errors = extract_pages_isolated(content, artifact_id=run.artifact.artifact_id, owner_id="1", max_pages=60, max_bytes=30 * 1024 * 1024, reuse_completed=True)
fresh_map = {f.field_name: f for f in extract_fields(candidate=run.candidates[0], artifact=run.artifact, pages=fresh_pages)}
parsed_snips = [e["snippet"] for c in build_reviewed_payload(content)["fields"][0]["value"] for e in c.get("evidence", [])]
print(json.dumps({"debug_first_missing_snippet": next((s for s in parsed_snips if s not in fresh_pages[0].text and s not in fresh_pages[1].text), None)}, ensure_ascii=False))
print(json.dumps({"debug_cargos_equal": fresh_map["cargos"].value == next(f for f in run.fields if f.field_name == "cargos").value, "debug_cargos_state": fresh_map["cargos"].state.value, "debug_cargos_reason": fresh_map["cargos"].reason, "debug_storage_path": run.artifact.storage_path, "debug_artifact_dir": os.environ["TENDERPROOF_ARTIFACT_DIR"], "debug_errors": fresh_errors, "debug_page1_sha": hashlib.sha256(fresh_pages[0].text.encode()).hexdigest()}, ensure_ascii=False))

with Session() as db:
    user = User(id=1, name="ID16 disposable reviewer", email="id16@example.test", password_hash="unused", is_active=True)
    source = Source(name="OMNI Concursos Públicos", base_url="https://portal.omniconcursospublicos.com.br", source_type="omni_open")
    db.add_all([user, source]); db.flush()
    contest = Concurso(source_id=source.id, external_id="246", banca="OMNI Concursos", titulo="Concurso Público - 002/2024 - Prefeitura Municipal de Osvaldo Cruz -SP", orgao="Prefeitura Municipal De Osvaldo Cruz- Sp", edital_numero="002/2024", content_hash="0" * 64, link_pagina="https://portal.omniconcursospublicos.com.br/informacoes/246/", inscricao_inicio=datetime(2024, 11, 27), inscricao_fim=datetime(2024, 12, 29), salario_min=None, salario_max=None, raw_data={"fixture": "preserved-id16-catalogue-identity", "cargos_baseline": None})
    db.add(contest); db.commit()
    result = publication.create_proposal(db, run=run, user=user, store=store, authorization={"actor_kind":"delegated_automation", "human_read":False, "delegation_reference":"id16-disposable-gate", "delegation_sha256":hashlib.sha256(b"id16-disposable-gate").hexdigest()})
    print(json.dumps({"import": imported, "proposal": {"id": result["id"], "state": result["state"], "eligible_fields": result.get("eligible_fields"), "blocked_fields": result.get("blocked_fields"), "proposed": result.get("proposed"), "action": result.get("action"), "baseline": result.get("baseline")}}, ensure_ascii=False, default=str))
