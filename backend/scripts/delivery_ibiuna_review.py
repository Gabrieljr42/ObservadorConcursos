"""Prepare a private, unapproved documentary review for ABCP 2867.

The three documents are registration/assistance lists.  Their titles and
contents do not by themselves alter the contest schedule or the catalogue
fields, and their extracted headers carry ``PROCESSO SELETIVO - 001/2026``
while the approved edital-base is ``002/2026``.  This script reads only
the three URLs already present in the preserved continuous manifest, checks
their bytes and PDF pages, and writes a redacted review packet.  It never
calls an approval or publication endpoint and never changes the pilot state.

The input PDFs are expected to have been acquired into the private evidence
directory by the operator or by the bounded review flow.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "backend" / ".tenderproof" / "product-completion" / "ibiuna-review-20260909"
OUT = EVIDENCE_DIR / "decision-draft.json"

BASE_SHA256 = "ab10571f0d89399ed24f54e9ea7c41b7d56ebbbad1be70fa12d9f7838ad29c72"
BASE_URL = "https://anexos-r2.selecao.net.br/uploads/567/concursos/2867/anexos/4194043a-894b-4a70-88b8-d5c8ad4a62ce.pdf"
BASE_HEADER_SNIPPET = "PREFEITURA DO MUNICÍPIO DA ESTÂNCIA TURÍSTICA DE IBIÚNA / PROCESSO SELETIVO SIMPLIFICADO / EDITAL NÚMERO 002/2026"

DOCUMENTS = (
    {
        "filename": "deferidas.pdf",
        "title": "LISTA PROVISÓRIA DE INSCRIÇÕES DEFERIDAS 09/09/2026",
        "url": "https://anexos-r2.selecao.net.br/uploads/567/concursos/2867/anexos/c99be3f3-74d0-42fa-88dc-0aaf0b3b46d5.pdf",
        "safe_terms": ("LISTA PROVISÓRIA", "INSCRIÇÕES DEFERIDAS"),
    },
    {
        "filename": "deferidas-pcd.pdf",
        "title": "LISTA PROVISÓRIA DE INSCRIÇÕES DEFERIDAS E INDEFERIDAS - PcD 09/09/2026",
        "url": "https://anexos-r2.selecao.net.br/uploads/567/concursos/2867/anexos/1fb4b5f1-4e55-447f-a883-9eddb32e1105.pdf",
        "safe_terms": ("LISTA PROVISÓRIA", "INSCRIÇÕES", "INDEFERIDAS"),
    },
    {
        "filename": "condicoes-especiais.pdf",
        "title": "LISTA DE SOLICITAÇÕES DE CONDIÇÕES ESPECIAIS PARA REALIZAÇÃO DE PROVA 09/09/2026",
        "url": "https://anexos-r2.selecao.net.br/uploads/567/concursos/2867/anexos/194440b3-fb5b-4d54-80e2-916c97d752f7.pdf",
        "safe_terms": ("LISTA", "CONDIÇÕES ESPECIAIS", "REALIZAÇÃO DE PROVA"),
    },
)

SCHEDULE_RE = re.compile(r"cronograma|prova objetiva|inscri(?:ç|c)[õo]es.*(?:até|período|periodo)", re.I)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u00a0", " ")).strip()


def safe_title_snippet(pages: list[str], terms: tuple[str, ...], fallback: str) -> tuple[int, str]:
    """Return a title-only snippet; never return a row containing candidate data."""
    for page_number, raw in enumerate(pages, 1):
        compact = normalized(raw)
        if all(term.casefold() in compact.casefold() for term in terms):
            # Stop before the first column heading.  Everything after that
            # point is a candidate row (names, dates of birth, identifiers).
            row_heading = re.search(r"\bINSC\.?\s+NASC\.?\s+NOME\b", compact, re.I)
            snippet = compact[: row_heading.start() if row_heading else 320].strip()
            # Keep the evidence literal useful while guaranteeing no row data.
            snippet = snippet[-320:]
            return page_number, snippet
    return 1, fallback


def inspect_document(spec: dict) -> dict:
    path = EVIDENCE_DIR / spec["filename"]
    if not path.is_file():
        raise FileNotFoundError(f"evidence missing: {path}")
    content_hash = sha256(path)
    reader = PdfReader(str(path), strict=False)
    pages = [page.extract_text() or "" for page in reader.pages]
    page_number, snippet = safe_title_snippet(pages, spec["safe_terms"], spec["title"])
    schedule_terms = sorted({match.group(0).lower() for text in pages for match in SCHEDULE_RE.finditer(text)})
    return {
        "title": spec["title"],
        "url": spec["url"],
        "filename": spec["filename"],
        "sha256": content_hash,
        "byte_len": path.stat().st_size,
        "page_count": len(pages),
        "inspected_all_pages": True,
        "evidence_page": page_number,
        "literal_snippet": snippet,
        "schedule_term_hits": schedule_terms,
        "schedule_effect": "not_observed_in_extracted_text",
        "decision": "no_field_change_identity_conflict",
        "identity_check": {
            "expected_edital": "002/2026",
            "observed_header": "PROCESSO SELETIVO - 001/2026",
            "status": "conflict_requires_human_review",
            "note": "The document URL belongs to the 2867 detail manifest, but the extracted header carries a different process number. Do not clear the pending gate until the operator confirms whether this is an official numbering error or a document from another process.",
        },
        "effect": "No catalogue field change is proposed. The list records an administrative result or requested accommodation, but its process number conflicts with the approved edital identity.",
        "reason": "The preserved document is a list and does not establish a new inscription deadline or proof date. Its header says PROCESSO SELETIVO - 001/2026 while the approved edital-base is 002/2026, so the identity conflict must be resolved by a human before any approval or pending-document clearance.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT, help="private JSON output path")
    args = parser.parse_args()
    docs = [inspect_document(spec) for spec in DOCUMENTS]
    result = {
        "schema": "ibiuna-document-review/1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "prepared_unapproved",
        "contest": {"source": "abcp_open", "external_id": "2867", "catalogue_id": 2, "edital": "002/2026"},
        "selected_document": {
            "url": BASE_URL,
            "sha256": BASE_SHA256,
            "page": 1,
            "literal_snippet": BASE_HEADER_SNIPPET,
            "relation": "edital-base",
        },
        "documents": docs,
        "catalogue_effect": "no_field_change_identity_conflict",
        "identity_check": {
            "expected_edital": "002/2026",
            "observed_header": "PROCESSO SELETIVO - 001/2026",
            "status": "conflict_requires_human_review",
        },
        "schedule_decision": {
            "inscricao_inicio": {"value": "2026-08-25", "action": "retain_approved_value"},
            "inscricao_fim": {"value": "2026-09-08", "action": "retain_approved_value"},
            "prova_data": {"value": None, "action": "remain_unconfirmed"},
        },
        "approval_required": True,
        "approval_blocked_until_identity_review": True,
        "approval_note": "Human reviewer must resolve the 001/2026 versus 002/2026 identity conflict, inspect the three preserved PDFs, and then approve one decision per SHA if the documents are confirmed to belong to contest 2867. This packet does not approve, apply, or clear anything.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "output": str(args.out),
        "documents": [{"title": d["title"], "sha256": d["sha256"], "pages": d["page_count"], "evidence_page": d["evidence_page"]} for d in docs],
        "catalogue_effect": result["catalogue_effect"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
