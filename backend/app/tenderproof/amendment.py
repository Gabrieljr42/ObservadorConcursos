"""Controlled application of field changes published by a later notice.

An amendment is deliberately kept separate from document-effect review.  The
review says *what* a later document changes; this module records the identity
of both documents, the exact field values and their evidence, and applies the
approved delta through the existing publication/version ledger.

The module does not infer changes from a title.  Callers must provide the
previous value, the new value, and a provenance item for every changed field.
Dates that contain a time must carry an explicit UTC offset.  The JSON payload
keeps the original period, re-openings and event schedule even though the
canonical catalogue has only a few date columns.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import unicodedata
from contextlib import contextmanager
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlsplit

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError, OperationalError

from app.models import Concurso, ConcursoVersion, Source
from app.tenderproof.contracts import Artifact, TenderProofRun
from app.tenderproof.processing import ProcessingError, extract_pages_isolated
from app.tenderproof.security import TenderProofSettings
from app.tenderproof.publication_models import PublicationOutbox, PublicationProposal
from app.versioning import VERSIONED_FIELDS, jsonable


EVENT_CHANGE_FIELDS = frozenset({"etapas_prova", "resultado_final_prazo", "entrega_titulos_prazo"})
AMENDABLE_FIELDS = frozenset({"inscricao_inicio", "inscricao_fim", "prova_data", "cargos"}) | EVENT_CHANGE_FIELDS
_DATE_FIELDS = frozenset({"inscricao_inicio", "inscricao_fim", "prova_data"})
_LABELS = {
    "inscricao_inicio": "início das inscrições",
    "inscricao_fim": "fim das inscrições",
    "prova_data": "data da prova",
    "etapas_prova": "etapas da prova",
    "resultado_final_prazo": "prazo do resultado final",
    "entrega_titulos_prazo": "prazo da entrega de títulos",
    "cargos": "dados por cargo",
}
_MISSING = object()


def _error(status: int, message: str) -> None:
    raise HTTPException(status_code=status, detail=message)


def authorize(user) -> None:
    """Use the same explicit publisher allow-list as ordinary publication."""
    allowed = {item.strip() for item in os.getenv("TENDERPROOF_PUBLISHER_USER_IDS", "").split(",") if item.strip()}
    if not user or not getattr(user, "is_active", False) or str(user.id) not in allowed:
        _error(403, "TenderProof: usuário sem permissão de revisão/publicação")


def _json(value: Any) -> Any:
    """Return stable JSON values, including aware datetimes."""
    return jsonable(value)


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_json(value), sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def _aware(value: Any, field: str) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, str):
        try:
            result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            _error(422, f"Retificação: valor inválido para {field}")
            raise AssertionError from exc
    else:
        _error(422, f"Retificação: valor inválido para {field}")
    if result.tzinfo is None or result.utcoffset() is None:
        _error(422, f"Retificação: {field} exige data/hora com fuso explícito")
    return result


def _value(field: str, value: Any) -> Any:
    if field in _DATE_FIELDS:
        # prova_data may be date-only in the canonical model.  Keep a date-only
        # value as a date; times belong in the separately preserved events.
        if isinstance(value, str) and len(value) == 10:
            try:
                return date.fromisoformat(value).isoformat()
            except ValueError:
                _error(422, f"Retificação: valor inválido para {field}")
        return _aware(value, field).isoformat() if value is not None else None
    return _json(value)


def _same_value(field: str, left: Any, right: Any) -> bool:
    if field in _DATE_FIELDS:
        if left is None or right is None:
            return left is None and right is None
        if isinstance(left, str) and len(left) == 10 and isinstance(right, datetime):
            return right.date().isoformat() == left
        if isinstance(right, str) and len(right) == 10 and isinstance(left, datetime):
            return left.date().isoformat() == right
        # SQLite returns naive datetimes after a round trip.  Compare the
        # instant when both values are datetimes; retain date-only semantics.
        try:
            l = datetime.fromisoformat(left.replace("Z", "+00:00")) if isinstance(left, str) else left
            r = datetime.fromisoformat(right.replace("Z", "+00:00")) if isinstance(right, str) else right
            if isinstance(l, datetime) and isinstance(r, datetime):
                # SQLite drops timezone metadata from DateTime(timezone=True).
                # Preserve explicit offsets in the proposal, while comparing a
                # round-tripped canonical value by its recorded wall time.
                if l.tzinfo is None or r.tzinfo is None:
                    return l.replace(tzinfo=None) == r.replace(tzinfo=None)
                return l.astimezone(timezone.utc) == r.astimezone(timezone.utc)
        except (TypeError, ValueError):
            return False
    return _json(left) == _json(right)


def _event_current_value(contest: Concurso, field: str) -> Any:
    """Read an event-only field from the amendment ledger, if one exists."""
    if field not in EVENT_CHANGE_FIELDS:
        return getattr(contest, field, _MISSING)
    for version in sorted(getattr(contest, "versions", []) or [], key=lambda item: item.id or 0, reverse=True):
        change = (version.changed_fields or {}).get(field)
        if isinstance(change, dict) and "new" in change:
            return change["new"]
    for entry in reversed(((contest.raw_data or {}).get("tenderproof", {}) or {}).get("amendments", []) or []):
        change = (entry.get("changes") or {}).get(field) if isinstance(entry, dict) else None
        if isinstance(change, dict) and "new" in change:
            return change["new"]
    return _MISSING


def _revision(db, contest: Concurso) -> dict[str, Any]:
    return {
        "values": {name: _json(getattr(contest, name)) for name in VERSIONED_FIELDS},
        "latest_version_id": db.scalar(select(func.max(ConcursoVersion.id)).where(ConcursoVersion.concurso_id == contest.id)),
        "source_id": contest.source_id,
        "external_id": contest.external_id,
        "link_pagina": contest.link_pagina,
    }


def _same_url(left: str | None, right: str | None) -> bool:
    def canonical(value: str | None) -> str:
        parsed = urlsplit(value or "")
        return "://".join([parsed.scheme.lower(), parsed.netloc.lower()]) + parsed.path.rstrip("/") + ("?" + parsed.query if parsed.query else "")
    return canonical(left) == canonical(right)


def _case_row(qdb, case_id: str, owner: int) -> dict[str, Any]:
    exists = qdb.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='document_effect_cases'").fetchone()
    row = qdb.execute("SELECT * FROM document_effect_cases WHERE id=? AND owner=?", (case_id, owner)).fetchone() if exists else None
    if not row:
        _error(409, "Retificação: revisão documental não encontrada")
    payload = json.loads(row["payload"])
    payload.update({"id": row["id"], "run_id": row["run_id"], "approved_at": row["approved_at"],
                    "decisions": json.loads(row["decisions"]) if row["decisions"] else None})
    if row["approved_at"] is None:
        _error(409, "Retificação: revisão documental ainda não foi aprovada")
    return payload


def _run_contest_identity(run: TenderProofRun, contest: Concurso) -> None:
    candidate = next((item for item in run.candidates if item.candidate_id == run.selected_candidate_id), None)
    if (run.owner_user_id is None or not candidate or candidate.source != run.source
            or not candidate.external_id or candidate.external_id != contest.external_id
            or not _same_url(candidate.detail_url_observed, contest.link_pagina)):
        _error(422, "Retificação: run não identifica o mesmo concurso, fonte e página oficial")
    if contest.source and contest.source.source_type != run.source:
        _error(422, "Retificação: fonte do run não corresponde ao concurso")


def _initial_identity(db, run: TenderProofRun, source_id: int | None = None) -> dict[str, Any]:
    """Build the identity for a reviewed initial publication.

    A composed proposal may precede the first ``Concurso`` row.  The source,
    external id and URL still come from the selected run candidate, while the
    notice number and authority must come from extracted run fields.  They are
    corroborated against both preserved PDFs before a proposal is persisted.
    """
    candidate = next((item for item in run.candidates if item.candidate_id == run.selected_candidate_id), None)
    sources = list(db.scalars(select(Source).where(Source.source_type == run.source)))
    if source_id is not None:
        sources = [source for source in sources if source.id == source_id]
    if not candidate or not candidate.external_id or not candidate.detail_url_observed or len(sources) != 1:
        _error(422, "Retificação: run inicial não identifica fonte, concurso e página oficial sem ambiguidade")
    values = {field.field_name: field.value for field in run.fields}
    required = {name: values.get(name) for name in ("titulo", "orgao", "edital_numero")}
    if not all(isinstance(value, str) and value.strip() for value in required.values()):
        _error(422, "Retificação: criação inicial exige título, órgão e número do edital extraídos do run")
    return {
        "source_id": sources[0].id,
        "banca": sources[0].name,
        "external_id": candidate.external_id,
        "edital_numero": required["edital_numero"],
        "orgao": required["orgao"],
        "titulo": required["titulo"],
        "detail_url": candidate.detail_url_observed,
        "reason": "new_verified_identity",
    }


def _initial_fields(run: TenderProofRun, documents: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Re-extract useful base fields for explicit approval at initial apply."""
    from app.tenderproof.fields import extract_fields
    from app.tenderproof.selection_scope import document_scope
    from app.tenderproof.source_adapters import get_source_adapter
    from app.tenderproof.validation import validate_identity

    candidate = next((item for item in run.candidates if item.candidate_id == run.selected_candidate_id), None)
    item = documents.get(run.artifact.sha256 if run.artifact else "")
    if not candidate or not item or not run.document or not run.artifact:
        _error(422, "Retificação: run inicial sem documento selecionado para revalidação")
    try:
        adapter = get_source_adapter(run.source)
        adapter.validate_detail_url(candidate.detail_url_observed)
        expected_candidate = adapter.candidate_from_url(candidate.detail_url_observed, candidate.title_observed)
        if expected_candidate.external_id != candidate.external_id:
            _error(422, "Retificação: identificador do candidato não corresponde à URL oficial")
        for url in (run.document.url_requested, run.artifact.url_requested, run.artifact.url_final):
            adapter.validate_document_url(url, candidate)
    except Exception:
        _error(422, "Retificação: URL da fonte ou documento inicial não passou na validação do adaptador")
    pages = item.get("page_objects") or []
    if document_scope(run.source, run.artifact, pages):
        _error(422, "Retificação: documento inicial está fora do escopo de edital")
    identity = validate_identity(candidate=candidate, pages=pages, document_title=run.document.title,
                                 document_url=run.artifact.url_final, document_kind=run.document.kind)
    if identity.status.value != "valid":
        _error(422, "Retificação: identidade do documento inicial não foi revalidada")
    fresh_fields = extract_fields(candidate=candidate, artifact=run.artifact, pages=pages)
    if run.source == "legalle_open":
        from app.tenderproof.legalle_jobs import extract_fields as extract_legalle_fields
        replacements = {field.field_name: field for field in extract_legalle_fields(
            run.artifact, pages, lambda **kwargs: __import__("app.tenderproof.fields", fromlist=["_evidence"])._evidence(**kwargs),
            source=run.source, external_id=candidate.external_id)}
        fresh_fields = [replacements.get(field.field_name, field) for field in fresh_fields]
        fresh_fields.extend(field for name, field in replacements.items()
                            if not any(existing.field_name == name for existing in fresh_fields))
    result = {}
    page_text = item.get("pages") or {}
    for field in fresh_fields:
        if field.field_name not in VERSIONED_FIELDS or field.value is None:
            continue
        if field.state.value != "supported" or not field.validation.ok:
            continue
        evidence = [item.model_dump(mode="json") for item in field.evidence]
        if not evidence or any(not proof.get("snippet") or proof.get("snippet") not in page_text.get(proof.get("page_number"), "")
                               or proof.get("document_sha256") != run.artifact.sha256
                               or not _same_url(proof.get("source_url"), run.artifact.url_final)
                               for proof in evidence):
            continue
        result[field.field_name] = {
            "value": _json(field.value),
            "state": field.state.value,
            "evidence": evidence,
        }
    return result


