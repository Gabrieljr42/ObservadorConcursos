"""Prepare, but do not approve/apply, the FAPESE proposal in the pilot DB."""
import json
from datetime import datetime, timezone
from pathlib import Path

from app.database import SessionLocal
from app.models import User
from app.tenderproof import publication
from app.tenderproof.processing import extract_pages_isolated
from app.tenderproof.store import get_store


RUN_ID = "tpr-a459e76ba624"
CONCURSO_ID = 14
AUTHORIZATION = {
    "actor_kind": "delegated_automation",
    "human_read": False,
    "delegation_reference": "user-attachment:6b86284b-154e-4ef6-88a1-6318513307e3/pasted-text-1.txt",
    "delegation_sha256": "a8d5f58a652eaed76d186385e12dadf9cbc4acf71cca71d5535a1797aca059f6",
}
OUT = Path("/var/lib/observador/tenderproof/product-completion/delivery-fapese-proposal-20260909.json")


def main():
    store = get_store()
    run = store.get_run(RUN_ID)
    if run is None or run.source != "fapese_selection" or run.owner_user_id != 1:
        raise RuntimeError("pilot FAPESE run not found for owner 1")
    with SessionLocal() as db:
        user = db.get(User, 1)
        view = publication.create_proposal(db, concurso_id=CONCURSO_ID, run=run, user=user, store=store,
                                           authorization=AUTHORIZATION)
        content = store.load_artifact_bytes(run.artifact)
        pages, _, _, _, errors = extract_pages_isolated(
            content, artifact_id=run.artifact.artifact_id, owner_id="1",
            max_bytes=30 * 1024 * 1024, max_pages=120, capacity_wait_s=15,
            reuse_completed=True,
        )
        full_text = "\n".join(page.text for page in pages)
        def excerpt(needle):
            index = full_text.lower().find(needle.lower())
            return full_text[max(0, index - 120):index + len(needle) + 320] if index >= 0 else None
        result = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "publication_applied": False,
            "authorization": AUTHORIZATION,
            "run_id": RUN_ID,
            "concurso_id": CONCURSO_ID,
            "source": run.source,
            "proposal": view,
            "field_summary": [
                {"field_name": f.field_name, "state": f.state.value,
                 "value": f.value,
                 "evidence": [{"page": e.page_number, "sha256": e.document_sha256,
                               "source_url": e.source_url,
                               "snippet": e.snippet} for e in f.evidence]}
                for f in run.fields
            ],
            "scope_check": {
                "title": run.document.title,
                "kind": run.document.kind,
                "personnel_modality": "prestadores de serviço/pessoa física; chamada pública para cadastro reserva",
                "bolsa_or_fomento_marker": False,
                "clt_employment_marker": False,
                "employment_word_context": excerpt("Documentação para Prestadores com Vínculo Empregatício"),
                "literal_evidence": {
                    "service_person": excerpt("PRESTADORES DE SERVIÇO/PESSOA FÍSICA"),
                    "selected_professional": excerpt("Selecionar profissional de nível superior"),
                    "civil_contract": excerpt("natureza estritamente civil"),
                },
                "literal_schedule": {
                    "page": next((page.page_number for page in pages if "9.2 Inscrição" in page.text), None),
                    "excerpt": next((page.text[max(0, page.text.find("9.2 Inscrição") - 80):page.text.find("9.3")]
                                     for page in pages if "9.2 Inscrição" in page.text and "9.3" in page.text), None),
                    "registration_period": "2026-09-07 a 2026-09-14",
                    "registration_deadline": "2026-09-14 23:59",
                    "parser_state": "literal schedule present; generic field extractor left inscricao_inicio/fim unknown because the table layout was not normalized",
                },
                "processing_errors": errors,
                "review_note": "A modalidade é prestação de serviço/pessoa física, com contrato de natureza civil; não foi tratada como bolsa, fomento ou emprego CLT. A menção a vínculo empregatício aparece apenas como documentação de eventual vínculo externo do prestador.",
            },
            "intended_approval_fields": ["inscricao_inicio", "inscricao_fim"],
        }
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(json.dumps({"receipt": str(OUT), "proposal_id": view["id"],
                          "proposal_hash": view["proposal_hash"], "state": view["state"],
                          "eligible_fields": view["eligible_fields"],
                          "blocked_fields": view["blocked_fields"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
