"""Field-changing notice flow: identity, evidence, review, application and precedence."""
from datetime import datetime
import copy
import hashlib
import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.models import Concurso, ConcursoVersion
from app.tenderproof import amendment
from app.tenderproof import review_cases as review
from app.tenderproof.contracts import DocumentCandidate
from app.tenderproof.demo_pdf import make_text_pdf
from app.tenderproof.solari_adapter import DownloadedBytes
from app.tenderproof.store import artifact_dir
from app.tenderproof.publication_models import PublicationOutbox, PublicationProposal
from test_tenderproof_publication import env
from test_tenderproof_document_review_gate import checkpoint, manifest


NOTICE_URL = "https://cdn-fenix.selecao.site/edital/1/129/08d76dcea494860bd7181d1f6b79d884.pdf"
AUTH = {"actor_kind": "delegated_automation", "human_read": False,
        "delegation_reference": "delivery-pedrinhas-review-20260909", "delegation_sha256": "a" * 64}


def _documents(contest, base_sha, notice_sha, base_url):
    contest.raw_data = {"tenderproof_documents": [{"sha256": base_sha, "role": "base"}]}
    base = {"sha256": base_sha, "url": base_url,
            "identity": {"source_id": contest.source_id, "external_id": contest.external_id,
                          "edital_numero": contest.edital_numero}}
    notice = {"sha256": notice_sha, "url": NOTICE_URL,
              "identity": {"source_id": contest.source_id, "external_id": contest.external_id,
                            "edital_numero": contest.edital_numero}}
    return base, notice


def _changes(contest, notice_sha):
    return {
        "inscricao_inicio": {"previous": "2026-08-21T10:00:00-03:00", "new": "2026-09-09T10:00:00-03:00",
            "reason": "Ato posterior reabre as inscrições com horário comprovado.",
            "provenance": {"sha256": notice_sha, "page": 1, "source_url": NOTICE_URL,
                            "snippet": "inscrições de 09/09/2026 às 10h até 11/09/2026 às 10h"}},
        "inscricao_fim": {"previous": "2026-09-04T23:59:00-03:00", "new": "2026-09-11T10:00:00-03:00",
            "reason": "Ato posterior substitui o prazo vigente de inscrições.",
            "provenance": {"sha256": notice_sha, "page": 1, "source_url": NOTICE_URL,
                            "snippet": "09/09/2026 às 10h até 11/09/2026 às 10h"}},
        "prova_data": {"previous": "2026-09-13", "new": "2026-09-27",
            "reason": "Ato posterior altera a data da prova objetiva.",
            "provenance": {"sha256": notice_sha, "page": 1, "source_url": NOTICE_URL,
                            "snippet": "prova objetiva em 27/09/2026, das 08h00 às 11h00"}},
    }