def _initial_fields_match(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Compare revalidation by values and evidence, ignoring serialization noise."""
    if set(left) != set(right):
        return False
    def evidence_key(item):
        return (item.get("document_sha256"), item.get("page_number"), item.get("snippet"), item.get("source_url"))
    for name in left:
        if left[name].get("state") != right[name].get("state") or _json(left[name].get("value")) != _json(right[name].get("value")):
            return False
        if {evidence_key(item) for item in left[name].get("evidence", [])} != {evidence_key(item) for item in right[name].get("evidence", [])}:
            return False
    return True


def _assert_initial_run_identity(run: TenderProofRun, identity: dict[str, Any]) -> None:
    candidate = next((item for item in run.candidates if item.candidate_id == run.selected_candidate_id), None)
    if (not candidate or candidate.source != run.source or candidate.external_id != identity.get("external_id")
            or not _same_url(candidate.detail_url_observed, identity.get("detail_url"))):
        _error(422, "Retificação: run inicial não corresponde à identidade documental apresentada")


def _case_documents(case: dict[str, Any], queue, store, run: TenderProofRun) -> dict[str, dict[str, Any]]:
    """Re-read every preserved artifact while the queue write lock is held."""
    settings = TenderProofSettings.from_env()
    result: dict[str, dict[str, Any]] = {}
    for document in case.get("documents", []):
        artifact = Artifact.model_validate(document["artifact"])
        content = store.load_artifact_bytes(artifact)
        if content is None or hashlib.sha256(content).hexdigest() != artifact.sha256 or len(content) != artifact.byte_len:
            _error(409, "Retificação: bytes preservados ausentes ou divergentes")
        try:
            pages, total, processed, truncated, errors = extract_pages_isolated(
                content, artifact_id=artifact.artifact_id, owner_id=str(run.owner_user_id),
                max_pages=settings.limits.max_pages, max_bytes=settings.limits.max_download_bytes,
                capacity_wait_s=15, reuse_completed=True)
        except ProcessingError as exc:
            _error(409, f"Retificação: revalidação do documento falhou ({exc})")
        if truncated or errors or total != processed or not pages:
            _error(409, "Retificação: extração revalidada incompleta")
        result[artifact.sha256] = {"document": document, "artifact": artifact, "content": content,
                                  "pages": {page.page_number: page.text for page in pages},
                                  "page_objects": pages}
    if not result:
        _error(409, "Retificação: revisão sem documentos preservados")
    return result


def _assert_review_current(qdb, queue, run: TenderProofRun, case: dict[str, Any], case_id: str, *, allow_finalized=False) -> None:
    from app.tenderproof import review_cases
    if case.get("run_id") != run.run_id or case.get("identity") != list(review_cases.identity(run)):
        _error(409, "Retificação: revisão não pertence ao run e à identidade apresentados")
    if case.get("extraction_method_version") != review_cases.METHOD_VERSION:
        _error(409, "Retificação: interpretação documental atualizada; prepare nova revisão")
    current = review_cases.revision(queue, run, qdb)
    if current != case.get("revision"):
        same_documents = (current.get("manifest") == case.get("revision", {}).get("manifest")
                          and current.get("artifact_sha256") == case.get("revision", {}).get("artifact_sha256")
                          and current.get("supplementary_documents", []) == case.get("revision", {}).get("supplementary_documents", []))
        if not (allow_finalized and same_documents and not current.get("pending")):
            _error(409, "Retificação: manifesto ou documentos mudaram; prepare nova revisão")
    approved = review_cases.approved_case(queue, run, qdb, allow_field_changes=True)
    if approved != case_id and not (allow_finalized and not current.get("pending")):
        _error(409, "Retificação: revisão aprovada não cobre o manifesto atual")


@contextmanager
def _review_context(queue, store, run: TenderProofRun, case_id: str, contest: Concurso | None,
                    *, initial_identity: dict[str, Any] | None = None, allow_finalized=False):
    if queue is None or store is None or not case_id:
        _error(422, "Retificação: queue, store e review_case_id são obrigatórios")
    if contest is not None:
        _run_contest_identity(run, contest)
    elif initial_identity is not None:
        _assert_initial_run_identity(run, initial_identity)
    else:
        _error(422, "Retificação: identidade inicial ausente")
    from app.tenderproof import review_cases
    with queue._db(write=True) as qdb:
        case = _case_row(qdb, case_id, run.owner_user_id)
        _assert_review_current(qdb, queue, run, case, case_id, allow_finalized=allow_finalized)
        documents = _case_documents(case, queue, store, run)
        yield case, documents, qdb


def _trusted_document(provided: dict[str, Any], documents: dict[str, dict[str, Any]], contest: Concurso | None,
                      *, identity: dict[str, Any] | None = None, role: str) -> dict[str, Any]:
    provided = provided if isinstance(provided, dict) else {}
    artifact_input = provided.get("artifact") if isinstance(provided.get("artifact"), dict) else {}
    document_input = provided.get("document") if isinstance(provided.get("document"), dict) else {}
    sha = provided.get("sha256") or artifact_input.get("sha256")
    item = documents.get(sha)
    if not item:
        _error(409, f"Retificação: {role} não pertence à revisão documental aprovada")
    manifest = item["document"].get("document") or item["document"]
    artifact = item["artifact"]
    allowed_urls = {manifest.get("url_requested"), manifest.get("url_final"), artifact.url_requested, artifact.url_final}
    supplied_url = provided.get("url") or provided.get("url_final") or artifact_input.get("url_final") or artifact_input.get("url_requested") or document_input.get("url_requested")
    if supplied_url not in allowed_urls:
        _error(409, f"Retificação: URL do {role} não corresponde ao manifesto preservado")
    expected = identity or _identity(contest)
    supplied_identity = provided.get("identity") or document_input.get("identity")
    if supplied_identity and (supplied_identity.get("source_id") != expected.get("source_id")
                              or supplied_identity.get("external_id") != expected.get("external_id")
                              or supplied_identity.get("edital_numero") != expected.get("edital_numero")):
        _error(422, f"Retificação: identidade enviada para {role} não corresponde ao concurso")
    return {"sha256": artifact.sha256, "url": artifact.url_final or artifact.url_requested,
            "title": manifest.get("title"), "kind": manifest.get("kind"),
            "identity": {"source_id": expected.get("source_id"), "external_id": expected.get("external_id"),
                         "edital_numero": expected.get("edital_numero")}}


def _assert_provenance_in_pages(changes: dict[str, Any], events: list[dict[str, Any]], documents: dict[str, dict[str, Any]]) -> None:
    for group in [*changes.values(), *events]:
        for provenance in group.get("provenance", []):
            item = documents.get(provenance.get("sha256"))
            text = item["pages"].get(provenance.get("page")) if item else None
            if not text or provenance.get("snippet") not in text:
                _error(422, "Retificação: trecho literal não foi reproduzido nos bytes revalidados")


def _fold(value: Any) -> str:
    return unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode().casefold()


def _assert_identity_text(document: dict[str, Any], documents: dict[str, dict[str, Any]], contest: Concurso | None = None,
                          *, identity: dict[str, Any] | None = None) -> None:
    item = documents.get(document["sha256"])
    text = "\n".join(item["pages"].values()) if item else ""
    folded = _fold(text)
    expected = identity or _identity(contest)
    number = _fold(expected.get("edital_numero")).strip()
    number_pattern = re.escape(number).replace("/", r"\s*/\s*")
    if not number or not re.search(rf"(?<!\d){number_pattern}(?!\d)", folded):
        _error(422, "Retificação: número do edital não foi corroborado no texto preservado")
    from app.tenderproof.validation import distinctive_title_words
    distinctive = distinctive_title_words(expected.get("orgao") or "")
    if distinctive and not all(re.search(rf"\b{re.escape(_fold(word))}\b", folded) for word in distinctive):
        _error(422, "Retificação: órgão do concurso não foi corroborado no texto preservado")


def _assert_review_changes_bound(case: dict[str, Any], changes: dict[str, Any]) -> None:
    decisions = case.get("decisions") or []
    review_changes = {item.get("field_name"): item
                      for decision in decisions if decision.get("effect") == "field_changes"
                      for item in (decision.get("changes") or []) if isinstance(item, dict)}
    for name, change in changes.items():
        item = review_changes.get(name)
        if not item or "previous" not in item or "new" not in item or not item.get("provenance"):
            _error(409, f"Retificação: revisão não vincula valores e proveniência do campo {name}")
        if _value(name, item.get("previous")) != change.get("previous") or _value(name, item.get("new")) != change.get("new"):
            _error(409, f"Retificação: valores do campo {name} divergem da revisão aprovada")
        review_provenance = item.get("provenance")
        if isinstance(review_provenance, dict):
            review_provenance = [review_provenance]
        if not any((p.get("sha256") or p.get("document_sha256")) == ev.get("sha256")
                   and p.get("page", p.get("page_number")) == ev.get("page")
                   and p.get("snippet") == ev.get("snippet") for p in review_provenance for ev in change.get("provenance", [])):
            _error(409, f"Retificação: proveniência do campo {name} diverge da revisão aprovada")


def _assert_temporal_coherence(payload: dict[str, Any], selected: list[str]) -> None:
    periods = payload.get("periods") or {}
    changes = payload["changes"]
    original = periods.get("original") or {}
    for key, field in (("start", "inscricao_inicio"), ("end", "inscricao_fim")):
        if original.get(key) is not None:
            if field not in selected or not _same_value(field, original[key], changes[field]["previous"]):
                _error(422, "Retificação: período original não coincide com o valor anterior aprovado")
    current = periods.get("current") or {}
    for key, field in (("start", "inscricao_inicio"), ("end", "inscricao_fim")):
        if current.get(key) is not None:
            if field not in selected or not _same_value(field, current[key], changes[field]["new"]):
                _error(422, "Retificação: período vigente não coincide com os campos aprovados")
    for reopening in periods.get("reopenings", []):
        for key, field in (("start", "inscricao_inicio"), ("end", "inscricao_fim")):
            if reopening.get(key) is not None and (field not in selected or not _same_value(field, reopening[key], changes[field]["new"])):
                _error(422, "Retificação: reabertura não coincide com o novo período aprovado")
    for event in payload.get("events", []):
        event_name = re.sub(r"[^a-z]", "", _fold(event.get("name", "")))
        if event_name in {"prova", "provaobjetiva"}:
            if "prova_data" not in selected or not _same_value("prova_data", event.get("date"), changes["prova_data"]["new"]):
                _error(422, "Retificação: evento de prova não coincide com o campo aprovado")
    event_aliases = {
        "resultado_final_prazo": ("resultadofinal",),
        "entrega_titulos_prazo": ("titulosprazo",),
    }
    for field, aliases in {**event_aliases, "etapas_prova": ()}.items():
        if field not in selected:
            continue
        def matches_field(event: dict[str, Any]) -> bool:
            name = re.sub(r"[^a-z]", "", _fold(event.get("name", "")))
            if field == "etapas_prova":
                return "etapas" in name and "prova" in name
            if field == "entrega_titulos_prazo":
                return "entrega" in name and "titulo" in name or any(alias in name for alias in aliases)
            return any(alias in name for alias in aliases)
        matches = [event for event in payload.get("events", []) if matches_field(event)]
        if not matches:
            _error(422, f"Retificação: evento comprovado ausente para {field}")
        expected = changes[field]["new"]
        matched = False
        for event in matches:
            observed = event.get("value")
            if field in {"resultado_final_prazo", "entrega_titulos_prazo"}:
                observed = event.get("date", observed)
                if isinstance(observed, str) and isinstance(expected, str):
                    matched = observed[:10] == expected[:10]
                else:
                    matched = _same_value(field, observed, expected)
            else:
                matched = _fold(observed).strip() == _fold(expected).strip()
            if matched:
                break
        if not matched:
            _error(422, f"Retificação: evento comprovado não coincide com {field}")


def _known_document_hashes(contest: Concurso) -> set[str]:
    found: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"sha256", "document_sha256", "artifact_sha256", "base_document_sha256"} and isinstance(child, str):
                    found.add(child)
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(contest.raw_data or {})
    for version in contest.versions:
        visit(version.raw_data_snapshot or {})
    if contest.edital_pdf_text_hash:
        found.add(contest.edital_pdf_text_hash)
    return found


def _identity(contest: Concurso) -> dict[str, Any]:
    return {"source_id": contest.source_id, "external_id": contest.external_id,
            "edital_numero": contest.edital_numero, "concurso_id": contest.id}


def _assert_document(document: dict[str, Any], contest: Concurso | None = None, *, identity: dict[str, Any] | None = None,
                     role: str) -> dict[str, Any]:
    if not isinstance(document, dict):
        _error(422, f"Retificação: {role} deve ser um objeto documental")
    sha = document.get("sha256")
    url = document.get("url") or document.get("url_final") or document.get("source_url")
    if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha.lower()):
        _error(422, f"Retificação: SHA-256 do {role} é obrigatório")
    if not isinstance(url, str) or not urlsplit(url).scheme or not urlsplit(url).netloc:
        _error(422, f"Retificação: URL comprovada do {role} é obrigatória")
    expected = identity or _identity(contest)
    document_identity = document.get("identity") or document
    if document_identity.get("source_id") != expected.get("source_id") or document_identity.get("external_id") != expected.get("external_id"):
        _error(422, f"Retificação: {role} pertence a outra fonte ou concurso")
    if document_identity.get("edital_numero") != expected.get("edital_numero"):
        _error(422, f"Retificação: edital-base não corresponde ao concurso selecionado")
    result = dict(document)
    result["sha256"] = sha.lower()
    result["url"] = url
    result["identity"] = {"source_id": expected.get("source_id"), "external_id": expected.get("external_id"),
                           "edital_numero": expected.get("edital_numero")}
    if role == "base" and contest is not None and sha not in _known_document_hashes(contest):
        _error(409, "Retificação: SHA do edital-base não está ligado à evidência preservada do concurso")
    return _json(result)


def _authorization(value: dict[str, Any] | None, *, required: bool = True) -> dict[str, Any] | None:
    if value is None:
        if required:
            _error(422, "Retificação: autorização de revisão delegada é obrigatória")
        return None
    if not isinstance(value, dict):
        _error(422, "Retificação: autorização deve ser um objeto")
    actor = value.get("actor_kind")
    if actor not in {"delegated_automation", "human_reviewer"}:
        _error(422, "Retificação: actor_kind deve identificar automação delegada ou revisor")
    if actor == "delegated_automation" and value.get("human_read", False):
        _error(422, "Retificação: automação delegada não pode alegar leitura humana")
    reference = value.get("delegation_reference") or value.get("reference")
    reference_hash = value.get("delegation_sha256") or value.get("reference_sha256")
    if (not isinstance(reference, str) or not reference.strip()
            or not isinstance(reference_hash, str) or len(reference_hash) != 64
            or any(char not in "0123456789abcdefABCDEF" for char in reference_hash)):
        _error(422, "Retificação: referência e SHA da autorização são obrigatórios")
    result = dict(value)
    result.update({"actor_kind": actor, "human_read": bool(value.get("human_read", False)),
                   "delegation_reference": reference.strip(), "delegation_sha256": reference_hash.lower()})
    return _json(result)


def normalize_authorization(value: dict[str, Any] | None, *, required: bool = True) -> dict[str, Any] | None:
    """Public compatibility helper for the ordinary publication approval API."""
    return _authorization(value, required=required)


def _provenance(item: dict[str, Any], amendment_sha: str | list[dict[str, Any]], amendment_url: str | None = None) -> dict[str, Any]:
    if not isinstance(item, dict):
        _error(422, "Retificação: proveniência inválida")
    sha = item.get("sha256") or item.get("document_sha256")
    page = item.get("page") if item.get("page") is not None else item.get("page_number")
    snippet = item.get("snippet")
    source_url = item.get("source_url") or item.get("url")
    if isinstance(amendment_sha, list):
        matched = next((document for document in amendment_sha if document.get("sha256") == sha), None)
        expected_sha = matched.get("sha256") if matched else None
        expected_url = matched.get("url") if matched else None
    else:
        expected_sha = amendment_sha
        expected_url = amendment_url
    if sha != expected_sha or not isinstance(page, int) or page < 1 or not isinstance(snippet, str) or len(snippet.strip()) < 8:
        _error(422, "Retificação: cada campo exige SHA, página e trecho literal do documento retificador")
    if source_url != expected_url:
        _error(422, "Retificação: URL da proveniência não corresponde ao documento retificador")
    return _json({**item, "sha256": expected_sha, "page": page, "snippet": snippet, "source_url": expected_url})


def _changes(changes: dict[str, Any] | list[dict[str, Any]], contest: Concurso | None,
             amendment: dict[str, Any] | list[dict[str, Any]]) -> dict[str, Any]:
    items = [{"field_name": key, **value} for key, value in changes.items()] if isinstance(changes, dict) else changes
    if not isinstance(items, list) or not items:
        _error(422, "Retificação: informe ao menos uma mudança de campo")
    result: dict[str, Any] = {}
    for item in items:
        if not isinstance(item, dict) or item.get("field_name") not in AMENDABLE_FIELDS:
            _error(422, "Retificação: campo fora do escopo de retificação suportado")
        name = item["field_name"]
        if name in result:
            _error(422, "Retificação: campo repetido")
        previous = _value(name, item.get("previous"))
        new = _value(name, item.get("new"))
        current = _event_current_value(contest, name) if contest is not None else _MISSING
        if current is not _MISSING and previous != current and not _same_value(name, previous, current):
            _error(409, f"Retificação: versão anterior de {name} não coincide com o catálogo atual")
        prov = item.get("provenance") or item.get("evidence")
        if isinstance(prov, dict):
            prov = [prov]
        if not isinstance(prov, list) or not prov:
            _error(422, f"Retificação: proveniência ausente para {name}")
        result[name] = {"field_name": name, "previous": previous, "new": new,
                        "label": _LABELS[name],
                        "provenance": [_provenance(p, amendment if isinstance(amendment, list) else amendment["sha256"],
                                                   None if isinstance(amendment, list) else amendment["url"]) for p in prov],
                        "reason": str(item.get("reason") or "").strip()}
        if len(result[name]["reason"]) < 10:
            _error(422, f"Retificação: motivo curto ou ausente para {name}")
    return result


def _validate_periods(periods: dict[str, Any] | None) -> dict[str, Any] | None:
    if periods is None:
        return None
    if not isinstance(periods, dict):
        _error(422, "Retificação: períodos devem ser um objeto")
    result = copy.deepcopy(periods)
    for key in ("original", "current"):
        value = result.get(key)
        if value is None:
            continue
        if not isinstance(value, dict):
            _error(422, f"Retificação: período {key} inválido")
        for date_key in ("start", "end"):
            if value.get(date_key) is not None:
                value[date_key] = _value("inscricao_inicio", value[date_key])
        has_time = any(isinstance(value.get(date_key), str) and "T" in value[date_key] for date_key in ("start", "end"))
        if has_time and not value.get("timezone"):
            _error(422, f"Retificação: fuso explícito ausente no período {key}")
        if not has_time:
            # A legacy date-only period is preserved as a day, without an
            # invented midnight or timezone.  New values with a time still
            # require the documented IANA/offset timezone above.
            value.setdefault("precision", "day")
            value.setdefault("timezone", None)
    reopenings = result.get("reopenings", [])
    if not isinstance(reopenings, list):
        _error(422, "Retificação: reaberturas devem ser uma lista")
    for reopening in reopenings:
        if not isinstance(reopening, dict):
            _error(422, "Retificação: reabertura exige fuso explícito")
        for date_key in ("start", "end"):
            if reopening.get(date_key) is not None:
                reopening[date_key] = _value("inscricao_inicio", reopening[date_key])
        has_time = any(isinstance(reopening.get(date_key), str) and "T" in reopening[date_key] for date_key in ("start", "end"))
        if has_time and not reopening.get("timezone"):
            _error(422, "Retificação: reabertura exige fuso explícito")
        if not has_time:
            reopening.setdefault("precision", "day")
            reopening.setdefault("timezone", None)
    return _json(result)


def _validate_events(events: list[dict[str, Any]] | None,
                     amendment: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep day precision and require the same evidence contract as fields."""
    if events is None:
        return []
    if not isinstance(events, list):
        _error(422, "Retificação: eventos devem ser uma lista")
    result = []
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("name"), str) or not event["name"].strip():
            _error(422, "Retificação: evento sem nome")
        value = event.get("date") or event.get("value")
        if value is None:
            _error(422, f"Retificação: evento {event['name']} sem data")
        # Event values may be descriptive text (for example, "Títulos").
        # Only an ISO date followed by a time marker is a timestamp here.
        if isinstance(value, str) and re.match(r"^\d{4}-\d{2}-\d{2}T", value):
            _aware(value, event["name"])
        provenance = event.get("provenance") or event.get("evidence")
        if isinstance(provenance, dict):
            provenance = [provenance]
        if not isinstance(provenance, list) or not provenance:
            _error(422, f"Retificação: proveniência ausente para o evento {event['name']}")
        result.append({**_json(event), "provenance": [_provenance(p, amendment if isinstance(amendment, list) else amendment["sha256"],
                                                                   None if isinstance(amendment, list) else amendment["url"]) for p in provenance]})
    return result


