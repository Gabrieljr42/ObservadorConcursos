"""Inventory evidence must not become false source certification or unsafe I/O."""
import asyncio
import copy
import json
import socket
import ssl
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qsl, urlsplit

import httpx
import pytest

from app.connectors.registry import MASTER_SOURCES
from app.tenderproof import inventory as module


def test_exact_catalogue_and_history_are_preserved():
    original_urls = [list(d.list_urls) for d in MASTER_SOURCES]
    historical = {"generated_at": "2026-08-30T17:00:00Z", "sources": [
        {"source_type": "imeso_open", "verification_status": "BROKEN", "crawler_status": "success"}
    ]}
    original_history = copy.deepcopy(historical)
    result = module.build_inventory(historical)
    rows = result["sources"]
    assert result["total_sources"] == 99
    assert result["categories"] == {"banca": 63, "institutional_selection": 36}
    assert [r["source_type"] for r in rows] == [d.source_type for d in MASTER_SOURCES]
    assert [r["listing_urls"] for r in rows] == original_urls
    assert len({r["source_type"] for r in rows}) == 99
    assert historical == original_history
    assert sum(r["tenderproof_adapter"] != "pending" for r in rows) == 2
    row = next(r for r in rows if r["source_type"] == "imeso_open")
    row["url_observations"] = [{"state": "http_observed", "http_status": 200, "document_samples": []}]
    module.summarize_inventory(result)
    assert row["legacy_verification"] == "BROKEN"
    assert row["legacy_audit_at"] == historical["generated_at"]
    assert row["document_evidence"]["status"] == "no_document_link_in_bounded_sample"
    assert row["document_evidence"]["content_verified"] is False
    assert result["current_summary"]["new_tenderproof_sources_certified"] == 0
    assert [list(d.list_urls) for d in MASTER_SOURCES] == original_urls


def test_reuse_uses_exact_platform_suffix_and_aliases_do_not_merge():
    result = module.build_inventory()
    groups = result["identity_groups"]
    assert groups == [{
        "group": "instituto consulplan",
        "sources": ["consulplan_open", "institutoconsulplan_open"],
        "status": "candidate_alias_not_merged",
        "evidence": "same banca label in canonical catalogue",
        "action": "confirmar sobreposição de concursos e IDs antes de reconciliar",
    }]
    assert result["families"] == {"own_portal": 56, "selecao.net.br": 5, "selecao.site": 2, "institutional_portal": 36}
    spoof = SimpleNamespace(base_url="https://selecao.net.br.evil.example/", list_urls=["https://example.com/selecao.site"], category="banca")
    assert module.family_of(spoof) == "own_portal"
    rows = {r["source_type"]: r for r in result["sources"]}
    assert rows["ibgp_open"]["priority"] == 1
    assert rows["access_open"]["priority"] == 2
    assert rows["fapemig_selection"]["priority"] == 4
    assert rows["fapemig_selection"]["scope_status"] == "requires_item_filter"
    assert all(r["pending"] and r["priority_reason"] for r in result["sources"])


def test_reviewed_redirects_are_explicit_and_do_not_change_catalogue():
    result = module.build_inventory()
    rows = {r["source_type"]: r for r in result["sources"]}
    assert len(module.REVIEWED_REDIRECTS) == 13
    assert rows["elo_open"]["listing_urls"] == ["https://eloassessoriaeservicos.com.br/concursos"]
    assert rows["elo_open"]["allowed_probe_hosts"] == ["eloassessoriaeservicos.com.br", "novo.eloassessoriaeservicos.com.br"]
    assert rows["elo_open"]["reviewed_redirects"][0]["to"] == "https://novo.eloassessoriaeservicos.com.br//concursos"
    assert rows["ibgp_open"]["allowed_probe_hosts"] == ["novo.ibgpconcursos.com.br"]


