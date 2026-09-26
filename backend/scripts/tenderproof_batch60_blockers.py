"""Bounded public diagnostics only; never source certification or challenge solving."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, UnicodeDammit

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "backend/tests/fixtures/tenderproof_batch60_blockers"
SOURCES = {"aocp_open", "seprod_open", "fumarc_open", "unifil_open", "leandroferreira_open", "iuds_open", "idgran_open", "shdias_open", "epl_open", "apta_open"}
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"


def capture(row):
    result = {"source": row["source"], "url": row["url"], "basis": row.get("basis", "Existing catalogue URL; one User-Agent compatibility check"), "observed_at": datetime.now(timezone.utc).isoformat(), "tls_verified": True}
    try:
        with httpx.Client(timeout=25, follow_redirects=False, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"}) as client:
            with client.stream("GET", row["url"]) as response:
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > 2 * 1024 * 1024:
                        raise ValueError("Response exceeds 2 MiB; body not retained")
                    chunks.append(chunk)
                body = b"".join(chunks)
                name = f"{row['source']}-{hashlib.sha256(row['url'].encode()).hexdigest()[:12]}.html"
                (FIXTURES / name).write_bytes(body)
                decoded = UnicodeDammit(body, is_html=True)
                soup = BeautifulSoup(decoded.unicode_markup or "", "html.parser")
                text = soup.get_text(" ", strip=True)
                result.update(status=response.status_code, location=response.headers.get("location"), bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), file=name, encoding=decoded.original_encoding, title=soup.title.get_text(" ", strip=True) if soup.title else None, text_preview=text[:600], links=[{"url": urljoin(row["url"], a["href"]), "title": a.get_text(" ", strip=True)} for a in soup.select("a[href]")], scripts=[urljoin(row["url"], a["src"]) for a in soup.select("script[src]")])
                if "Just a moment" in text:
                    result["diagnosis"] = "HTTP access challenge; no challenge solving attempted"
                elif response.status_code == 403:
                    result["diagnosis"] = "HTTP 403 refusal despite HTML body; body is not a successful source acquisition"
                elif "Navegador incomp" in text:
                    result["diagnosis"] = "Browser compatibility refusal, not an empty catalogue"
                elif response.status_code == 200:
                    result["diagnosis"] = "HTTP document available; source contract and scope still unvalidated"
                else:
                    result["diagnosis"] = "HTTP response requires investigation"
    except Exception as exc:
        result.update(error_type=type(exc).__name__, error=str(exc)[:500], diagnosis="Transport failed; no unverified TLS fallback")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/tenderproof-batch60-blockers.json")
    args = parser.parse_args()
    FIXTURES.mkdir(parents=True, exist_ok=True)
    if args.targets:
        rows = json.loads(args.targets.read_text(encoding="utf-8"))
    else:
        initial = json.loads((ROOT / "backend/tests/fixtures/tenderproof_batch60_own/initial-manifest.json").read_text(encoding="utf-8"))
        rows, seen = [], set()
        for row in initial["pages"]:
            if row["source"] in SOURCES and row["source"] not in seen:
                seen.add(row["source"])
                rows.append(row)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(capture, rows))
    payload = {"observed_at": datetime.now(timezone.utc).isoformat(), "scope": "Read-only public HTTP; verified TLS; one compatibility User-Agent; no cookies, login, challenge solving, browser, PDFs, production effects or adapter certification; 25 seconds and 2 MiB per request; redirects recorded only.", "pages": results}
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps([{k: r.get(k) for k in ("source", "status", "bytes", "title", "error", "diagnosis")} for r in results], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
