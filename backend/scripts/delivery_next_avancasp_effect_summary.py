"""Summarize literal effects from the prepared AVANCASP review case."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "/app")

from app.tenderproof.continuous_store import get_continuous_store
from app.tenderproof import review_cases
from app.tenderproof.store import get_store


RUN_ID = "tp-tcj-11c94e0888d15070a71c65b32bd7c98d-1"
CASE_ID = "drc-12bd9c8d22a1416b97c8b920813dfaaf"
ROOT = Path("/var/lib/observador/tenderproof")
OUTPUT = ROOT / "product-completion/delivery-next-avancasp-effects-20260909.json"


def compact_window(pages, pattern: str, radius: int = 80) -> str:
    for page in pages:
        text = " ".join(page["text"].split())
        match = re.search(pattern, text, re.I | re.S)
        if match:
            start = max(0, match.start() - 40)
            end = min(len(text), match.end() + radius)
            return " ".join(text[start:end].split())
    raise RuntimeError(f"trecho de efeito ausente: {pattern}")


def main() -> None:
    store = get_store()
    queue = get_continuous_store()
    run = store.get_run(RUN_ID)
    case = review_cases.read(queue, CASE_ID, run.owner_user_id)
    documents = []
    for item in case["documents"]:
        document = item["document"]
        kind = document["kind"]
        if kind == "prorrogacao":
            effect = "inscricao_fim 2026-05-04 -> 2026-05-07; pagamento 2026-05-05 -> 2026-05-08"
            snippet = compact_window(item["pages"], r"As inscrições para o Concurso Público encontrar-se-ão abertas")
        elif kind == "retificacao" and "CONVOCAÇÃO" in document["title"]:
            effect = "prova prática 25/07/2026 -> 26/07/2026"
            snippet = compact_window(item["pages"], r"Data:\s*25 de julho de 2026")
        elif kind == "retificacao":
            effect = "retificação do anexo de convocação da prova prática de Pedreiro; data 26/07/2026 às 08:00"
            snippet = "DATA DE PROVA HORÁRIO"
        elif kind == "edital":
            effect = "edital-base: inscricoes 30/03/2026–04/05/2026; prova objetiva 22/05/2026"
            snippet = compact_window(item["pages"], r"Período de Inscrições.*?30/03 a 04/05/2026")
        else:
            effect = "retificação de convocação da prova prática para Pedreiro; sem alteração canônica aprovada"
            snippet = "retificação de anexo de convocação preservada; detalhes individuais omitidos"
        documents.append({
            "kind": kind,
            "title": document["title"],
            "artifact_sha256": item["artifact"]["sha256"],
            "pages": len(item["pages"]),
            "effect_summary": effect,
            "evidence_snippet": snippet,
        })
    report = {
        "generated_at": "2026-09-09",
        "run_id": RUN_ID,
        "case_id": CASE_ID,
        "revision_hash": case["revision_hash"],
        "approval_performed": False,
        "application_performed": False,
        "documents": documents,
        "real_gap": "Os efeitos posteriores precisam de decisão documental antes de qualquer proposta/publicação AVANCASP; o edital-base não foi promovido como atual.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "case_id": CASE_ID, "documents": len(documents)}))


if __name__ == "__main__":
    main()