def _proposal(env):
    db, _, user, contest, run, store = env
    # Fixture dates intentionally differ from the real case; set the baseline
    # explicitly to exercise the previous-value conflict gate.
    contest.inscricao_inicio = datetime.fromisoformat("2026-08-21T10:00:00-03:00")
    contest.inscricao_fim = datetime.fromisoformat("2026-09-04T23:59:00-03:00")
    contest.prova_data = datetime.fromisoformat("2026-09-13T00:00:00-03:00")
    db.commit()
    base_content = store.load_artifact_bytes(run.artifact)
    notice_content = make_text_pdf(["PREFEITURA MUNICIPAL DE EXEMPLO. CONCURSO PÚBLICO 01/2026. EDITAL DE PRORROGAÇÃO. inscrições de 09/09/2026 às 10h até 11/09/2026 às 10h. homologação das inscrições em 18/09/2026. prova objetiva em 27/09/2026, das 08h00 às 11h00."])
    notice_sha = hashlib.sha256(notice_content).hexdigest()
    base, notice = _documents(contest, run.artifact.sha256, notice_sha, run.document.url_requested)
    run.document.kind = "consolidado"
    docs = manifest(env)
    docs[0]["kind"] = "consolidado"
    docs.append({"title": "Retificação 01", "url": NOTICE_URL, "kind": "retificacao"})
    queue, _ = checkpoint(env, docs)
    class Driver:
        settings = SimpleNamespace(limits=SimpleNamespace(max_download_bytes=30_000_000))
        adapter = SimpleNamespace(confirm_identity=lambda *args: None,
            documents=lambda *args: [DocumentCandidate(doc_id=str(i), title=d["title"], url_requested=d["url"], kind=d["kind"]) for i, d in enumerate(docs)])
        def __init__(self, source, settings): pass
        def open_detail(self, url): return "fixture"
        def download(self, url, **kwargs):
            return DownloadedBytes(url, url, notice_content if url == NOTICE_URL else base_content)
        def close(self): pass
    case = review.prepare(queue, store, run, driver_factory=Driver)
    changes = _changes(contest, notice_sha)
    notice_page = next(item for item in case["documents"] if item["artifact"]["sha256"] == notice_sha)["pages"][0]["text"]
    for change in changes.values():
        change["provenance"]["snippet"] = notice_page[:80]
    decisions = []
    for document in case["documents"]:
        snippet = document["pages"][0]["text"][:70]
        if document["artifact"]["sha256"] == notice_sha:
                decisions.append({"sha256": notice_sha, "page": 1, "snippet": snippet,
                    "effect": "field_changes", "reason": "O documento posterior altera campos do cronograma.",
                    "changes": [{"field_name": name, "previous": item["previous"], "new": item["new"],
                                 "provenance": item["provenance"]} for name, item in changes.items()]})
        else:
            decisions.append({"sha256": document["artifact"]["sha256"], "page": 1, "snippet": snippet,
                "effect": "no_field_change", "reason": "O edital-base permanece como histórico original."})
    review.approve(queue, store, run, case["id"], case["revision_hash"], decisions)
    proposal = amendment.create_proposal(
        db, concurso_id=contest.id, user=user, base_document=base, amendment_document=notice,
        changes=changes, reason="Retificação documental posterior do cronograma.",
        periods={"original": {"start": "2026-08-21T10:00:00-03:00", "end": "2026-09-04T23:59:00-03:00", "timezone": "America/Sao_Paulo"},
                  "reopenings": [{"start": "2026-09-09T10:00:00-03:00", "end": "2026-09-11T10:00:00-03:00", "timezone": "America/Sao_Paulo"}],
                  "current": {"start": "2026-09-09T10:00:00-03:00", "end": "2026-09-11T10:00:00-03:00", "timezone": "America/Sao_Paulo"}},
        events=[{"name": "homologacao", "date": "2026-09-18", "precision": "day", "timezone": None,
                  "provenance": {"sha256": notice_sha, "page": 1, "source_url": NOTICE_URL,
                                  "snippet": notice_page[:80]}}],
        authorization=AUTH, run=run, queue=queue, store=store, review_case_id=case["id"])
    return db, user, contest, run, store, queue, case, proposal


def test_prepare_requires_preserved_base_identity_and_evidence(env):
    db, user, contest, run, store, queue, case, proposal = _proposal(env)
    with pytest.raises(HTTPException, match="não pertence à revisão"):
        amendment.create_proposal(db, concurso_id=contest.id, user=user,
            base_document={**proposal["base_document"], "sha256": "b" * 64},
            amendment_document=proposal["amendment_document"], changes=proposal["changes"],
            reason=proposal["reason"], authorization=AUTH, run=run, queue=queue, store=store,
            review_case_id=case["id"])


def test_identity_number_is_bounded_and_snippet_must_be_literal(env):
    db, user, contest, run, store, queue, case, proposal = _proposal(env)
    pages = {item["artifact"]["sha256"]: {"pages": {page["page_number"]: page["text"]
             for page in item["pages"]}} for item in case["documents"]}
    wrong_number = {proposal["base_document"]["sha256"]: {"pages": {1:
        "PREFEITURA MUNICIPAL DE EXEMPLO Concurso Publico Edital 101/2026"}}}
    with pytest.raises(HTTPException, match="número do edital"):
        amendment._assert_identity_text(proposal["base_document"], wrong_number, contest)
    invented = copy.deepcopy(proposal["changes"])
    invented["inscricao_fim"]["provenance"][0]["snippet"] = "trecho que não existe no PDF"
    with pytest.raises(HTTPException, match="trecho literal"):
        amendment._assert_provenance_in_pages(invented, [], pages)