def test_html_samples_separate_site_documents_and_scope_and_redact_signed_queries():
    html = """
        <meta charset="utf-8"><title>Seleções</title><script src="/wp-content/thing.js"></script>
        <a href="/termos.pdf">Termos de uso</a>
        <a href="/politicas.pdf">Privacidade</a>
        <div class="row">Edital 1/2026 Concurso público
          <span><a href="https://cdn.example.org/edital/1/a.pdf?AWSAccessKeyId=secret&Signature=private">DOWNLOAD</a></span>
        </div>
        <a href="/bolsas.pdf">Bolsas de pós-doutorado</a>
        <a href="/vestibular.pdf">Edital Vestibular</a>
        <a href="http://192.168.188.2/private.pdf">Privado</a>
        <a href="https://username:password@public.example/hidden.pdf">Credenciais</a>
        <a href="https://metadata.google.internal/edital.pdf">Metadados</a>
        <a href="javascript:alert(1)">ação</a>
        <a href="/informacoes/12">Concurso A</a>
        <a href="?page=2">Próxima</a>
        <a href="/index/encerrados/">Encerrados</a>
    """
    result = module.inspect_html(html.encode(), "https://public.example/lista")
    assert result["document_links_observed"] == 5
    assert result["document_sample_role_counts"] == {
        "generic_site_document": 2, "contest_document_candidate": 1, "outside_contest_scope_candidate": 2,
    }
    first = result["document_samples"][0]
    assert first["url"] == "https://cdn.example.org/edital/1/a.pdf"
    assert first["query_redacted"] is True
    assert first["document_role_hint"] == "contest_document_candidate"
    assert "Edital 1/2026" in first["context"]
    encoded = json.dumps(result)
    for forbidden in ("secret", "private.pdf", "password", "AWSAccessKeyId", "192.168.188.2", "metadata.google.internal"):
        assert forbidden not in encoded
    assert result["detail_links_observed"] == 1
    assert result["pagination_samples"][0]["url"] == "https://public.example/lista?page=2"
    assert result["status_tab_samples"][0]["label"] == "Encerrados"
    assert result["technology_hints"][0]["technology"] == "wordpress"
    assert len(result["scope_signals"]["possible_funding_or_scholarship_link_samples"]) == 2


def test_empty_script_shell_is_not_reported_as_no_contests():
    observation = module.inspect_html(b"<html><div id='root'></div><script src='bundle.js'></script></html>", "https://public.example/")
    assert observation["rendering_hint"] == "sparse_html_requires_browser_or_api_investigation"
    assert observation["document_links_observed"] == 0
    assert "empty" not in observation


def test_personnel_selection_is_not_excluded_for_a_generic_licitacoes_folder():
    link = {"label": "EDITAL", "url": "https://official.example/doc.licitacoes/edital.pdf",
            "context": "CONTRATAÇÃO CLT: ANALISTA DE PROJETOS. PROCESSO SELETIVO 1/2026"}
    assert module.document_role_hint(link) == "contest_document_candidate"
    link["context"] = "Pregão para compra de equipamentos"
    assert module.document_role_hint(link) == "outside_contest_scope_candidate"


async def _public(host):
    return None


def _run_probe(monkeypatch, handler, url="https://source.example/lista", hosts=("source.example",)):
    monkeypatch.setattr(module, "public_dns", _public)
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await module.probe_url(client, url, hosts)
    return asyncio.run(run())


@pytest.mark.parametrize("destination", [
    "https://external.example/",
    "https://unreviewed.source.example/",
    "http://127.0.0.1/private",
    "https://user:password@source.example/",
])
def test_redirects_never_fetch_unapproved_destinations(monkeypatch, destination):
    requested = []
    def handler(request):
        requested.append(str(request.url))
        return httpx.Response(302, headers={"location": destination})
    result = _run_probe(monkeypatch, handler)
    assert result["state"] == "destination_review_required"
    assert requested == ["https://source.example/lista"]
    assert len(result["redirects"]) == 1


def test_approved_redirect_keeps_evidence_and_http_200_is_only_observation(monkeypatch):
    requested = []
    def handler(request):
        requested.append(str(request.url))
        if request.url.path == "/lista":
            return httpx.Response(301, headers={"location": "/listagem"})
        return httpx.Response(200, headers={"content-type": "text/html"}, text="<title>Concursos</title><a href='/a.pdf'>Edital 1/2026</a>")
    result = _run_probe(monkeypatch, handler)
    assert requested == ["https://source.example/lista", "https://source.example/listagem"]
    assert result["state"] == "http_observed"
    assert result["body_complete"] is True
    assert len(result["sha256"]) == 64
    assert result["document_links_observed"] == 1
    assert result["final_url"].endswith("/listagem")
    assert "verified" not in result


@pytest.mark.parametrize("status,body", [
    (200, "<title>Just a moment...</title>Verify you are human"),
    (403, "Forbidden"),
    (429, "Too many requests"),
])
def test_challenges_and_limits_are_not_valid_empty_sources(monkeypatch, status, body):
    result = _run_probe(monkeypatch, lambda request: httpx.Response(status, headers={"content-type": "text/html"}, text=body))
    assert result["state"] == "blocked_or_challenge"
    assert result["http_status"] == status


def test_response_limit_does_not_emit_complete_body_hash(monkeypatch):
    monkeypatch.setitem(module.PROBE_POLICY, "max_response_bytes", 1000)
    result = _run_probe(monkeypatch, lambda request: httpx.Response(200, headers={"content-type": "text/html"}, content=b"x" * 3000))
    assert result["state"] == "response_too_large"
    assert result["body_complete"] is False
    assert "sha256" not in result


