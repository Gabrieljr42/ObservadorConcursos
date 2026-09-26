"""Re-extract six preserved 2026 edital PDFs and prepare normal proposals.

The base TenderProof extractor is reused for identity and ordinary fields. A
small source table below only resolves the literal registration/proof rows
whose wording is specific to each preserved edital. Original runs and bytes
remain untouched; new completed runs are stored and proposals stay proposed.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/app")

from app.database import SessionLocal
from app.models import User
from app.tenderproof import publication
from app.tenderproof.acquisition import new_run_id
from app.tenderproof.contracts import ComparisonResult, ExecutionStatus, FieldState
from app.tenderproof.fields import extract_fields, semantic_hash
from app.tenderproof.processing import extract_pages_isolated
from app.tenderproof.store import get_store
from app.tenderproof.validation import validate_identity


ROOT = Path("/var/lib/observador/tenderproof")
OUTPUT = ROOT / "product-completion/delivery-next-reextract-six-2026-20260909.json"
TARGETS = {
    "legatus_open": "tp-tcj-fcb88161aca85300b7577a2c9bb3ca8d-1",
    "funvapi_open": "tp-tcj-d0d2a0870efb5314aaaf97079b11ced0-1",
    "funcern_open": "tp-tcj-78d603004e005e7889bbab3e41ebb061-1",
    "fgv_open": "tp-tcj-9ba68e23375a5ff7a0fef6e8ea7bbbc5-1",
    "fcc_open": "tp-tcj-1c9a86c6c29557df9207489a99c50487-1",
    "facet_open": "tp-tcj-e34b795398cb56cc8260c5df21b3e3e4-1",
}
EXPECTED = {
    "legatus_open": {
        "orgao": "Prefeitura Municipal De Domingos Mourão",
        "edital_numero": "01/2026",
        "inscricao_inicio": "2026-01-12",
        "inscricao_fim": "2026-02-09",
        "prova_data": "2026-03-08",
    },
    "funvapi_open": {
        "orgao": "Prefeitura Municipal De Cajueiro",
        "edital_numero": "001/2026",
        "inscricao_inicio": "2026-04-27",
        "inscricao_fim": "2026-05-27",
        "prova_data": "2026-06-28",
    },
    "funcern_open": {
        "orgao": "Prefeitura Municipal De Lagoa De Pedras",
        "edital_numero": "01/2026",
        "inscricao_inicio": "2026-08-03",
        "inscricao_fim": "2026-09-10",
        "prova_data": "2026-11-01",
    },
    "funcern_selection": {
        "orgao": "Prefeitura Municipal De Lagoa De Pedras",
        "edital_numero": "01/2026",
        "inscricao_inicio": "2026-08-03",
        "inscricao_fim": "2026-09-10",
        "prova_data": "2026-11-01",
    },
    "fgv_open": {
        "orgao": "Prefeitura Municipal De Macaé",
        "edital_numero": "01/2026",
        "inscricao_inicio": "2026-03-30",
        "inscricao_fim": "2026-04-30",
        "prova_data": "2026-06-21",
    },
    "fcc_open": {
        "orgao": "Câmara Municipal De Presidente Prudente",
        "edital_numero": "01/2026",
        "inscricao_inicio": "2026-04-22",
        "inscricao_fim": "2026-05-21",
        "prova_data": "2026-07-12",
    },
    "facet_open": {
        "orgao": "Prefeitura Municipal De Floresta",
        "edital_numero": "01/2026",
        "inscricao_inicio": "2026-08-24",
        "inscricao_fim": "2026-10-01",
        "prova_data": "2026-11-01",
    },
}
AUTHORIZATION = {
    "actor_kind": "delegated_automation",
    "human_read": False,
    "delegation_reference": "user-attachment:6b86284b-154e-4ef6-88a1-6318513307e3/pasted-text-1.txt",
    "delegation_sha256": "a8d5f58a652eaed76d186385e12dadf9cbc4acf71cca71d5535a1797aca059f6",
}


def _iso_long(raw: str) -> str:
    normalized = re.sub(r"\s+", " ", raw).strip().lower().replace("marco", "março")
    value = _date_value(normalized)
    if not value:
        raise RuntimeError(f"data extensa inválida: {raw!r}")
    return value


def _iso_short(day: str, month: str, year: str) -> str:
    month_value = {
        "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3,
        "abril": 4, "maio": 5, "junho": 6, "julho": 7,
        "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11,
        "dezembro": 12,
    }[month.lower()]
    return f"{int(year):04d}-{month_value:02d}-{int(day):02d}"


def _source_patterns(source: str):
    if source == "legatus_open":
        registration = re.compile(
            rf"per[ií]odo\s+de\s+(?P<sd>\d{{1,2}})\s+de\s+(?P<sm>{MONTHS})\s+a\s+"
            rf"(?P<ed>\d{{1,2}})\s+de\s+(?P<em>{MONTHS})\s+de\s+(?P<year>\d{{4}})", re.I
        )
        proof = re.compile(rf"prova\s+escrita\s+objetiva\s+ser[aá]\s+realizada\s+na\s+data\s+prevista\s+de\s+(?P<date>{LONG_DATE})", re.I)
    elif source == "funvapi_open":
        registration = re.compile(rf"inscri[çc][õo]es[\s\S]{{0,500}}?do\s+dia\s+(?P<start>{LONG_DATE})[\s\S]{{0,220}}?do\s+dia\s+(?P<end>{LONG_DATE})", re.I)
        proof = re.compile(rf"aplica[çc][aã]o\s+da\s+prova\s+escrita\s+objetiva\s+e\s+prova\s+de\s+t[ií]tulos[\s\S]{{0,300}}?(?P<date>{NUM_DATE_DOT})", re.I)
    elif source in {"funcern_open", "funcern_selection"}:
        registration = re.compile(rf"\binscri[çc][õo]es\s+(?P<start>{NUM_DATE})\s+a\s+(?P<end>{NUM_DATE})", re.I)
        proof = re.compile(rf"aplica[çc][aã]o\s+da\s+prova\s+escrita\s+(?P<date>{NUM_DATE})", re.I)
    elif source == "fgv_open":
        registration = re.compile(rf"inscri[çc][õo]es[^.\n]{{0,120}}?per[ií]odo\s+de\s+(?P<start>{LONG_DATE})\s+a\s+(?P<end>{LONG_DATE})", re.I)
        proof = re.compile(rf"prova\s+objetiva[^.\n]{{0,180}}?realizada\s+na\s+data\s+prov[aá]vel\s+de\s+(?P<date>{LONG_DATE})", re.I)
    elif source == "fcc_open":
        registration = re.compile(rf"inscri[çc][õo]es\s+ficar[aã]o\s+abertas[^.\n]{{0,260}}?do\s+dia\s+(?P<start>{NUM_DATE})[^.\n]{{0,100}}?do\s+dia\s+(?P<end>{NUM_DATE})", re.I)
        proof = re.compile(rf"previs[aã]o\s+de\s+aplica[çc][aã]o\s+para\s+o\s+dia\s+(?P<date>{NUM_DATE})", re.I)
    elif source == "facet_open":
        registration = re.compile(rf"inscri[çc][õo]es[^.\n]{{0,180}}?(?P<sd>\d{{1,2}})\s+de\s+(?P<sm>{MONTHS})\s+a\s+(?P<ed>\d{{1,2}})\s+de\s+(?P<em>{MONTHS})\s+de\s+(?P<year>\d{{4}})", re.I)
        proof = re.compile(rf"prova\s+est[aá]\s+prevista\s+para\s+ser\s+realizada\s+em\s+(?P<date>{LONG_DATE})", re.I)
    else:
        raise RuntimeError(f"fonte sem padrão explícito: {source}")
    return registration, proof


def _registration_dates(source: str, pages):
    pattern, _ = _source_patterns(source)
    found = []
    for page in pages:
        for match in pattern.finditer(page.text):
            if source in {"legatus_open", "facet_open"}:
                year = match["year"]
                start = _iso_short(match["sd"], match["sm"], year)
                end = _iso_short(match["ed"], match["em"], year)
            elif source == "funvapi_open" or source == "fgv_open":
                start = _iso_long(match["start"])
                end = _iso_long(match["end"])
            else:
                start = _date_value(match["start"])
                end = _date_value(match["end"])
            if start and end and start <= end:
                found.append((page, start, end, match.group(0)))
    pairs = {(start, end) for _, start, end, _ in found}
    if len(pairs) != 1:
        raise RuntimeError(f"{source}: período de inscrição ausente ou divergente: {sorted(pairs)!r}")
    page, start, end, snippet = found[0]
    return page, start, end, snippet


def _proof_date(source: str, pages):
    _, pattern = _source_patterns(source)
    found = []
    for page in pages:
        for match in pattern.finditer(page.text):
            raw = match["date"]
            value = _date_value(raw.replace(".", "/")) if ("/" in raw or "." in raw) else _iso_long(raw)
            if value:
                found.append((page, value, match.group(0)))
    values = {value for _, value, _ in found}
    if len(values) != 1:
        raise RuntimeError(f"{source}: data de prova ausente ou divergente: {sorted(values)!r}")
    return found[0]


def _replace_date_fields(fields, source, artifact, pages):
    fmap = {field.field_name: field for field in fields}
    page_map = {page.page_number: page.text for page in pages}
    date_evidence = {}
    for name in ("inscricao_inicio", "inscricao_fim", "prova_data"):
        field = fmap[name]
        expected = EXPECTED[source][name]
        if field.state != FieldState.SUPPORTED or field.value != expected or not field.evidence:
            raise RuntimeError(f"{source}: fields.py não reproduziu {name}: {field.value!r}")
        for item in field.evidence:
            if item.page_number not in page_map or not item.snippet or item.snippet not in page_map[item.page_number]:
                raise RuntimeError(f"{source}: evidência inválida para {name}")
        item = field.evidence[0]
        date_evidence[name] = {"page": item.page_number, "snippet": item.snippet, "value": field.value}
    return fields, date_evidence


def evidence_fields(run):
    return [
        {
            "field": field.field_name,
            "state": field.state.value,
            "value": field.value,
            "reason": field.reason,
            "evidence": [
                {"page": item.page_number, "sha256": item.document_sha256, "snippet": " ".join((item.snippet or "").split())[:620]}
                for item in field.evidence[:4]
            ],
        }
        for field in run.fields
    ]


def reextract(original, store):
    if original is None or original.artifact is None or original.document is None:
        raise RuntimeError("run original/artifact/document ausente")
    content = store.load_artifact_bytes(original.artifact)
    digest = hashlib.sha256(content).hexdigest()
    if digest != original.artifact.sha256:
        raise RuntimeError(f"hash divergente em {original.run_id}")
    pages, total, processed, truncated, errors = extract_pages_isolated(
        content,
        artifact_id=original.artifact.artifact_id,
        owner_id=str(original.owner_user_id),
        max_bytes=max(len(content), 30 * 1024 * 1024),
        max_pages=200,
        reuse_completed=True,
    )
    if truncated or errors or total != processed:
        raise RuntimeError(f"extração incompleta em {original.run_id}")
    candidate = next(c for c in original.candidates if c.candidate_id == original.selected_candidate_id)
    validation = validate_identity(
        candidate=candidate,
        pages=pages,
        document_title=original.document.title,
        document_url=original.document.url_final or original.document.url_requested,
        document_kind=original.document.kind,
    )
    if validation.status.value != "valid":
        raise RuntimeError(f"identidade inválida em {original.run_id}: {validation.status.value}")
    fields = extract_fields(candidate=candidate, artifact=original.artifact, pages=pages)
    fields, date_evidence = _replace_date_fields(fields, original.source, original.artifact, pages)
    fmap = {field.field_name: field for field in fields}
    for field_name, expected in EXPECTED[original.source].items():
        if fmap[field_name].value != expected:
            raise RuntimeError(f"{original.source} {field_name} inesperado: {fmap[field_name].value!r}")
    now = datetime.now(timezone.utc)
    new_run = original.model_copy(deep=True, update={
        "run_id": new_run_id(),
        "execution_status": ExecutionStatus.COMPLETED,
        "validation_status": validation.status,
        "comparison_status": "pending",
        "comparison": ComparisonResult(),
        "total_pages": total,
        "processed_pages": processed,
        "truncated": truncated,
        "page_errors": errors,
        "fields": fields,
        "validation": validation,
        "semantic_hash": semantic_hash(fields),
        "diagnostics": [*original.diagnostics, f"reextract_of={original.run_id}; literal six-source date evidence"],
        "created_at": now,
        "updated_at": now,
    })
    return original, new_run, date_evidence


def proposal(db, run, store):
    user = db.get(User, run.owner_user_id)
    if user is None:
        raise RuntimeError("owner ausente")
    publication.authorize(user)
    result = publication.create_proposal(db, run=run, user=user, store=store, authorization=AUTHORIZATION)
    return {
        "id": result["id"],
        "proposal_hash": result["proposal_hash"],
        "state": result["state"],
        "action": result["action"],
        "source": run.source,
        "run_id": run.run_id,
        "eligible_fields": result.get("eligible_fields"),
        "blocked_fields": result.get("blocked_fields"),
        "authorization": result.get("authorization"),
    }


def main():
    store = get_store()
    pairs = {}
    evidence = {}
    for source, run_id in TARGETS.items():
        original, new_run, date_evidence = reextract(store.get_run(run_id), store)
        pairs[source] = (original, new_run)
        evidence[source] = date_evidence
    for _, new_run in pairs.values():
        store.put_run(new_run)
    with SessionLocal() as db:
        proposals = [proposal(db, pairs[source][1], store) for source in TARGETS]
    report = {
        "generated_at": "2026-09-09",
        "method": "normal_reextract_preserved_pdf_new_run_then_create_proposal",
        "publication_performed": False,
        "approval_performed": False,
        "application_performed": False,
        "authorization": AUTHORIZATION,
        "original_runs_preserved": True,
        "runs": {
            source: {
                "original_run_id": pairs[source][0].run_id,
                "new_run_id": pairs[source][1].run_id,
                "source": pairs[source][1].source,
                "artifact_sha256": pairs[source][1].artifact.sha256,
                "pages": pairs[source][1].processed_pages,
                "validation_status": pairs[source][1].validation_status.value,
                "fields": evidence_fields(pairs[source][1]),
                "date_evidence": evidence[source],
            }
            for source in TARGETS
        },
        "proposals": proposals,
        "real_gaps": [
            "As seis propostas estão proposed; root deve revisar/aprovar/aplicar separadamente.",
            "As identidades, números dos editais, inscrições e datas previstas de prova foram confirmados nos trechos literais indicados; o edital FUNCERN é a versão atualizada pelas retificações listadas na p.1.",
            "Cargos não foram inventados; os quadros de cargos permanecem fora do merge canônico desta rodada.",
            "Remuneração permanece bloqueada quando observada por cargo, pois o merge global não é seguro.",
            "Não há pendência documental de aquisição neste lote; as propostas usam os bytes preservados dos seis editais.",
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "proposals": [{"source": p["source"], "id": p["id"], "state": p["state"]} for p in proposals]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