def test_amendment_is_reviewed_applied_idempotently_and_preserves_history(env):
    db, user, contest, run, store, queue, case, proposal = _proposal(env)
    approved = amendment.approve_proposal(db, proposal_id=proposal["id"], proposal_hash=proposal["proposal_hash"], user=user,
                                          fields=["inscricao_inicio", "inscricao_fim", "prova_data"], queue=queue, store=store)
    assert approved["state"] == "approved"
    result = amendment.apply_proposal(db, proposal_id=proposal["id"], proposal_hash=proposal["proposal_hash"], user=user, queue=queue, store=store)
    assert result["state"] == "applied"
    again = amendment.apply_proposal(db, proposal_id=proposal["id"], proposal_hash=proposal["proposal_hash"], user=user, queue=queue, store=store)
    assert again["version_id"] == result["version_id"]
    db.refresh(contest)
    assert contest.inscricao_fim.isoformat().startswith("2026-09-11T10:00:00")
    version = db.get(ConcursoVersion, result["version_id"])
    assert version.change_type == "amendment"
    assert version.changed_fields["inscricao_fim"]["provenance"][0]["sha256"] == proposal["amendment_document"]["sha256"]
    assert db.scalar(select(PublicationOutbox).where(PublicationOutbox.version_id == version.id)) is not None
    assert contest.raw_data["tenderproof"]["amendments"][0]["periods"]["original"]["timezone"] == "America/Sao_Paulo"


def test_conflict_wrong_contest_and_old_observation_are_rejected(env):
    db, user, contest, run, store, queue, case, proposal = _proposal(env)
    wrong = {**proposal["amendment_document"], "identity": {"source_id": contest.source_id, "external_id": "other", "edital_numero": contest.edital_numero}}
    with pytest.raises(HTTPException, match="identidade enviada"):
        amendment.create_proposal(db, concurso_id=contest.id, user=user, base_document=proposal["base_document"],
                                  amendment_document=wrong, changes=_changes(contest, proposal["amendment_document"]["sha256"]), reason="Outro concurso rejeitado.", authorization=AUTH,
                                  run=run, queue=queue, store=store, review_case_id=case["id"])
    amendment.approve_proposal(db, proposal_id=proposal["id"], proposal_hash=proposal["proposal_hash"], user=user,
                               fields=["inscricao_inicio", "inscricao_fim", "prova_data"], queue=queue, store=store)
    amendment.apply_proposal(db, proposal_id=proposal["id"], proposal_hash=proposal["proposal_hash"], user=user, queue=queue, store=store)
    with pytest.raises(HTTPException, match="não pode reverter"):
        amendment.reject_stale_observation(db, contest, {"inscricao_fim": "2026-09-04T23:59:00-03:00"})


def test_approval_cannot_claim_human_read_for_delegated_automation(env):
    db, _, user, contest, run, store = env
    with pytest.raises(HTTPException, match="não pode alegar leitura humana"):
        amendment.normalize_authorization({**AUTH, "human_read": True})


def test_event_only_effects_require_matching_provenance_events():
    payload = {
        "changes": {
            "etapas_prova": {"new": "Objetiva de Múltipla Escolha e Títulos"},
            "resultado_final_prazo": {"new": "2026-11-30"},
            "entrega_titulos_prazo": {"new": "2026-11-13"},
        },
        "events": [
            {"name": "Etapas da prova", "value": "Objetiva de Múltipla Escolha e Títulos"},
            {"name": "Resultado final", "date": "2026-11-30"},
            {"name": "Entrega dos títulos", "date": "2026-11-13"},
        ],
    }
    amendment._assert_temporal_coherence(payload, list(payload["changes"]))
    payload["events"][1]["date"] = "2026-11-29"
    with pytest.raises(HTTPException, match="evento comprovado"):
        amendment._assert_temporal_coherence(payload, list(payload["changes"]))


def test_event_text_value_is_not_mistaken_for_timestamp():
    events = amendment._validate_events([{
        "name": "Etapas da prova", "value": "Objetiva de Múltipla Escolha e Títulos",
        "provenance": {"sha256": "a" * 64, "page": 1, "source_url": NOTICE_URL,
                        "snippet": "Etapas da prova: Títulos"},
    }], {"sha256": "a" * 64, "url": NOTICE_URL})
    assert events[0]["value"].endswith("Títulos")