def create_proposal(db, *, concurso_id: int | None = None, user, base_document: dict[str, Any], amendment_document: dict[str, Any],
                    changes: dict[str, Any] | list[dict[str, Any]], reason: str, authorization: dict[str, Any] | None = None,
                    periods: dict[str, Any] | None = None, events: list[dict[str, Any]] | None = None,
                    amendment_documents: list[dict[str, Any]] | None = None,
                    run: TenderProofRun | None = None, queue=None, store=None, review_case_id: str | None = None,
                    run_id: str | None = None, case_id: str | None = None, review_hash: str | None = None,
                    source_id: int | None = None) -> dict[str, Any]:
    """Create an idempotent, reviewable amendment proposal.

    ``base_document`` and ``amendment_document`` must each carry ``sha256``,
    ``url`` and an identity object with source, external ID and edital number.
    ``changes`` is a map or list containing ``previous``, ``new`` and
    ``provenance`` (page, literal snippet, URL and the amendment SHA).
    """
    authorize(user)
    review_case_id = review_case_id or case_id
    if store is None:
        from app.tenderproof.store import get_store
        store = get_store()
    if queue is None:
        from app.tenderproof.continuous_store import get_continuous_store
        queue = get_continuous_store()
    if run is None and run_id:
        run = store.get_run(run_id)
    if run is None or not review_case_id:
        _error(422, "Retificação: run, queue, store e review_case_id são obrigatórios")
    if run.owner_user_id != user.id or (run_id is not None and run.run_id != run_id):
        _error(404, "Retificação: observação não pertence ao usuário")
    contest = db.get(Concurso, concurso_id) if concurso_id is not None else None
    if concurso_id is not None and not contest:
        _error(404, "Retificação: concurso não encontrado")
    if not isinstance(reason, str) or len(reason.strip()) < 10:
        _error(422, "Retificação: motivo obrigatório")
    authorization_value = _authorization(authorization)
    initial_identity = _initial_identity(db, run, source_id) if contest is None else None
    expected_identity = initial_identity or _identity(contest)
    with _review_context(queue, store, run, review_case_id, contest, initial_identity=initial_identity) as (case, documents, _qdb):
        if review_hash is not None and case["revision_hash"] != review_hash:
            _error(409, "Retificação: revisão documental mudou")
        base = _trusted_document(base_document, documents, contest, identity=expected_identity, role="base")
        supplied_amendments = amendment_documents or [amendment_document]
        if not supplied_amendments:
            _error(422, "Retificação: informe ao menos um documento retificador")
        amendments = [_trusted_document(item, documents, contest, identity=expected_identity, role="retificador")
                      for item in supplied_amendments]
        amendment = amendments[0]
        base = _assert_document(base, contest, identity=expected_identity, role="base")
        amendments = [_assert_document(item, contest, identity=expected_identity, role="retificador") for item in amendments]
        # The manifest identifies which preserved bytes to open; it is not
        # evidence of the document's identity.  Corroborate the contest
        # number and distinctive authority words in the re-extracted pages.
        _assert_identity_text(base, documents, contest, identity=expected_identity)
        for item in amendments:
            _assert_identity_text(item, documents, contest, identity=expected_identity)
        if base["sha256"] == amendment["sha256"]:
            _error(422, "Retificação: edital-base e retificador devem ser documentos distintos")
        normalized_changes = _changes(changes, contest, amendments)
        normalized_periods = _validate_periods(periods)
        normalized_events = _validate_events(events, [base, *amendments])
        _assert_review_changes_bound(case, normalized_changes)
        _assert_provenance_in_pages(normalized_changes, normalized_events, documents)
        initial_fields = _initial_fields(run, documents) if contest is None else None
        if contest is None and not {"titulo", "orgao", "edital_numero"}.issubset(initial_fields or {}):
            _error(422, "Retificação: edital-base não revalidou os campos mínimos de criação")
        if contest is None and any(expected_identity.get(name) != initial_fields.get(name, {}).get("value")
                                   for name in ("titulo", "orgao", "edital_numero")):
            _error(409, "Retificação: identidade informada pelo run diverge do edital-base reextraído")
        payload = {
            "kind": "field_amendment", "action": "create" if contest is None else "update",
            "initial_composed": contest is None, "identity": expected_identity,
            "baseline": (_revision(db, contest) if contest is not None else {
                "values": {name: None for name in VERSIONED_FIELDS}, "latest_version_id": None,
                "source_id": expected_identity["source_id"], "external_id": expected_identity["external_id"],
                "link_pagina": expected_identity["detail_url"]}),
            "creation_metadata": ({"banca": initial_identity.get("banca") if initial_identity else None,
                                   "link_edital": (run.document.url_requested if run.document else None)}
                                  if contest is None else None),
            "initial_fields": initial_fields,
            "base_document": base, "amendment_document": amendment,
            "amendment_documents": amendments,
            "changes": normalized_changes, "periods": normalized_periods, "events": normalized_events,
            "reason": reason.strip(), "authorization": authorization_value,
            "run": run.model_dump(mode="json"), "review_case_id": review_case_id,
            "review_revision_hash": case["revision_hash"],
        }
        _assert_temporal_coherence(payload, list(normalized_changes))
        proposal_hash = _digest(payload)
        target_id = contest.id if contest is not None else None
        operation = _digest(["amendment", target_id, amendment["sha256"], proposal_hash])
        existing = db.scalar(select(PublicationProposal).where(PublicationProposal.proposal_hash == proposal_hash,
                                                              PublicationProposal.owner_user_id == user.id,
                                                              PublicationProposal.concurso_id == target_id))
        if existing:
            return proposal_view(existing)
        proposal = PublicationProposal(id="tpa-" + proposal_hash[:32], owner_user_id=user.id,
                                       run_id=run.run_id, concurso_id=target_id,
                                       proposal_hash=proposal_hash, payload=payload)
        db.add(proposal)
        try:
            db.commit()
        except (IntegrityError, OperationalError):
            db.rollback()
            existing = db.scalar(select(PublicationProposal).where(PublicationProposal.proposal_hash == proposal_hash,
                                                                   PublicationProposal.owner_user_id == user.id,
                                                                   PublicationProposal.concurso_id == target_id))
            if not existing:
                raise
            proposal = existing
        return proposal_view(proposal)