def test_non_html_body_is_not_downloaded_as_part_of_inventory(monkeypatch):
    result = _run_probe(monkeypatch, lambda request: httpx.Response(200, headers={"content-type": "application/pdf"}, content=b"%PDF-1.4"))
    assert result["state"] == "non_html_response"
    assert result["body_complete"] is False
    assert "sha256" not in result


def test_failure_diagnostics_distinguish_local_denial_tls_dns_and_timeout():
    cases = [
        (httpx.ConnectError("[WinError 10013] blocked secret-environment"), "local_network_denied"),
        (ssl.SSLCertVerificationError("CERTIFICATE_VERIFY_FAILED secret"), "tls_verification_failed"),
        (socket.gaierror("not found secret"), "dns_resolution_failed"),
        (httpx.ConnectTimeout("secret"), "timeout"),
    ]
    for exception, expected in cases:
        output = module._failure(exception)
        assert output["state"] == expected
        assert "secret" not in json.dumps(output)


def test_dns_rejects_mixed_public_and_private_answers(monkeypatch):
    async def run():
        async def resolve(*args, **kwargs):
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("8.8.8.8", 443)),
                (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("127.0.0.1", 443)),
            ]
        monkeypatch.setattr(asyncio.get_running_loop(), "getaddrinfo", resolve)
        await module.public_dns("source.example")
    with pytest.raises(ValueError, match="DNS não público"):
        asyncio.run(run())


def test_repeated_probe_replaces_current_observations_and_bounds_detail_reads(monkeypatch):
    result = module.build_inventory()
    result["sources"] = [result["sources"][0]]
    row = result["sources"][0]
    row["url_observations"] = [{"state": "local_network_denied"}]
    requested = []
    async def mock_probe(client, url, hosts, **kwargs):
        requested.append(url)
        return {"state": "http_observed", "requested_url": url, "document_samples": [],
                "detail_link_samples": [{"url": row["base_url"] + "/informacoes/1"},
                                        {"url": row["base_url"] + "/informacoes/2"},
                                        {"url": "https://external.example/informacoes/3"}]}
    monkeypatch.setattr(module, "probe_url", mock_probe)
    asyncio.run(module.probe_inventory(result))
    assert len(row["url_observations"]) == 1
    assert len(row["detail_observations"]) == 1
    assert len(requested) == 2
    assert requested[-1].endswith("/informacoes/1")
    assert result["probe_counts"] == {"http_observed": 1}


def test_json_and_markdown_write_complete_matrix_with_history_and_limits(tmp_path):
    result = module.build_inventory()
    destination = tmp_path / "sources.json"
    module.write_inventory(result, destination)
    restored = json.loads(destination.read_text(encoding="utf-8"))
    markdown = destination.with_suffix(".md").read_text(encoding="utf-8")
    assert restored["total_sources"] == 99
    assert len([line for line in markdown.splitlines() if line.startswith("| ")]) == 100
    assert "Auditoria histórica separada" in markdown
    assert "Downloads PDF não são feitos" in markdown
    assert restored["probe_policy"]["tls_verified"] is True
    assert restored["current_summary"]["listing_urls_catalogued"] == 103


def test_public_inventory_artifact_covers_every_catalogue_listing_with_safe_evidence():
    path = Path(__file__).resolve().parents[2] / "docs" / "tenderproof-sources-99.json"
    result = json.loads(path.read_text(encoding="utf-8"))
    expected = module.build_inventory()
    assert result["catalogue_sha256"] == expected["catalogue_sha256"]
    assert result["total_sources"] == 99
    assert result["current_summary"]["listing_urls_probed"] == 103
    assert result["probe_completed_at"] >= result["probe_started_at"]
    assert result["current_summary"]["new_tenderproof_sources_certified"] == 0
    assert sum(result["probe_counts"].values()) == 103
    for row, expected_row in zip(result["sources"], expected["sources"], strict=True):
        assert row["source_type"] == expected_row["source_type"]
        assert row["listing_urls"] == expected_row["listing_urls"]
        assert [o["requested_url"] for o in row["url_observations"]] == row["listing_urls"]
        assert len(row["detail_observations"]) <= 1
        assert row["document_evidence"]["content_verified"] is False
        for observation in row["url_observations"] + row["detail_observations"]:
            assert observation["observed_at"]
            assert observation["state"] != "local_network_denied"
            if observation.get("body_complete"):
                assert len(observation["sha256"]) == 64
                assert observation["bytes"] <= result["probe_policy"]["max_response_bytes"]
            for sample in observation.get("document_samples", []):
                parsed = urlsplit(sample["url"])
                assert not parsed.username and not parsed.password
                assert module._safe_link(sample["url"], sample["url"]) == sample["url"]
                assert all(key.casefold() not in module.SENSITIVE_QUERY_KEYS and not key.casefold().startswith("x-amz-")
                           for key, _ in parse_qsl(parsed.query))