def test_event_only_effects_follow_normal_proposal_approval_and_apply(env):
    db, user, contest, run, store, queue, case, proposal = _proposal(env)
    review_case = review.read(queue, case["id"], run.owner_user_id)
    notice_sha = proposal["amendment_document"]["sha256"]
    page_text = next(item for item in case["documents"] if item["artifact"]["sha256"] == notice_sha)["pages"][0]["text"]
    snippet = page_text[:80]
    provenance = {"sha256": notice_sha, "page": 1, "source_url": NOTICE_URL, "snippet": snippet}
    event_changes = {
        "etapas_prova": {"field_name": "etapas_prova", "previous": "Objetiva de Múltipla Escolha e TAF",
                         "new": "Objetiva de Múltipla Escolha e Títulos", "label": "etapas da prova",
                         "reason": "A retificação substitui a etapa TAF por títulos com texto comprovado.",
                         "provenance": [provenance]},
        "resultado_final_prazo": {"field_name": "resultado_final_prazo", "previous": "2026-11-17",
                                  "new": "2026-11-30", "label": "prazo do resultado final",
                                  "reason": "A retificação posterga o resultado final com data comprovada.",
                                  "provenance": [provenance]},
        "entrega_titulos_prazo": {"field_name": "entrega_titulos_prazo", "previous": None,
                                   "new": "2026-11-13", "label": "prazo da entrega de títulos",
                                   "reason": "A retificação cria prazo de entrega de títulos comprovado.",
                                   "provenance": [provenance]},
    }
    decisions = review_case["decisions"]
    for decision in decisions:
        if decision.get("effect") == "field_changes":
            decision["changes"] = [{key: item[key] for key in ("field_name", "previous", "new", "provenance")}
                                    for item in event_changes.values()]
    with queue._db(write=True) as qdb:
        qdb.execute("UPDATE document_effect_cases SET decisions=? WHERE id=?", (json.dumps(decisions, ensure_ascii=False), case["id"]))
    events = [
        {"name": "Etapas da prova", "value": event_changes["etapas_prova"]["new"], "provenance": [provenance]},
        {"name": "Resultado final", "date": "2026-11-30", "provenance": [provenance]},
        {"name": "Entrega dos títulos", "date": "2026-11-13", "provenance": [provenance]},
    ]
    row = db.get(PublicationProposal, proposal["id"])
    payload = copy.deepcopy(row.payload)
    payload.update(changes=event_changes, periods=None, events=events)
    row.payload = payload
    row.proposal_hash = amendment._digest(payload)
    db.commit()
    updated = amendment.get_proposal(db, row.id, user)
    approved = amendment.approve_proposal(db, proposal_id=row.id, proposal_hash=updated["proposal_hash"],
                                          fields=list(event_changes), user=user, queue=queue, store=store)
    assert approved["state"] == "approved"
    applied = amendment.apply_proposal(db, proposal_id=row.id, proposal_hash=updated["proposal_hash"],
                                       user=user, queue=queue, store=store)
    assert applied["state"] == "applied"
    version = db.get(ConcursoVersion, applied["version_id"])
    assert set(version.changed_fields) == set(event_changes)
    assert contest.raw_data["tenderproof"]["amendments"][-1]["changes"]["etapas_prova"]["new"].endswith("Títulos")
    assert amendment.verify_applied(db, row.id, user)["ok"] is True