def proposal_view(proposal: PublicationProposal) -> dict[str, Any]:
    payload = proposal.payload or {}
    return {"id": proposal.id, "run_id": proposal.run_id, "concurso_id": proposal.concurso_id,
            "proposal_hash": proposal.proposal_hash, "state": proposal.state,
            "kind": payload.get("kind"), "action": payload.get("action"),
            "initial_composed": bool(payload.get("initial_composed")), "identity": payload.get("identity"),
            "creation_metadata": payload.get("creation_metadata"), "initial_fields": payload.get("initial_fields"),
            "base_document": payload.get("base_document"), "amendment_document": payload.get("amendment_document"),
            "amendment_documents": payload.get("amendment_documents") or ([payload.get("amendment_document")] if payload.get("amendment_document") else []),
            "changes": payload.get("changes", {}), "periods": payload.get("periods"),
            "events": payload.get("events", []), "reason": payload.get("reason"),
            "authorization": payload.get("authorization"), "approved_fields": proposal.approved_fields,
            "approved_by": proposal.approved_by, "approved_at": jsonable(proposal.approved_at),
            "applied_at": jsonable(proposal.applied_at), "version_id": proposal.version_id,
            "result": proposal.result}


def get_proposal(db, proposal_id: str, user) -> dict[str, Any]:
    proposal = db.scalar(select(PublicationProposal).where(PublicationProposal.id == proposal_id,
                                                           PublicationProposal.owner_user_id == user.id)
                         .with_for_update()
                         .execution_options(populate_existing=True))
    if not proposal or proposal.payload.get("kind") != "field_amendment":
        _error(404, "Retificação: proposta não encontrada")
    return proposal_view(proposal)


