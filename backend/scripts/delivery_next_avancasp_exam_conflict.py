"""Record a preserved AVANCASP date conflict without creating a proposal.

The base edital contains two literal calendars for the objective exam.  This
evidence-only script reprocesses the preserved bytes through the normal page
extractor and records both contexts, so no date is silently promoted.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "/app")

from app.tenderproof.processing import extract_pages_isolated
from app.tenderproof.store import get_store


RUN_ID = "tp-tcj-11c94e0888d15070a71c65b32bd7c98d-1"
ROOT = Path("/var/lib/observador/tenderproof")
OUTPUT = ROOT / "product-completion/delivery-next-avancasp-exam-conflict-20260909.json"


def compact(text: str, pattern: str, radius: int = 220) -> str:
    normalized = " ".join(text.split())
    match = re.search(pattern, normalized, re.IGNORECASE)
    if not match:
        raise RuntimeError(f"trecho ausente: {pattern}")
    start = max(0, match.start() - 40)
    end = min(len(normalized), match.end() + radius)
    return normalized[start:end]


def page_evidence(pages, page_number: int, pattern: str, label: str, artifact_sha256: str) -> dict:
    page = next((item for item in pages if item.page_number == page_number), None)
    if page is None:
        raise RuntimeError(f"página ausente: {page_number}")
    return {
        "label": label,
        "page": page_number,
        "artifact_sha256": artifact_sha256,
        "snippet": compact(page.text, pattern),
    }


def main() -> None:
    store = get_store()
    run = store.get_run(RUN_ID)
    if run is None or run.artifact is None:
        raise RuntimeError("run/artifact AVANCASP preservado ausente")
    content = store.load_artifact_bytes(run.artifact)
    digest = hashlib.sha256(content).hexdigest()
    if digest != run.artifact.sha256:
        raise RuntimeError("hash do PDF preservado divergente")
    pages, total, processed, truncated, errors = extract_pages_isolated(
        content,
        artifact_id=run.artifact.artifact_id,
        owner_id=str(run.owner_user_id),
        max_bytes=max(len(content), 30 * 1024 * 1024),
        max_pages=200,
        reuse_completed=True,
    )
    if truncated or errors or total != processed:
        raise RuntimeError(f"extração incompleta: total={total} processadas={processed} erros={errors}")

    evidence = [
        page_evidence(
            pages,
            41,
            r"Realiza[çc][aã]o da Prova Objetiva",
            "calendário-resumo-22-05",
            run.artifact.sha256,
        ),
        page_evidence(
            pages,
            6,
            r"Per[ií]odo\s+1.*?Data:\s*31/05/2026",
            "quadro-cargos-31-05-periodo-1",
            run.artifact.sha256,
        ),
        page_evidence(
            pages,
            6,
            r"Per[ií]odo\s+2.*?Data:\s*31/05/2026",
            "quadro-cargos-31-05-periodo-2",
            run.artifact.sha256,
        ),
    ]
    report = {
        "generated_at": "2026-09-09",
        "run_id": RUN_ID,
        "artifact_sha256": run.artifact.sha256,
        "pages": processed,
        "validation_status": run.validation_status.value,
        "identity": {
            "title": "Concurso Público - 02/2026 - PREFEITURA MUNICIPAL DE ITAPECERICA DA SERRA",
            "orgao": "Município De Itapecerica Da Serra",
            "edital": "055/2026",
        },
        "conflict": {
            "field": "prova_data",
            "values": ["2026-05-22", "2026-05-31"],
            "status": "document_conflict",
            "reason": "O calendário-resumo da p41 registra 22/05/2026, enquanto o quadro de aplicação da p6 registra 31/05/2026 para os dois períodos. Nenhuma data foi promovida.",
        },
        "evidence": evidence,
        "proposal_created": False,
        "approval_performed": False,
        "application_performed": False,
        "real_gap": "Resolver a divergência literal do edital-base e conferir os documentos posteriores já preservados antes de qualquer proposta ou aplicação AVANCASP.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "status": "document_conflict", "proposal_created": False}))


if __name__ == "__main__":
    main()
