"""Persist the already acquired FAPESE evidence through the pilot service.

Inputs are copied from the previously preserved host evidence into the pilot
TenderProof volume before this script runs. No network transport is used.
"""
from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path

from app.tenderproof.contracts import TenderProofRun
from app.tenderproof.http_driver import BoundedHTTPDriver
from app.tenderproof.security import TenderProofLimits, TenderProofSettings
from app.tenderproof.service import TenderProofBusy, TenderProofService
from app.tenderproof.solari_adapter import DownloadedBytes
from app.tenderproof.source_adapters import get_source_adapter
from app.tenderproof.store import TenderProofStore


INPUT = Path("/var/lib/observador/tenderproof/replay-input")
DETAIL = INPUT / "fapese-detail.html"
PDF = INPUT / "fapese-edital-007-2026.pdf"
SOURCE = "fapese_selection"
LISTING = "https://www.fapese.org.br/pronera/"
PDF_URL = "https://www.fapese.org.br/wp-content/uploads/2026/09/Edital-007.2026-RPA-PRONERA-2026_assinado_assinado.pdf"


class ReplayDriver:
    session_id = None
    replay_available = False

    def __init__(self, html, pdf):
        self.adapter = get_source_adapter(SOURCE)
        self.html = html
        self.pdf = pdf
        self.candidate = None
        self._notes = ["replay of previously preserved official HTML/PDF; no network transport"]

    def open_listing(self, url):
        self.adapter.validate_listing_url(url)
        return self.html

    def set_candidate(self, candidate):
        self.candidate = candidate

    def open_detail(self, url):
        self.adapter.validate_detail_url(url)
        if self.candidate is None:
            self.candidate = self.adapter.candidate_from_url(url)
        self.adapter.confirm_identity(self.candidate, self.html, url)
        return self.html

    def download(self, url, *, max_bytes):
        if url != PDF_URL:
            raise ValueError("replay URL diverges from preserved FAPESE edital")
        if len(self.pdf) > max_bytes:
            raise ValueError("preserved PDF exceeds configured limit")
        return DownloadedBytes(url_requested=url, url_final=url, content=self.pdf,
                               content_type="application/pdf", redirect_chain=[url],
                               downloaded_at=datetime.now(timezone.utc), mechanism="replay")

    def observed_json(self):
        return []

    def session_records(self):
        return []

    def replay_url(self):
        return None

    def diagnostics(self):
        return list(self._notes)

    def close(self):
        return None


def main():
    html = DETAIL.read_text(encoding="utf-8")
    pdf = PDF.read_bytes()
    adapter = get_source_adapter(SOURCE)
    settings = TenderProofSettings(
        allowlist_hosts=tuple(adapter.allowed_hosts),
        limits=TenderProofLimits(max_candidates=5, max_documents=10, max_pages=120,
                                 max_download_bytes=30 * 1024 * 1024, total_timeout_s=300),
    )
    store = TenderProofStore()
    service = TenderProofService(store, settings)
    def acquire(method):
        last = None
        for _ in range(90):
            try:
                return method()
            except TenderProofBusy as exc:
                last = exc
                time.sleep(5)
        raise last or RuntimeError("pilot acquisition lease did not become available")

    listing = acquire(lambda: service.start_discovery(
        ReplayDriver(html, pdf), source=SOURCE, listing_url=LISTING,
        mode="real", owner_user_id=1))
    candidate = next(c for c in listing.candidates if c.external_id == "007/2026")
    run = acquire(lambda: service.select_and_process(
        listing.run_id, candidate.candidate_id, ReplayDriver(html, pdf)))
    durable = store.get_run(run.run_id)
    assert durable is not None and durable.artifact is not None
    data = store.load_artifact_bytes(durable.artifact)
    assert data is not None and hashlib.sha256(data).hexdigest() == durable.artifact.sha256
    print({"run_id": run.run_id, "status": run.execution_status.value,
           "validation": run.validation_status.value, "fields": len(run.fields),
           "artifact_sha256": run.artifact.sha256, "artifact_bytes": run.artifact.byte_len,
           "durable": True, "network": False})


if __name__ == "__main__":
    main()