def approve_proposal(db, *, proposal_id: str, proposal_hash: str, fields: list[str] | None = None,
                     user, authorization: dict[str, Any] | None = None, queue=None, store=None) -> dict[str, Any]:
    authorize(user)
    proposal = db.scalar(select(PublicationProposal).where(PublicationProposal.id == proposal_id,
                                                           PublicationProposal.owner_user_id == user.id))
    if not proposal or proposal.payload.get("kind") != "field_amendment":
        _error(404, "Retificação: proposta não encontrada")
    if proposal_hash != proposal.proposal_hash or _digest(proposal.payload) != proposal.proposal_hash:
        _error(409, "Retificação: conteúdo revisado mudou")
    if proposal.state not in {"proposed", "applied", "no_change"}:
        _error(409, "Retificação: proposta não está aguardando revisão")
    run_payload = proposal.payload.get("run")
    if not run_payload or queue is None or store is None:
        _error(422, "Retificação: run, queue e store são obrigatórios")
    run = TenderProofRun.model_validate(run_payload)
    contest = db.get(Concurso, proposal.concurso_id) if proposal.concurso_id is not None else None
    initial_identity = proposal.payload.get("identity") if proposal.payload.get("initial_composed") else None
    with _review_context(queue, store, run, proposal.payload.get("review_case_id"), contest,
                         initial_identity=initial_identity) as (case, documents, _qdb):
        _assert_identity_text(proposal.payload["base_document"], documents, contest, identity=initial_identity)
        for document in proposal.payload.get("amendment_documents") or [proposal.payload["amendment_document"]]:
            _assert_identity_text(document, documents, contest, identity=initial_identity)
        auth = _authorization(authorization or proposal.payload.get("authorization"))
        _assert_review_changes_bound(case, proposal.payload.get("changes", {}))
        _assert_provenance_in_pages(proposal.payload.get("changes", {}), proposal.payload.get("events", []), documents)
        if case.get("revision_hash") != proposal.payload.get("review_revision_hash"):
            _error(409, "Retificação: revisão documental mudou")
        if proposal.state in {"applied", "no_change"}:
            _assert_temporal_coherence(proposal.payload, proposal.approved_fields or [])
            return proposal_view(proposal)
        creation_fields = set((proposal.payload.get("initial_fields") or {}).keys()) if proposal.payload.get("initial_composed") else set()
        allowed = set(proposal.payload.get("changes", {})) | creation_fields
        selected = fields
        if selected is None:
            _error(422, "Retificação: informe explicitamente os campos aprovados")
        if not selected or len(selected) != len(set(selected)) or not set(selected).issubset(allowed):
            _error(422, "Retificação: aprove explicitamente somente campos propostos")
        if proposal.payload.get("initial_composed"):
            required = {"titulo", "orgao", "edital_numero"}
            if not required.issubset(selected):
                _error(422, "Retificação: criação inicial exige aprovação explícita de título, órgão e edital")
            if any(proposal.payload["initial_fields"].get(name, {}).get("state") != "supported" for name in set(selected) & creation_fields):
                _error(422, "Retificação: campo-base inicial não está validado")
        _assert_temporal_coherence(proposal.payload, selected)
        if auth != proposal.payload.get("authorization"):
            _error(409, "Retificação: autorização diverge da autorização registrada na proposta")
        proposal.approved_fields = sorted(selected)
        proposal.approved_by = user.id
        proposal.approved_at = datetime.utcnow()
        proposal.state = "approved"
        db.commit()
        return proposal_view(proposal)


