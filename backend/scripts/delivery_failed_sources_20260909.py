"""Bounded read-only retry for sources with adapters but no successful detail snapshot.

The script deliberately uses only the listing URLs already recorded in the source
status file. It captures at most two details and one PDF per source, preserves
response hashes and errors, and never publishes or starts a paid browser session.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TARGETS = {
    "idecan_open", "ibgp_open", "admtec_open", "gualimp_open", "rbo_open",
    "nossorumo_open", "fatec_selection", "fapese_selection", "fapesb_selection",
    "fapesp_selection", "fappr_selection", "fapergs_selection", "fapdf_selection",
    "fapeam_selection", "fapeap_selection",
}
MAX_HTML = 2 * 1024 * 1024
MAX_PDF = 8 * 1024 * 1024


def read_listing_urls() -> dict[str, list[str]]:
    status = json.loads((ROOT.parent / "docs" / "tenderproof-product-status.json").read_text(encoding="utf-8"))
    return {
        item["source"]: list(item.get("configured_listing_urls") or [])
        for item in status["sources"]
        if item["source"] in TARGETS
    }


def bounded_body(response: httpx.Response, limit: int) -> bytes:
    size = 0
    chunks: list[bytes] = []
    for chunk in response.iter_bytes():
        size += len(chunk)
        if size > limit:
            raise ValueError(f"response exceeds {limit} bytes")
        chunks.append(chunk)
    return b"".join(chunks)


def save_bytes(root: Path, source: str, label: str, raw: bytes, suffix: str) -> dict:
    digest = hashlib.sha256(raw).hexdigest()
    path = root / f"{source}-{label}-{digest[:16]}{suffix}"
    path.write_bytes(raw)
    return {"file": str(path.relative_to(root)), "bytes": len(raw), "sha256": digest}


def links(base: str, raw: bytes) -> list[dict[str, str]]:
    soup = BeautifulSoup(raw, "lxml")
    result = []
    for anchor in soup.select("a[href]"):
        href = urljoin(base, anchor.get("href", ""))
        if urlsplit(href).scheme in ("http", "https"):
            result.append({"url": href, "title": " ".join(anchor.get_text(" ", strip=True).split())[:300]})
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / ".tenderproof" / "product-completion" / "delivery-failed-sources-20260909")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    observed_at = datetime.now(timezone.utc).isoformat()
    urls_by_source = read_listing_urls()
    report = {
        "schema": 1,
        "observed_at": observed_at,
        "scope": "15 configured official listing URLs; max 2 details and 1 PDF per source; no publication",
        "limits": {"timeout_seconds": 15, "html_bytes": MAX_HTML, "pdf_bytes": MAX_PDF, "details_per_source": 2, "documents_per_source": 1},
        "sources": [],
    }

    with httpx.Client(timeout=15, follow_redirects=False, trust_env=False,
                      headers={"User-Agent": "ObservadorDeConcursos/1.0", "Accept": "text/html,application/xhtml+xml,application/pdf"}) as client:
        for source in sorted(TARGETS):
            source_result = {"source": source, "listing_urls": urls_by_source.get(source, []), "listing": [], "details": [], "documents": []}
            listing_url = (urls_by_source.get(source) or [None])[0]
            if not listing_url:
                source_result["error"] = "no configured listing URL"
                report["sources"].append(source_result)
                continue
            try:
                response = client.get(listing_url)
                record = {"requested_url": listing_url, "status": response.status_code, "location": response.headers.get("location")}
                raw = bounded_body(response, MAX_HTML)
                record.update(save_bytes(args.output, source, "listing", raw, ".html"))
                record["title"] = BeautifulSoup(raw, "lxml").title.get_text(" ", strip=True) if BeautifulSoup(raw, "lxml").title else None
                record["links"] = links(listing_url, raw)
                source_result["listing"].append(record)
                if response.status_code >= 400:
                    source_result["outcome"] = "listing_http_error"
                    report["sources"].append(source_result)
                    continue
            except Exception as exc:
                source_result["listing"].append({"requested_url": listing_url, "error_type": type(exc).__name__, "error": str(exc)[:400]})
                source_result["outcome"] = "listing_acquisition_failed"
                report["sources"].append(source_result)
                continue

            # Keep this generic and conservative: only same-host links containing
            # an observed detail-like path are tried, never guessed URL variants.
            listing_links = source_result["listing"][0]["links"]
            host = urlsplit(listing_url).hostname
            candidates = []
            for link in listing_links:
                parsed = urlsplit(link["url"])
                path = parsed.path.casefold()
                if parsed.hostname == host and any(marker in path for marker in ("/informacoes/", "/edital/ver/", "/concurso/", "/processo", "/publicacoes/", "/pagina/")):
                    if link["url"] not in [item["url"] for item in candidates]:
                        candidates.append(link)
                if len(candidates) >= 2:
                    break
            for index, candidate in enumerate(candidates):
                detail = {"url": candidate["url"], "title_from_listing": candidate["title"]}
                try:
                    response = client.get(candidate["url"])
                    detail.update({"status": response.status_code, "location": response.headers.get("location")})
                    raw = bounded_body(response, MAX_HTML)
                    detail.update(save_bytes(args.output, source, f"detail-{index}", raw, ".html"))
                    detail["links"] = links(candidate["url"], raw)
                    detail["pdf_links"] = [link for link in detail["links"] if ".pdf" in urlsplit(link["url"]).path.casefold() or ".pdf" in urlsplit(link["url"]).query.casefold()]
                    source_result["details"].append(detail)
                    if response.status_code >= 400:
                        continue
                    for doc in detail["pdf_links"][:1]:
                        try:
                            doc_response = client.get(doc["url"])
                            doc_record = {"url": doc["url"], "title": doc["title"], "status": doc_response.status_code}
                            doc_raw = bounded_body(doc_response, MAX_PDF)
                            doc_record.update(save_bytes(args.output, source, f"document-{index}", doc_raw, ".pdf"))
                            source_result["documents"].append(doc_record)
                        except Exception as exc:
                            source_result["documents"].append({"url": doc["url"], "error_type": type(exc).__name__, "error": str(exc)[:400]})
                        break
                except Exception as exc:
                    detail.update({"error_type": type(exc).__name__, "error": str(exc)[:400]})
                    source_result["details"].append(detail)
            source_result["outcome"] = "detail_acquired" if source_result["details"] else "no_observed_detail_links"
            report["sources"].append(source_result)

    (args.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for item in report["sources"]:
        print(json.dumps({"source": item["source"], "outcome": item.get("outcome"), "listing": item.get("listing", [{}])[0].get("status"), "details": len(item.get("details", [])), "documents": len(item.get("documents", [])), "errors": [d.get("error_type") for d in item.get("details", []) if d.get("error_type")]}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
