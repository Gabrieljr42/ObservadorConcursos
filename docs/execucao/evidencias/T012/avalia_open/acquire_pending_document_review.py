"""Bounded acquisition of the two explicitly preserved Avalia pending URLs.

No listing/detail crawl, redirect fallback, API, DB, or proposal action is used.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from app.tenderproof.batch60_major_adapters import AvaliaAdapter
from app.tenderproof.http_driver import BoundedHTTPDriver
from app.tenderproof.security import TenderProofLimits, TenderProofSettings


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "artifacts" / "document-review"
DETAIL_URL = "https://www2.avalia.org.br/concurso.jsp?id=631"
PENDING = [
    {
        "id": "pending-url-d8974aea-a734-4741-9f8a-011b75c0953a",
        "kind": "outro",
        "title": "1º Termo de Retificação do Edital de Abertura nº 001/2026 - Concurso Público nº 001/2026",
        "url": "https://arquivos-site.avalia.org.br/publicacoes/d8974aea-a734-4741-9f8a-011b75c0953a.pdf",
    },
    {
        "id": "pending-url-83d1c417-4dca-420b-be4c-d03fbbdf4f38",
        "kind": "edital",
        "title": "Edital de Abertura - Concurso Público nº 001/2026",
        "url": "https://arquivos-site.avalia.org.br/publicacoes/83d1c417-4dca-420b-be4c-d03fbbdf4f38.pdf",
    },
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    adapter = AvaliaAdapter()
    candidate = adapter.candidate_from_url(
        DETAIL_URL, "Superintendência Municipal de Segurança e Mobilidade de Caldas Novas - GO"
    )
    driver = BoundedHTTPDriver(
        adapter.source,
        TenderProofSettings(
            allowlist_hosts=adapter.allowed_hosts,
            limits=TenderProofLimits(max_navigations=2, total_timeout_s=60, max_download_bytes=30 * 1024 * 1024),
        ),
    )
    driver.set_candidate(candidate)
    report = {
        "schema": "t012.avalia.document-review-acquisition.v1",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "source": "avalia_open",
        "external_id": "631",
        "detail_url": DETAIL_URL,
        "scope": "exactly two pending URLs; bounded GET only",
        "requests_expected": 2,
        "documents": [],
        "network": True,
        "db_write": False,
        "proposal_dispatch": False,
    }
    try:
        for pending in PENDING:
            row = {"pending_id": pending["id"], "kind": pending["kind"], "title": pending["title"], "url": pending["url"]}
            try:
                result = driver.download(pending["url"], max_bytes=30 * 1024 * 1024)
                digest = hashlib.sha256(result.content).hexdigest()
                suffix = ".pdf"
                target = OUT / f"{pending['id']}{suffix}"
                target.write_bytes(result.content)
                row.update({"status": "ACQUIRED", "sha256": digest, "byte_len": len(result.content), "content_type": result.content_type, "url_final": result.url_final, "file": target.name, "redirect_chain": result.redirect_chain})
            except Exception as exc:
                row.update({"status": "BLOCKER", "error_type": type(exc).__name__, "error": str(exc)})
            report["documents"].append(row)
    finally:
        report["requests_used"] = driver.requests
        report["diagnostics"] = driver.diagnostics()
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        (OUT / "acquisition-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        driver.close()
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
