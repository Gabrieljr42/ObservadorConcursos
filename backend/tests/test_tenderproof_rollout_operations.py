"""Controlled operational scenarios, never evidence of live source coverage."""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.auth import get_current_user
from app.models import User
from app.tenderproof.continuous import ContinuousEngine
from app.tenderproof.continuous_store import ContinuousStore, SourcePolicy
from app.tenderproof.continuous_router import router
from app.tenderproof.source_adapters import ListingPage, SOURCE_ADAPTERS
import pytest


def test_one_obsolete_source_does_not_stop_other_schedules(tmp_path, monkeypatch):
    monkeypatch.setenv("TENDERPROOF_CONTINUOUS_ENABLED", "true")
    monkeypatch.setenv("TENDERPROOF_CONTINUOUS_OPERATOR_USER_IDS", "1")
    queue = ContinuousStore(tmp_path / "queue.sqlite3")
    for source in ("ibgp_open", "imeso_open"):
        queue.configure(1, source, SourcePolicy(enabled=True), now=100)
    with queue._db(write=True) as db:
        db.execute("UPDATE source_config SET source='removed_source' WHERE source='ibgp_open'")
    cycles = ContinuousEngine(queue=queue).schedule_due(now=101)
    assert len(cycles) == 1
    assert queue.cycle(cycles[0], 1)["source"] == "imeso_open"


def test_metrics_measure_queue_and_snapshots_without_leaking_other_owner(tmp_path):
    queue = ContinuousStore(tmp_path / "queue.sqlite3")
    for owner in (1, 2):
        queue.configure(owner, "ibgp_open", SourcePolicy(enabled=True), now=100)
        queue.enqueue(owner, "ibgp_open", [SOURCE_ADAPTERS["ibgp_open"].listing_urls[0]], now=100)
    job = next(job for job in queue.ready_jobs(now=100) if queue.owner_for_job(job) == 1)
    lease = queue.claim(job, now=101)
    html = "<p>Nenhum concurso disponível.</p>"
    queue.complete_listing(lease, html, ListingPage(empty_evidence="explicit empty", terminal_evidence="explicit empty"), now=102)
    measured = queue.metrics(1, now=105)
    assert measured["jobs_by_status"] == {"succeeded": 1}
    assert measured["snapshot_pages"] == 1
    assert measured["snapshot_html_bytes"] == len(html.encode())
    assert measured["completed_cycles_by_source"][0]["mean_seconds"] == 2
    assert measured["oldest_ready_delay_seconds"] == 0
    other = queue.metrics(2, now=105)
    assert other["jobs_by_status"] == {"queued": 1}
    assert other["oldest_ready_delay_seconds"] == 5
    assert other["snapshot_pages"] == 0


def test_catalogue_auth_and_pending_sources_are_explicit():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    assert client.get("/tenderproof/continuous/catalogue").status_code == 401
    assert client.get("/tenderproof/continuous/metrics").status_code == 401
    app.dependency_overrides[get_current_user] = lambda: User(id=1, email="operator@example.test", is_active=True)
    rows = client.get("/tenderproof/continuous/catalogue").json()
    assert len(rows) == len({row["source"] for row in rows}) == 99
    assert [row["number"] for row in rows] == list(range(1, 100))
    for row in rows:
        assert row["adapter_registered"] == (row["source"] in SOURCE_ADAPTERS)
        assert row["adapter_implemented"] == (row["implementation_state"] == "implemented")
        if not row["adapter_registered"]:
            assert row["homologation"] == "pending_adapter"


def test_failed_principal_keeps_manifest_review_and_deduplicates(tmp_path):
    queue = ContinuousStore(tmp_path / "queue.sqlite3")
    adapter = SOURCE_ADAPTERS["ibgp_open"]
    candidate = adapter.candidate_from_url("https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42", "Exemplo")
    queue.configure(1, candidate.source, SourcePolicy(enabled=True, max_attempts=1), now=100)
    manifest = [{"title":"Retificação 01", "url":"https://novo.ibgpconcursos.com.br/retificacao.pdf", "kind":"outro"}]
    for now in (100, 4000):
        cycle = queue.enqueue(1, candidate.source, adapter.listing_urls, force=True, now=now)
        listing = next(j["job_id"] for j in queue.cycle(cycle, 1)["jobs"] if j["kind"] == "listing")
        lease = queue.claim(listing, now=now)
        queue.complete_listing(lease, "controlled listing", ListingPage(candidates=[candidate], terminal_evidence="controlled end"), now=now+1)
        detail = next(j["job_id"] for j in queue.cycle(cycle, 1)["jobs"] if j["kind"] == "detail")
        lease = queue.claim(detail, now=now+2)
        queue.set_run_id(lease, "controlled-failed-run", now=now+2)
        queue.detail_checkpoint(lease, "controlled detail", manifest, now=now+2)
        queue.fail(lease, "ambiguous_document", retryable=False, now=now+3)
    observations = queue.observations(1)
    assert len(observations) == 1
    summary = observations[0]["summary"]
    assert summary["validation_status"] == "document_review_required"
    assert summary["documents"] == manifest
    assert summary["document_bytes_verified"] is False
    assert observations[0]["last_seen"] == 4003
    with queue._db() as db:
        assert db.execute("SELECT last_valid_run_id FROM known_candidates").fetchone()[0] is None


@pytest.mark.parametrize('enabled', [False, True])
def test_detail_challenge_uses_only_authorized_fallback(monkeypatch, enabled):
    from app.tenderproof.http_driver import ContinuousDriver
    from app.tenderproof.source_adapters import SourcePageBlocked
    driver = ContinuousDriver('access_open', allow_browser=enabled)
    url = 'https://access.selecao.net.br/informacoes/183/'
    driver.http.candidate = driver.http.adapter.candidate_from_url(url)
    monkeypatch.setattr(driver.http, 'open_detail', lambda target:'<main>Verify you are human</main>')
    calls=[]
    class Browser:
        def open_detail(self, target):
            calls.append(target)
            return 'controlled rendered detail'
    monkeypatch.setattr(driver, '_fallback', lambda reason:Browser())
    try:
        if enabled:
            assert driver.open_detail(url) == 'controlled rendered detail'
            assert calls == [url]
        else:
            with pytest.raises(SourcePageBlocked):
                driver.open_detail(url)
            assert calls == []
    finally:
        driver.close()


def test_identity_error_never_triggers_detail_browser(monkeypatch):
    from app.tenderproof.http_driver import ContinuousDriver
    driver=ContinuousDriver('access_open', allow_browser=True)
    monkeypatch.setattr(driver.http, 'open_detail', lambda target:(_ for _ in ()).throw(ValueError('identity mismatch')))
    monkeypatch.setattr(driver, '_fallback', lambda reason:pytest.fail('identity error cannot open browser'))
    try:
        with pytest.raises(ValueError, match='identity'):
            driver.open_detail('https://access.selecao.net.br/informacoes/183/')
    finally:
        driver.close()