def _assert_baseline(db, proposal: PublicationProposal, contest: Concurso) -> None:
    if not contest or proposal.payload.get("identity") != _identity(contest):
        _error(409, "Retificação: identidade do concurso mudou")
    baseline = proposal.payload.get("baseline") or {}
    current = _revision(db, contest)
    values_equal = True
    for name in VERSIONED_FIELDS:
        left = (baseline.get("values") or {}).get(name)
        right = (current.get("values") or {}).get(name)
        if name in _DATE_FIELDS:
            equal = _same_value(name, left, right)
        else:
            try:
                # SQLAlchemy may round-trip money as Decimal("3500.00")
                # while the pre-commit value was an integer.  That storage
                # representation is not a catalog edit.
                equal = Decimal(str(left)) == Decimal(str(right)) if (
                    name in {"salario_min", "salario_max", "taxa"}
                    and left is not None and right is not None
                ) else _json(left) == _json(right)
            except (InvalidOperation, ValueError):
                equal = _json(left) == _json(right)
        if not equal:
            values_equal = False
            break
    same_revision = (values_equal
                     and baseline.get("latest_version_id") == current.get("latest_version_id")
                     and baseline.get("source_id") == current.get("source_id")
                     and baseline.get("external_id") == current.get("external_id")
                     and _same_url(baseline.get("link_pagina"), current.get("link_pagina")))
    if not same_revision:
        _error(409, "Retificação: catálogo mudou; prepare uma nova revisão")
    for name, change in proposal.payload.get("changes", {}).items():
        current = _event_current_value(contest, name)
        if current is not _MISSING and not _same_value(name, change.get("previous"), current):
            _error(409, f"Retificação: campo {name} mudou desde a revisão")


