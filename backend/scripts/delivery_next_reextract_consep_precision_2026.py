"""Re-extract a preserved CONSEP 2026 edital with precise timing.

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
from app.tenderproof.continuous_store import get_continuous_store
from app.tenderproof.validation import validate_identity


ROOT = Path("/var/lib/observador/tenderproof")
OUTPUT = ROOT / "product-completion/delivery-next-reextract-consep-precision-v3-20260909.json"
TARGETS = {
    "consep_open": "tp-tcj-b38a9dcfdada5ee19dd857d2e0589df3-1",
}
EXPECTED = {
    "consep_open": {
        "titulo": "PROCESSO SELETIVO SIMPLIFICADO - SEBASTIÃO LEAL - PI",
        "orgao": "Prefeitura Municipal De Sebastião Leal",
        "edital_numero": "001/2026",
        "inscricao_inicio": "2026-01-12",
        "inscricao_fim": "2026-01-19",
        "prova_data": "2026-02-01",
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


MODALITY_PATTERNS = {
    "consep_open": re.compile(r"inscri[çc][õo]es\s+ser[aã]o\s+feitas\s+exclusivamente\s+pela\s+internet", re.I),
}
SELECTION_PATTERNS = {
    "consep_open": re.compile(r"PROCESSO\s+SELETIVO\s+SIMPLIFICADO\s+DE\s+PROVAS\s+E\s+T[IÍ]TULOS", re.I),
}


def modality_evidence(source, pages):
    result = {}
    for kind, pattern in (("registration", MODALITY_PATTERNS[source]), ("selection", SELECTION_PATTERNS[source])):
        for page in pages:
            match = pattern.search(page.text)
            if match:
                result[kind] = {
                    "state": "supported",
                    "page": page.page_number,
                    "snippet": " ".join(match.group(0).split()),
                    "snippet_verbatim": match.group(0),
                }
                break
        if kind not in result:
            raise RuntimeError(f"{source}: modalidade {kind} não corroborada")
    return result


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
    review = get_continuous_store().review_for_run(original)
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
        "diagnostics": [*original.diagnostics, f"reextract_of={original.run_id}; literal three-source date/proof evidence"],
        "created_at": now,
        "updated_at": now,
    })
    return original, new_run, date_evidence, modality_evidence(original.source, pages), review


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
    modalities = {}
    reviews = {}
    for source, run_id in TARGETS.items():
        original, new_run, date_evidence, modality, review = reextract(store.get_run(run_id), store)
        pairs[source] = (original, new_run, review)
        evidence[source] = date_evidence
        modalities[source] = modality
        reviews[source] = {"pending": bool(review.get("pending")), "documents": review.get("documents", [])}
    for _, new_run, review in pairs.values():
        if not review.get("pending"):
            store.put_run(new_run)
    with SessionLocal() as db:
        proposals = [proposal(db, pairs[source][1], store) for source in TARGETS if not pairs[source][2].get("pending")]
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
                "stored": not bool(pairs[source][2].get("pending")),
                "source": pairs[source][1].source,
                "artifact_sha256": pairs[source][1].artifact.sha256,
                "pages": pairs[source][1].processed_pages,
                "validation_status": pairs[source][1].validation_status.value,
                "fields": evidence_fields(pairs[source][1]),
                "date_evidence": evidence[source],
                "modality_evidence": modalities[source],
                "document_review": reviews[source],
            }
            for source in TARGETS
        },
        "proposals": proposals,
        "blocked_sources": [
            {
                "source": source,
                "run_id": pairs[source][0].run_id,
                "reason": pairs[source][2].get("reason"),
                "documents": [
                    {"kind": item.get("kind"), "title": item.get("title")}
                    for item in pairs[source][2].get("documents", [])
                ],
            }
            for source in TARGETS if pairs[source][2].get("pending")
        ],
        "real_gaps": [
            "A proposta de precisão está proposed; root deve revisar/aprovar/aplicar separadamente.",
            "As identidades, modalidade do processo seletivo e da inscrição, períodos e datas de prova foram confirmados nos trechos literais indicados.",
            "Cargos não foram inventados; os quadros de cargos permanecem fora do merge canônico desta rodada.",
            "Remuneração permanece bloqueada quando observada por cargo, pois o merge global não é seguro.",
            "Não há pendência documental de aquisição; a proposta usa os bytes preservados do edital CONSEP.",
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "proposals": [{"source": p["source"], "id": p["id"], "state": p["state"]} for p in proposals]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