def test_initial_composed_proposal_is_reviewable_before_canonical_registration(env):
    """A base plus notice can be queued without inventing a Concurso row."""
    db, user, contest, run, store, queue, case, existing = _proposal(env)
    source_id = contest.source_id
    base = existing["base_document"]
    notice = existing["amendment_document"]
    changes = existing["changes"]

    # This fixture starts with a catalog row only so the normal document-review
    # helper can prepare the case.  The composed path must work after that row
    # is absent; it must not silently associate the proposal with another row.
    db.delete(contest)
    db.commit()
    result = amendment.create_proposal(
        db, concurso_id=None, source_id=source_id, user=user, base_document=base,
        amendment_document=notice, changes=changes,
        reason="Publicação inicial composta pelo edital e sua retificação.",
        authorization=AUTH, run=run, queue=queue, store=store,
        review_case_id=case["id"], review_hash=case["revision_hash"],
    )
    assert result["state"] == "proposed"
    assert result["concurso_id"] is None
    assert result["action"] == "create"
    assert result["initial_composed"] is True
    assert result["base_document"]["sha256"] == base["sha256"]
    assert result["amendment_document"]["sha256"] == notice["sha256"]
    assert queue.review_for_run(run)["pending"]

    approved = amendment.approve_proposal(
        db, proposal_id=result["id"], proposal_hash=result["proposal_hash"],
        fields=["titulo", "orgao", "edital_numero", *changes], user=user, queue=queue, store=store,
    )
    assert approved["state"] == "approved"
    assert queue.review_for_run(run)["pending"]
    applied = amendment.apply_proposal(
        db, proposal_id=result["id"], proposal_hash=result["proposal_hash"],
        user=user, queue=queue, store=store,
    )
    assert applied["state"] == "applied"
    assert applied["concurso_id"] is not None
    created = db.get(Concurso, applied["concurso_id"])
    assert created.titulo == "Concurso Prefeitura Municipal de Exemplo MG cod 42"
    assert created.inscricao_inicio is not None
    version = db.get(ConcursoVersion, applied["version_id"])
    assert version.change_type == "amendment"
    assert {"titulo", "orgao", "edital_numero"}.issubset(version.changed_fields)
    assert db.scalar(select(PublicationOutbox).where(PublicationOutbox.version_id == version.id)) is not None
    repeated = amendment.apply_proposal(
        db, proposal_id=result["id"], proposal_hash=result["proposal_hash"],
        user=user, queue=queue, store=store,
    )
    assert repeated["version_id"] == applied["version_id"]
    assert not queue.review_for_run(run)["pending"]


def test_initial_apply_rolls_back_catalog_when_preserved_bytes_change(env):
    db, user, contest, run, store, queue, case, existing = _proposal(env)
    source_id = contest.source_id
    base = existing["base_document"]
    notice = existing["amendment_document"]
    changes = existing["changes"]
    db.delete(contest)
    db.commit()
    result = amendment.create_proposal(
        db, concurso_id=None, source_id=source_id, user=user, base_document=base,
        amendment_document=notice, changes=changes,
        reason="Publicação inicial composta com gate de bytes preservados.",
        authorization=AUTH, run=run, queue=queue, store=store,
        review_case_id=case["id"], review_hash=case["revision_hash"],
    )
    amendment.approve_proposal(
        db, proposal_id=result["id"], proposal_hash=result["proposal_hash"],
        fields=["titulo", "orgao", "edital_numero", *changes], user=user, queue=queue, store=store,
    )
    for document in case["documents"]:
        (artifact_dir() / document["artifact"]["storage_path"]).write_bytes(b"altered-preserved-bytes")
    with pytest.raises(HTTPException, match="bytes preservados"):
        amendment.apply_proposal(db, proposal_id=result["id"], proposal_hash=result["proposal_hash"],
                                 user=user, queue=queue, store=store)
    assert db.scalar(select(Concurso).where(Concurso.external_id == "42")) is None
    assert db.get(PublicationProposal, result["id"]).state == "approved"


def test_initial_proposal_rejects_run_title_not_found_in_reextracted_base(env):
    db, user, contest, run, store, queue, case, existing = _proposal(env)
    source_id = contest.source_id
    base = existing["base_document"]
    notice = existing["amendment_document"]
    changes = existing["changes"]
    db.delete(contest)
    db.commit()
    title = next(field for field in run.fields if field.field_name == "titulo")
    title.value = "Outro concurso inventado"
    with pytest.raises(HTTPException, match="diverge do edital-base"):
        amendment.create_proposal(
            db, concurso_id=None, source_id=source_id, user=user, base_document=base,
            amendment_document=notice, changes=changes,
            reason="Tentativa inicial com identidade divergente do PDF.",
            authorization=AUTH, run=run, queue=queue, store=store,
            review_case_id=case["id"], review_hash=case["revision_hash"],
        )