def apply_proposal(db, *, proposal_id: str, proposal_hash: str, user, queue=None, store=None) -> dict[str, Any]:
    authorize(user)
    if os.getenv("TENDERPROOF_PUBLICATION_ENABLED", "false").lower() != "true":
        _error(403, "Retificação: publicação desabilitada")
    proposal = db.scalar(select(PublicationProposal).where(PublicationProposal.id == proposal_id,
                                                           PublicationProposal.owner_user_id == user.id)
                         .with_for_update()
                         .execution_options(populate_existing=True))
    if not proposal or proposal.payload.get("kind") != "field_amendment":
        _error(404, "Retificação: proposta não encontrada")
    if proposal_hash != proposal.proposal_hash or _digest(proposal.payload) != proposal.proposal_hash:
        _error(409, "Retificação: conteúdo revisado mudou")
    run_payload = proposal.payload.get("run")
    if not run_payload or queue is None or store is None:
        _error(422, "Retificação: run, queue e store são obrigatórios")
    run = TenderProofRun.model_validate(run_payload)
    initial = bool(proposal.payload.get("initial_composed"))
    contest = db.scalar(select(Concurso).where(Concurso.id == proposal.concurso_id)
                        .with_for_update()
                        .execution_options(populate_existing=True))
    if contest is None and not initial:
        _error(409, "Retificação: concurso canônico ausente; prepare uma nova proposta")
    try:
        with _review_context(queue, store, run, proposal.payload.get("review_case_id"), contest,
                            initial_identity=proposal.payload.get("identity") if initial else None,
                            allow_finalized=proposal.state in {"applied", "no_change"}) as (case, documents, qdb):
            initial_identity = proposal.payload.get("identity") if initial else None
            _assert_identity_text(proposal.payload["base_document"], documents, contest, identity=initial_identity)
            for document in proposal.payload.get("amendment_documents") or [proposal.payload["amendment_document"]]:
                _assert_identity_text(document, documents, contest, identity=initial_identity)
            _assert_provenance_in_pages(proposal.payload.get("changes", {}), proposal.payload.get("events", []), documents)
            _assert_review_changes_bound(case, proposal.payload.get("changes", {}))
            _assert_temporal_coherence(proposal.payload, proposal.approved_fields or [])
            if case.get("revision_hash") != proposal.payload.get("review_revision_hash"):
                _error(409, "Retificação: revisão documental mudou")
            if proposal.state in {"applied", "no_change"}:
                from app.tenderproof import review_cases
                changed = [name for name in proposal.approved_fields if name in proposal.payload.get("changes", {})]
                review_cases.finalize_field_changes(queue, run, proposal.payload["review_case_id"], changed, db=qdb)
                return proposal_view(proposal)
            if proposal.state != "approved" or not proposal.approved_fields:
                _error(409, "Retificação: aprovação explícita necessária")
            if initial:
                fresh_initial_fields = _initial_fields(run, documents)
                if not _initial_fields_match(fresh_initial_fields, proposal.payload.get("initial_fields") or {}):
                    _error(409, "Retificação: campos-base reextraídos divergem da proposta; prepare nova revisão")
                if not {"titulo", "orgao", "edital_numero"}.issubset(proposal.approved_fields):
                    _error(422, "Retificação: criação inicial exige os campos mínimos aprovados")
                from app.tenderproof import canonical
                from app.models import Source
                source = db.get(Source, initial_identity.get("source_id"))
                candidate = next((item for item in run.candidates if item.candidate_id == run.selected_candidate_id), None)
                if not source or not candidate or candidate.external_id != initial_identity.get("external_id"):
                    _error(409, "Retificação: identidade inicial mudou desde a proposta")
                from app.tenderproof.publication_models import CanonicalIdentity
                existing = db.scalar(select(Concurso).where(Concurso.source_id == source.id,
                                                              Concurso.external_id == candidate.external_id)
                                     .with_for_update()
                                     .execution_options(populate_existing=True))
                if existing:
                    _error(409, "Retificação: concurso já cadastrado; prepare atualização vinculada")
                initial_values = {name: proposal.payload["initial_fields"][name]["value"]
                                  for name in proposal.approved_fields if name in proposal.payload["initial_fields"]}
                if any(initial_identity.get(name) != initial_values.get(name)
                       for name in ("titulo", "orgao", "edital_numero")):
                    _error(409, "Retificação: identidade textual do edital-base diverge da aprovação")
                resolved_identity = dict(initial_identity)
                resolved_identity["reason"] = "new_verified_identity"
                resolved_identity["keys"] = canonical.keys(source, candidate, initial_values)
                linked = [db.get(CanonicalIdentity, key) for key, _ in resolved_identity["keys"]]
                if any(item is not None for item in linked):
                    _error(409, "Retificação: identidade canônica já reservada; prepare nova revisão")
                possible = next((item for item in db.scalars(select(Concurso).where(
                    Concurso.orgao.is_not(None), Concurso.edital_numero.is_not(None)
                )).all() if canonical.norm(item.orgao) == canonical.norm(initial_identity.get("orgao"))
                           and canonical.norm(item.edital_numero) == canonical.norm(initial_identity.get("edital_numero"))), None)
                if possible:
                    _error(409, "Retificação: órgão e edital já existem; associação explícita necessária")
                contest = Concurso(source_id=source.id, external_id=candidate.external_id, banca=source.name,
                                   titulo=initial_values["titulo"], orgao=initial_values["orgao"],
                                   edital_numero=initial_values["edital_numero"],
                                   link_pagina=candidate.detail_url_observed,
                                   link_edital=proposal.payload.get("creation_metadata", {}).get("link_edital"),
                                   content_hash=_digest([proposal.id, proposal.proposal_hash]), raw_data={})
                for name, value in initial_values.items():
                    if name in {"titulo", "orgao", "edital_numero"}:
                        continue
                    if name in _DATE_FIELDS:
                        setattr(contest, name, datetime.fromisoformat(value) if isinstance(value, str) else value)
                    elif hasattr(contest, name):
                        setattr(contest, name, value)
                db.add(contest)
                db.flush()
                proposal.concurso_id = contest.id
                canonical.bind(db, contest, resolved_identity, proposal)
            else:
                _assert_baseline(db, proposal, contest)
            operation = _digest(["amendment", proposal.id, proposal.proposal_hash])
            prior = db.scalar(select(PublicationProposal).where(PublicationProposal.applied_observation == operation))
            if prior:
                return proposal_view(prior)
            claimed = db.execute(update(PublicationProposal).where(
                PublicationProposal.id == proposal.id,
                PublicationProposal.state == "approved",
                PublicationProposal.approved_at == proposal.approved_at,
            ).values(state="applying", applied_observation=operation).execution_options(synchronize_session=False))
            if claimed.rowcount != 1:
                _error(409, "Retificação: operação concorrente; recarregue a proposta")
            changed_names = [name for name in proposal.approved_fields if name in proposal.payload.get("changes", {})]
            creation_names = [name for name in proposal.approved_fields if name not in changed_names]
            before = {name: (_json(_event_current_value(contest, name))
                             if _event_current_value(contest, name) is not _MISSING else None)
                      for name in changed_names}
            before.update({name: None for name in creation_names})
            values = {name: _value(name, proposal.payload["changes"][name]["new"]) for name in changed_names}
            for name, value in values.items():
                if name in _DATE_FIELDS:
                    setattr(contest, name, datetime.fromisoformat(value) if isinstance(value, str) and "T" in value else (date.fromisoformat(value) if isinstance(value, str) else value))
                elif hasattr(contest, name):
                    setattr(contest, name, value)
            ledger = copy.deepcopy(contest.raw_data or {})
            tenderproof = ledger.setdefault("tenderproof", {})
            amendments = tenderproof.setdefault("amendments", [])
            amendments.append({"proposal_id": proposal.id, "proposal_hash": proposal.proposal_hash,
                               "base_document_sha256": proposal.payload["base_document"]["sha256"],
                               "amendment_document_sha256": proposal.payload["amendment_document"]["sha256"],
                               "base_document": proposal.payload["base_document"],
                               "amendment_document": proposal.payload["amendment_document"],
                               "amendment_documents": proposal.payload.get("amendment_documents") or [proposal.payload["amendment_document"]],
                               "changes": proposal.payload.get("changes", {}),
                               "reason": proposal.payload["reason"], "periods": proposal.payload.get("periods"),
                               "events": proposal.payload.get("events", []), "authorization": proposal.payload.get("authorization"),
                               "applied_at": datetime.now(timezone.utc).isoformat()})
            contest.raw_data = ledger
            db.flush()
            diff = {}
            for name in changed_names:
                diff[name] = {"label": proposal.payload["changes"][name]["label"], "old": before[name],
                              "new": _json(getattr(contest, name)) if name in _DATE_FIELDS else _json(values[name]),
                              "reason": proposal.payload["changes"][name]["reason"],
                              "provenance": proposal.payload["changes"][name]["provenance"]}
            for name in creation_names:
                evidence = proposal.payload.get("initial_fields", {}).get(name, {}).get("evidence", [])
                diff[name] = {"label": name, "old": None, "new": _json(getattr(contest, name)),
                              "reason": "Campo extraído do edital-base e aprovado explicitamente para a criação inicial.",
                              "provenance": evidence}
            version = ConcursoVersion(concurso_id=contest.id, content_hash=contest.content_hash,
                                      change_type="amendment", changed_fields=diff,
                                      change_summary=proposal.payload["reason"],
                                      raw_data_snapshot=_json({"canonical": ledger, "tenderproof": {
                                          "kind": "field_amendment", "proposal_id": proposal.id,
                                          "run_id": proposal.run_id, "base_document_sha256": proposal.payload["base_document"]["sha256"],
                                          "amendment_document_sha256": proposal.payload["amendment_document"]["sha256"],
                                          "changes": proposal.payload.get("changes", {}),
                                          "events": proposal.payload.get("events", []),
                                          "authorization": proposal.payload.get("authorization")}}))
            db.add(version)
            db.flush()
            db.add(PublicationOutbox(version_id=version.id, proposal_id=proposal.id))
            proposal.version_id = version.id
            proposal.state = "applied" if diff else "no_change"
            proposal.applied_observation = operation
            proposal.applied_at = datetime.utcnow()
            proposal.result = {"diff": diff, "after_revision": _revision(db, contest), "state": proposal.state,
                               "periods": proposal.payload.get("periods"), "events": proposal.payload.get("events", [])}
            db.commit()
            from app.tenderproof import review_cases
            review_cases.finalize_field_changes(queue, run, proposal.payload["review_case_id"], changed_names, db=qdb)
            return proposal_view(proposal)
    except (IntegrityError, OperationalError):
        db.rollback()
        _error(409, "Retificação: concorrência ou idempotência; recarregue a proposta")
    except Exception:
        db.rollback()
        raise


def reject_stale_observation(db, contest: Concurso, observed_values: dict[str, Any]) -> None:
    """Reject an old collector snapshot after an amendment became canonical.

    Legacy collectors can call this before assigning an item.  A snapshot that
    still carries the ``old`` value of an applied amendment cannot overwrite
    its ``new`` value.  Unrelated fields continue through the normal crawler.
    """
    rows = db.scalars(select(ConcursoVersion).where(ConcursoVersion.concurso_id == contest.id,
                                                    ConcursoVersion.change_type == "amendment")).all()
    for version in rows:
        for name, change in (version.changed_fields or {}).items():
            if name not in observed_values or name in EVENT_CHANGE_FIELDS:
                continue
            if _same_value(name, getattr(contest, name), change.get("new")) and _same_value(name, observed_values[name], change.get("old")):
                _error(409, f"Retificação: observação antiga não pode reverter {name}")


def verify_applied(db, proposal_id: str, user) -> dict[str, Any]:
    result = get_proposal(db, proposal_id, user)
    if result["state"] not in {"applied", "no_change"}:
        _error(409, "Retificação: proposta ainda não aplicada")
    contest = db.get(Concurso, result["concurso_id"]) if result["concurso_id"] is not None else None
    if contest is None:
        _error(409, "Retificação: proposta inicial composta ainda não possui concurso canônico")
    current = {name: _event_current_value(contest, name) for name in result["changes"]}
    ok = all(value is not _MISSING and _same_value(name, change["new"], value)
             for name, change in result["changes"].items() for value in [current[name]])
    return {"ok": ok,
            "concurso_id": contest.id, "version_id": result["version_id"], "state": result["state"],
            "current": {name: _json(value) if value is not _MISSING else None for name, value in current.items()}}
