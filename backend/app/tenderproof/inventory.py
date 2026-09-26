"""Read-only catalogue inventory and bounded public HTTP observations.

Planning evidence, not a source adapter or a certification of contests.
It never changes MASTER_SOURCES or invokes legacy collectors/publication.
"""
from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import json
import re
import socket
import ssl
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urldefrag, urljoin, urlsplit, urlunsplit

import httpx
from bs4 import BeautifulSoup

from app.connectors.registry import MASTER_SOURCES, DEDICATED_CLASSES
from app.tenderproof.security import DestinationBlocked, LOCAL_SUFFIXES, METADATA_HOSTS, validate_destination


PROBE_POLICY = {
    "concurrent_sources": 4,
    "max_response_bytes": 1024 * 1024,
    "request_timeout_seconds": 12,
    "total_timeout_seconds_per_url": 25,
    "max_redirects": 3,
    "max_detail_pages_per_source": 1,
    "tls_verified": True,
    "credentials": False,
    "allowed_destinations": "exact catalogue or explicitly reviewed redirect hosts, public DNS, HTTP(S), default ports",
    "document_content_fetched": False,
    "signed_link_query_values_retained": False,
}
SUPPORTED_SOURCES = {"ibgp_open", "imeso_open"}
SHARED_PLATFORMS = ("selecao.net.br", "selecao.site")
DETAIL_PATTERN = re.compile(
    r"/informacoes/\d+|/edital/ver/\d+|/concursos?/detalh\w*/|"
    r"/concursos?/\d+|concurso\.jsp\?.*\bcod=\d+|"
    r"[?&](?:id_concurso|idconcurso|concurso|codconcurso)=\d+", re.I
)
EMPLOYMENT_PATTERN = re.compile(r"concurso|processo\s+seletivo|sele[çc][aã]o\s+(?:de\s+)?pessoal|vaga|contrata[çc][aã]o", re.I)
OTHER_SCOPE_PATTERN = re.compile(r"bolsa|fomento|aux[íi]lio|inicia[çc][aã]o\s+cient[íi]fica|p[óo]s[- ]?doutor|pesquisador", re.I)
OTHER_DOCUMENT_PATTERN = re.compile(r"termos(?:[ _-]|%20)+(?:de(?:[ _-]|%20)+)?uso|termos\.pdf|pol[ií]tica|privacidade|estatuto|manual|guia|e-book|ebook|presta[çc][aã]o(?:[ _-]|%20)+de(?:[ _-]|%20)+contas", re.I)
OUTSIDE_CONTEST_PATTERN = re.compile(r"vestibular|licita[çc]|preg[aã]o|credenciamento.*(?:empresa|fornecedor)", re.I)
CONTEST_DOCUMENT_PATTERN = re.compile(r"edital|retifica|errata|cronograma|inscri|gabarito|classifica|convoca|resultado|anexo", re.I)
PERSONNEL_EXPLICIT_PATTERN = re.compile(r"contrata[çc][aã]o\s+(?:clt|tempor[áa]ri[ao]|de\s+pessoal)|concurso\s+p[úu]blico|sele[çc][aã]o\s+de\s+pessoal", re.I)
SENSITIVE_QUERY_KEYS = {"awsaccesskeyid", "signature", "credential", "token", "access_token", "key", "sig"}
PAGINATION_PATTERN = re.compile(r"[?&](?:page|pagina|p[aá]gina|offset|start)=\d+|/page/\d+|/pagina/\d+", re.I)
TABS_PATTERN = re.compile(r"abertos|em.andamento|encerrados|finalizados|previstos|homologados|todos", re.I)
# Exact targets observed in the strict public probe on 2026-09-07. These
# catalogue-owned HTTP redirects were reviewed individually; no suffix wildcard
# or catalogue mutation is used. New redirects still stop for review.
REVIEWED_REDIRECTS = {
    "msconcursos_open": ("https://www.msconcursos.com.br", "https://msconcursos.com.br/"),
    "facet_open": ("https://www.facetconcursos.com.br", "https://facetconcursos.com.br/"),
    "educapb_open": ("https://www.educapb.com.br", "https://educapb.com.br/"),
    "funvapi_open": ("https://www.funvapi.com.br", "https://funvapi.com.br/"),
    "elo_open": ("https://eloassessoriaeservicos.com.br/concursos", "https://novo.eloassessoriaeservicos.com.br//concursos"),
    "nossorumo_open": ("https://www.nossorumo.org.br", "https://nossorumo.org.br/"),
    "fapese_selection": ("https://fapese.org.br", "https://www.fapese.org.br/"),
    "fapern_selection": ("https://fapern.rn.gov.br", "https://www.fapern.rn.gov.br/"),
    "fapeal_selection": ("https://fapeal.br", "https://www.fapeal.br/"),
    "fappr_selection": ("https://fappr.pr.gov.br/Pagina/Processos-Seletivos", "https://www.fappr.pr.gov.br/Pagina/Processos-Seletivos"),
    "fapemat_selection": ("https://fapemat.mt.gov.br", "https://www.fapemat.mt.gov.br/"),
    "fapt_selection": ("https://fapt.to.gov.br", "https://www.to.gov.br/fapt/"),
    "fapespa_selection": ("https://fapespa.pa.gov.br", "https://www.fapespa.pa.gov.br/"),
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def catalogue_hosts(definition) -> tuple[str, ...]:
    return tuple(sorted({urlsplit(u).hostname for u in [definition.base_url, *definition.list_urls]}))


def family_of(definition) -> str:
    """Platform classification needs hostname evidence, not a connector class."""
    for platform in SHARED_PLATFORMS:
        if any(host == platform or host.endswith("." + platform) for host in catalogue_hosts(definition)):
            return platform
    return "institutional_portal" if definition.category == "institutional_selection" else "own_portal"


def _identity_groups() -> list[dict]:
    by_name = defaultdict(list)
    for definition in MASTER_SOURCES:
        by_name[definition.banca.casefold().strip()].append(definition)
    return [{"group": key, "sources": [d.source_type for d in definitions],
             "status": "candidate_alias_not_merged", "evidence": "same banca label in canonical catalogue",
             "action": "confirmar sobreposição de concursos e IDs antes de reconciliar"}
            for key, definitions in by_name.items() if len(definitions) > 1]


def build_inventory(historical: dict | None = None) -> dict:
    history = {s["source_type"]: s for s in (historical or {}).get("sources", [])}
    aliases = _identity_groups()
    alias_by_source = {source: group for group in aliases for source in group["sources"]}
    rows = []
    for number, definition in enumerate(MASTER_SOURCES, 1):
        source = definition.source_type
        previous = history.get(source, {})
        family = family_of(definition)
        supported = source in SUPPORTED_SOURCES
        priority = 1 if supported else 2 if family in SHARED_PLATFORMS else 4 if definition.category == "institutional_selection" else 3
        alias = alias_by_source.get(source)
        row = {
            "number": number, "source_type": source, "name": definition.name, "banca": definition.banca,
            "category": definition.category, "family": family,
            "family_basis": "catalogue hostname suffix" if family in SHARED_PLATFORMS else "catalogue category; no shared platform yet established",
            "canonical_group": alias["group"] if alias else source,
            "identity_status": alias["status"] if alias else "no_catalogue_alias_detected",
            "base_url": definition.base_url, "listing_urls": list(definition.list_urls),
            "allowed_probe_hosts": list(catalogue_hosts(definition)),
            "frequency_minutes": definition.frequency_minutes,
            "legacy_connector": getattr(DEDICATED_CLASSES.get(source), "__name__", "InstitutionalSelectionConnector" if definition.category == "institutional_selection" else "ConfigurableHTMLConnector"),
            "legacy_verification": previous.get("verification_status", "NOT_AUDITED"),
            "legacy_crawler_status": previous.get("crawler_status"),
            "legacy_audit_at": (historical or {}).get("generated_at"),
            "legacy_error_type": previous.get("error_type"),
            "legacy_tls_verified": definition.verify_ssl,
            "tenderproof_adapter": "implemented_two_source_scope" if supported else "pending",
            "priority": priority,
            "priority_reason": {1: "consolidar as duas fontes já implementadas", 2: "reuso por plataforma comprovada no endereço catalogado", 3: "adaptar portal próprio após o piloto", 4: "revisar escopo institucional antes de ativar"}[priority],
            "scope": "seleção/contratação de pessoas; excluir fomento e bolsas acadêmicas" if definition.category == "institutional_selection" else "concursos e processos seletivos",
            "scope_status": "requires_item_filter" if definition.category == "institutional_selection" else "contest_scope_pending_item_validation",
            "discovery_strategy": "HTTP/HTML com núcleo comum e particularidades por fonte; verificar abas, paginação, detalhes e documentos",
            "configured_detail_patterns": list(definition.detail_url_patterns),
            "pending": [], "url_observations": [], "detail_observations": [],
        }
        if family in SHARED_PLATFORMS:
            row["discovery_strategy"] = f"avaliar aquisição compartilhada {family}; identidade e documentos continuam específicos por fonte"
        row["reviewed_redirects"] = []
        if source in REVIEWED_REDIRECTS:
            origin, destination = REVIEWED_REDIRECTS[source]
            if origin not in row["listing_urls"]:
                raise ValueError("reviewed redirect origin no longer belongs to the catalogue")
            row["allowed_probe_hosts"] = sorted(set(row["allowed_probe_hosts"]) | {urlsplit(destination).hostname})
            row["reviewed_redirects"].append({"from": origin, "to": destination,
                "evidence": "HTTP redirect from catalogue URL observed 2026-09-07T22:54:22Z–22:54:42Z",
                "decision": "public read-only destination approved for inventory only; canonical catalogue unchanged"})
        rows.append(row)
    catalogue = [{"source_type": r["source_type"], "banca": r["banca"], "category": r["category"],
                  "base_url": r["base_url"], "listing_urls": r["listing_urls"]} for r in rows]
    inventory = {"schema_version": 2, "generated_at": now(), "scope": "inventory_and_bounded_public_http_probe",
        "quality_note": "HTTP/links não comprovam correção, cobertura, vigência nem homologação TenderProof. Nenhuma fonte nova foi ativada.",
        "catalogue_path": "backend/app/connectors/registry.py", "catalogue_sha256": hashlib.sha256(json.dumps(catalogue, sort_keys=True).encode()).hexdigest(),
        "historical_audit": {"path": "backend/audit_live_99.json", "generated_at": (historical or {}).get("generated_at"),
                             "verification_counts": dict(Counter(r["legacy_verification"] for r in rows))},
        "priority_policy": "prioridade de implementação derivada de reuso e escopo; não é nota de qualidade ou vigência",
        "probe_policy": dict(PROBE_POLICY), "total_sources": len(rows), "identity_groups": aliases,
        "families": dict(Counter(r["family"] for r in rows)), "categories": dict(Counter(r["category"] for r in rows)), "sources": rows}
    summarize_inventory(inventory)
    return inventory


async def public_dns(host: str) -> None:
    answers = await asyncio.wait_for(asyncio.get_running_loop().getaddrinfo(host, 443, type=socket.SOCK_STREAM), 5)
    if not answers or any(not ipaddress.ip_address(a[4][0]).is_global for a in answers):
        raise ValueError("DNS não público")


def _failure(exc: Exception) -> dict:
    """Keep a diagnostic code; never emit environment, headers or exception text."""
    chain, current = [], exc
    while current is not None and len(chain) < 8 and current not in chain:
        chain.append(current)
        current = current.__cause__ or current.__context__
    if any(getattr(item, "winerror", None) == 10013 or "WinError 10013" in str(item) for item in chain):
        code, reason = "local_network_denied", "rede local recusou acesso ao socket (WinError 10013); não diagnostica o portal"
    elif any(isinstance(item, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in str(item) for item in chain):
        code, reason = "tls_verification_failed", "certificado TLS não pôde ser verificado; não houve tentativa sem verificação"
    elif any(isinstance(item, socket.gaierror) for item in chain):
        code, reason = "dns_resolution_failed", "nome não resolvido neste ambiente; confirmar endereço e DNS"
    elif isinstance(exc, (TimeoutError, httpx.TimeoutException)):
        code, reason = "timeout", "prazo de DNS, transporte ou total da URL excedido"
    elif isinstance(exc, DestinationBlocked):
        code, reason = "destination_review_required", "destino fora dos hosts exatos catalogados ou URL não permitida; redirect não seguido"
    elif isinstance(exc, ValueError):
        code, reason = "probe_limit_or_destination", "limite de redirects, ciclo ou DNS não público; observar a cadeia registrada"
    else:
        code, reason = "transport_error", "falha de transporte; investigar separadamente de qualidade do conteúdo"
    return {"state": code, "error_type": type(exc).__name__, "reason": reason}


def _safe_link(href: str, base: str) -> str | None:
    try:
        url = urldefrag(urljoin(base, href.strip()))[0]
        parsed = urlsplit(url)
        if parsed.scheme not in ("https", "http") or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 80, 443):
            return None
        host = parsed.hostname.lower()
        if host == "localhost" or host in METADATA_HOSTS or host.endswith(LOCAL_SUFFIXES):
            return None
        try:
            if not ipaddress.ip_address(host).is_global:
                return None
        except ValueError:
            pass
        query = parse_qsl(parsed.query, keep_blank_values=True)
        if any(key.casefold() in SENSITIVE_QUERY_KEYS or key.casefold().startswith("x-amz-") for key, _ in query):
            # Signed public links are evidence of a link, not credentials to keep.
            url = urlunsplit(parsed._replace(query=""))
        return url
    except ValueError:
        return None


def document_role_hint(link: dict) -> str:
    """URL/label triage only; personnel text can disambiguate a generic folder."""
    context = link["label"] + " " + link.get("context", "")
    description = unquote(link["url"]) + " " + context
    if OTHER_DOCUMENT_PATTERN.search(description):
        return "generic_site_document"
    if OTHER_SCOPE_PATTERN.search(context) or OUTSIDE_CONTEST_PATTERN.search(context):
        return "outside_contest_scope_candidate"
    if PERSONNEL_EXPLICIT_PATTERN.search(context):
        return "contest_document_candidate"
    if OTHER_SCOPE_PATTERN.search(description) or OUTSIDE_CONTEST_PATTERN.search(description):
        return "outside_contest_scope_candidate"
    return "contest_document_candidate" if CONTEST_DOCUMENT_PATTERN.search(description) else "unclassified_document"


def inspect_html(raw: bytes, base_url: str, detail_patterns: list[str] | None = None) -> dict:
    """Structural/link evidence only. A zero count never means a verified empty."""
    soup = BeautifulSoup(raw, "html.parser")
    links, seen, discarded = [], set(), 0
    for anchor in soup.select("a[href]"):
        url = _safe_link(str(anchor["href"]), base_url)
        if not url:
            discarded += 1
            continue
        if url in seen:
            continue
        seen.add(url)
        label = anchor.get_text(" ", strip=True) or str(anchor.get("title", "")) or str(anchor.get("aria-label", ""))
        context = label
        if not label or label.casefold().strip() in ("download", "baixar", "edital", "resultado", "aviso", "errata", "abrir", "clique aqui", "acessar proposta"):
            for ancestor in list(anchor.parents)[:4]:
                if ancestor.name in ("body", "html", "[document]"):
                    break
                nearby = ancestor.get_text(" ", strip=True)
                if len(nearby) > len(context) and len(nearby) <= 600:
                    context = nearby
                    break
        original_query = urlsplit(urljoin(base_url, str(anchor["href"]))).query
        links.append({"label": label[:220], "url": url, "context": context[:600],
                      "query_redacted": bool(original_query and not urlsplit(url).query)})
    docs = [link for link in links if re.search(r"\.pdf(?:$|[?&/])|/download(?:$|/|[.?])|/baixar(?:$|/|[.?])", link["url"], re.I)]
    for link in docs:
        link["document_role_hint"] = document_role_hint(link)
    docs.sort(key=lambda link: {"contest_document_candidate": 0, "unclassified_document": 1, "outside_contest_scope_candidate": 2, "generic_site_document": 3}[link["document_role_hint"]])
    patterns = [DETAIL_PATTERN, *(re.compile(pattern, re.I) for pattern in detail_patterns or [])]
    details = [link for link in links if link not in docs and any(pattern.search(link["url"]) for pattern in patterns)]
    pages = [link for link in links if PAGINATION_PATTERN.search(link["url"]) or re.fullmatch(r"pr[óo]xim[ao]|seguinte|next|[»›]", link["label"], re.I)]
    tabs = [link for link in links if TABS_PATTERN.search(urlsplit(link["url"]).path + " " + link["label"]) and len(link["label"]) < 90]
    other = [link for link in links if OTHER_SCOPE_PATTERN.search(link["label"] + " " + unquote(link["url"])) or OUTSIDE_CONTEST_PATTERN.search(link["label"] + " " + unquote(link["url"]))]
    employment = [link for link in links if EMPLOYMENT_PATTERN.search(link["label"]) and link not in other]
    markup = raw.decode("utf-8", errors="ignore").lower()
    technology = []
    for name, markers in {"wordpress": ("/wp-content/", "/wp-includes/"), "aspnet": ("__viewstate", "__eventvalidation"),
                          "sharepoint": ("/_layouts/", "_sppagecontextinfo"), "joomla": ("joomla!",),
                          "nextjs": ("__next_data__", "/_next/"), "nuxt": ("__nuxt", "/_nuxt/")}.items():
        if any(marker in markup for marker in markers):
            technology.append({"technology": name, "basis": "HTML marker; reuse hypothesis, not adapter certification"})
    for label, pattern in (("edital_ver", r"/edital/ver/\d+"), ("informacoes_id", r"/informacoes/\d+")):
        if any(re.search(pattern, link["url"]) for link in links):
            technology.append({"technology": label, "basis": "observed link structure; platform vendor unconfirmed"})
    for platform in SHARED_PLATFORMS:
        hosted_links = [link for link in links if (urlsplit(link["url"]).hostname or "").endswith("." + platform)]
        if hosted_links:
            technology.append({"technology": f"linked_host:{platform}", "basis": "asset or document link on platform domain; candidate for reuse, not full platform certification",
                               "evidence_url": hosted_links[0]["url"]})
    visible = soup.get_text(" ", strip=True)
    challenge = any(marker in visible.casefold() for marker in ("verify you are human", "just a moment", "checking your browser", "enable javascript and cookies", "verifique se você é humano"))
    return {"title": soup.title.get_text(" ", strip=True)[:200] if soup.title else None,
            "links_observed": len(links), "document_links_observed": len(docs), "document_samples": docs[:5],
            "document_sample_role_counts": dict(Counter(link["document_role_hint"] for link in docs[:5])),
            "discarded_non_http_private_or_credential_links": discarded,
            "document_scope": "links observados nesta página; bytes, identidade, vigência e relevância dos documentos não validados",
            "detail_links_observed": len(details), "detail_link_samples": details[:5],
            "pagination_samples": pages[:5], "status_tab_samples": tabs[:8], "technology_hints": technology,
            "scope_signals": {"personnel_or_contest_link_samples": employment[:4], "possible_funding_or_scholarship_link_samples": other[:4],
                              "basis": "triagem lexical; decisão de escopo exige leitura do edital"},
            "rendering_hint": "sparse_html_requires_browser_or_api_investigation" if len(visible) < 180 and len(soup.select("script")) > 0 else "html_observed",
            "challenge_marker": challenge}


async def probe_url(client: httpx.AsyncClient, url: str, allowed_hosts: tuple[str, ...], *, detail_patterns: list[str] | None = None) -> dict:
    report = {"requested_url": url, "observed_at": now(), "redirects": [], "body_complete": False}
    current, seen = url, set()
    try:
        for _ in range(PROBE_POLICY["max_redirects"] + 1):
            host = validate_destination(current, allowlist=allowed_hosts)
            if host not in allowed_hosts:
                raise DestinationBlocked("exact catalogue host required")
            await public_dns(host)
            if current in seen:
                raise ValueError("redirect circular")
            seen.add(current)
            async with client.stream("GET", current) as response:
                report.update(http_status=response.status_code, final_url=str(response.url))
                if response.is_redirect:
                    target = urljoin(current, response.headers.get("location", ""))
                    report["redirects"].append({"from": current, "to": _safe_link(target, current) or "[blocked invalid/private/credential destination]", "status": response.status_code})
                    current = target
                    continue
                content_type = response.headers.get("content-type", "")
                report["content_type"] = content_type
                if not any(value in content_type.lower() for value in ("text/", "html", "json", "xml")):
                    report.update(state="non_html_response", reason="tipo de conteúdo não textual; corpo não transferido nesta sondagem")
                    return report
                chunks, size = [], 0
                async for chunk in response.aiter_bytes(chunk_size=16384):
                    size += len(chunk)
                    if size > PROBE_POLICY["max_response_bytes"]:
                        report.update(state="response_too_large", bytes=size, reason="resposta excede 1 MiB; corpo parcial descartado")
                        return report
                    chunks.append(chunk)
                raw = b"".join(chunks)
                report.update(bytes=size, sha256=hashlib.sha256(raw).hexdigest(), body_complete=True)
                report.update(inspect_html(raw, current, detail_patterns))
                report["state"] = "blocked_or_challenge" if report.pop("challenge_marker") or response.status_code in (401, 403, 429) else "http_observed" if response.is_success else "http_error"
                return report
        raise ValueError("limite de redirects")
    except Exception as exc:
        report.update(_failure(exc))
        return report


def summarize_inventory(inventory: dict) -> None:
    reuse_groups = defaultdict(set)
    for row in inventory["sources"]:
        observations = row["url_observations"] + row["detail_observations"]
        for observation in observations:
            if "document_samples" in observation:
                for sample in observation["document_samples"]:
                    sample["document_role_hint"] = document_role_hint(sample)
                observation.pop("document_role_counts", None)
                observation["document_sample_role_counts"] = dict(Counter(sample["document_role_hint"] for sample in observation["document_samples"]))
                observation["sample_classification_version"] = 2
            if observation["state"] == "http_observed":
                for hint in observation.get("technology_hints", []):
                    reuse_groups[hint["technology"]].add(row["source_type"])
        pending = ["validar cobertura contínua e documentos em ciclos repetidos"] if row["source_type"] in SUPPORTED_SOURCES else ["implementar e homologar adaptador TenderProof; confirmar identidade, paginação e vazio"]
        if row["identity_status"] == "candidate_alias_not_merged":
            pending.append("reconciliar alias Consulplan sem duplicar concursos; catálogo preservado")
        if not row["legacy_tls_verified"]:
            pending.append("legado desativa TLS; nova aquisição mantém verificação")
        if row["category"] == "institutional_selection":
            pending.append("filtrar seleção de pessoas por edital; fomento e bolsas acadêmicas ficam fora do catálogo de concursos")
        states = {o["state"] for o in observations}
        for state, action in {
            "destination_review_required": "revisar novo endereço de redirect antes de ampliar hosts permitidos",
            "tls_verification_failed": "confirmar cadeia/certificado TLS sem desativar verificação",
            "dns_resolution_failed": "revalidar domínio catalogado e resolução DNS",
            "blocked_or_challenge": "investigar bloqueio por navegador/API oficial e política da fonte",
            "timeout": "repetir acesso limitado e verificar latência da fonte",
            "transport_error": "investigar transporte/rede; falha não comprova ausência de concursos",
            "local_network_denied": "repetir em ambiente com rede autorizada; falha é local",
            "http_error": "revisar rota catalogada e resposta HTTP recebida",
            "response_too_large": "planejar leitura paginada ou limite específico para página grande",
            "probe_limit_or_destination": "revisar ciclo/limite de redirect ou resolução não pública",
            "non_html_response": "revisar tipo da resposta e estratégia de aquisição",
        }.items():
            if state in states:
                pending.append(action)
        successful = [o for o in observations if o["state"] == "http_observed"]
        documents = {sample["url"] for observation in successful for sample in observation.get("document_samples", [])}
        contest_documents = {sample["url"] for observation in successful for sample in observation.get("document_samples", [])
                             if sample.get("document_role_hint") == "contest_document_candidate"}
        row["document_evidence"] = {"status": "links_observed_unvalidated" if documents else "no_document_link_in_bounded_sample" if successful else "not_observed",
                                    "sample_distinct_links": len(documents), "sample_contest_candidate_links": len(contest_documents),
                                    "content_verified": False, "role_hint_is_lexical_not_validation": True}
        if row["reviewed_redirects"]:
            pending.append("avaliar atualização do endereço canônico a partir do redirect observado; catálogo preservado")
        if successful and not contest_documents:
            pending.append("localizar documentos nas páginas de detalhe/API; amostra sem links não significa ausência")
        if any(o.get("rendering_hint", "").startswith("sparse_html") for o in successful):
            pending.append("identificar API pública ou navegação necessária para a página com pouco HTML")
        if any(o.get("pagination_samples") for o in successful):
            pending.append("percorrer paginação observada; sondagem não seguiu todas as páginas")
        if any("temporariamente suspenso" in (o.get("title") or "").casefold() for o in observations):
            pending.append("portal informa suspensão temporária; acompanhar retomada e preservar último dado válido")
        if not observations:
            pending.append("executar sondagem pública atual dos endereços catalogados")
        row["pending"] = pending
        row["current_observation"] = "some_http_content_observed" if successful else "access_requires_investigation" if observations else "not_probed"
        row["acquisition_recommendation"] = {
            "initial_method": "public_http",
            "browser_or_official_api_investigation": "blocked_or_challenge" in states or any(o.get("rendering_hint", "").startswith("sparse_html") for o in successful),
            "basis": "observed page structure/access; no new source is enabled by this recommendation",
        }
    listings = [o for row in inventory["sources"] for o in row["url_observations"]]
    details = [o for row in inventory["sources"] for o in row["detail_observations"]]
    inventory["probe_counts"] = dict(Counter(o["state"] for o in listings))
    inventory["detail_probe_counts"] = dict(Counter(o["state"] for o in details))
    inventory["observed_reuse_candidates"] = [
        {"technology": technology, "sources": sorted(sources), "source_count": len(sources),
         "status": "HTML/link evidence only; contracts and document identity still require homologation"}
        for technology, sources in sorted(reuse_groups.items()) if len(sources) > 1
    ]
    inventory["current_summary"] = {
        "listing_urls_catalogued": sum(len(r["listing_urls"]) for r in inventory["sources"]),
        "listing_urls_probed": len(listings), "sample_detail_urls_probed": len(details),
        "source_observation_counts": dict(Counter(r["current_observation"] for r in inventory["sources"])),
        "sources_with_document_links_in_sample": sum(r["document_evidence"]["status"] == "links_observed_unvalidated" for r in inventory["sources"]),
        "sources_with_contest_document_candidates_in_sample": sum(bool(r["document_evidence"]["sample_contest_candidate_links"]) for r in inventory["sources"]),
        "new_tenderproof_sources_certified": 0,
    }


async def probe_inventory(inventory: dict, *, sample_details: bool = True, progress=None) -> dict:
    semaphore = asyncio.Semaphore(PROBE_POLICY["concurrent_sources"])
    inventory["probe_started_at"] = now()
    async with httpx.AsyncClient(timeout=PROBE_POLICY["request_timeout_seconds"], follow_redirects=False, trust_env=False, verify=True,
                                headers={"User-Agent": "ObservadorDeConcursos/1.0 (public source verification)"}) as client:
        async def observe(url, row, kind):
            try:
                result = await asyncio.wait_for(probe_url(client, url, tuple(row["allowed_probe_hosts"]), detail_patterns=row["configured_detail_patterns"]), PROBE_POLICY["total_timeout_seconds_per_url"])
            except TimeoutError as exc:
                result = {"requested_url": url, "observed_at": now(), **_failure(exc)}
            result["page_kind"] = kind
            return result

        async def inspect(row):
            async with semaphore:
                row["url_observations"], row["detail_observations"] = [], []
                for url in row["listing_urls"]:
                    row["url_observations"].append(await observe(url, row, "catalogue_listing"))
                if sample_details:
                    details = [sample["url"] for o in row["url_observations"] if o["state"] == "http_observed"
                               for sample in o.get("detail_link_samples", []) if urlsplit(sample["url"]).hostname in row["allowed_probe_hosts"]]
                    if details:
                        row["detail_observations"].append(await observe(details[0], row, "sample_detail_not_full_coverage"))
                if progress:
                    progress(row)
        await asyncio.gather(*(inspect(row) for row in inventory["sources"]))
    inventory["probe_completed_at"] = now()
    summarize_inventory(inventory)
    return inventory


def write_inventory(inventory: dict, destination: Path) -> None:
    summarize_inventory(inventory)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = inventory["current_summary"]
    history = inventory["historical_audit"]
    lines = ["# Inventário das 99 fontes — TenderProof", "", f"Gerado: {inventory['generated_at']}", "",
             inventory["quality_note"], "", f"Catálogo: **{inventory['total_sources']} fontes**, sendo **{inventory['categories'].get('banca', 0)} bancas** e **{inventory['categories'].get('institutional_selection', 0)} seleções institucionais**. O inventário preserva todos os IDs.", "",
             f"Sondagem atual: {summary['listing_urls_probed']}/{summary['listing_urls_catalogued']} endereços de listagem e {summary['sample_detail_urls_probed']} detalhes amostrados. {summary['sources_with_document_links_in_sample']} fontes tiveram links documentais na amostra; em {summary['sources_with_contest_document_candidates_in_sample']} há candidatos lexicais a documentos de concursos. Conteúdo e identidade desses documentos ainda exigem validação. PDFs de privacidade, manuais, vestibulares e fomento são classificados à parte.", "",
             f"Respostas de listagem: {json.dumps(inventory['probe_counts'], ensure_ascii=False, sort_keys=True)}.", "",
             f"Auditoria histórica separada: {history['generated_at'] or 'indisponível'}; {json.dumps(history['verification_counts'], sort_keys=True)}. Os resultados HTTP atuais não substituem essas avaliações de qualidade.", "",
             "Prioridade de implementação: 1 = consolidar IBGP/IMESO; 2 = endereço em plataforma compartilhada; 3 = portal próprio; 4 = seleção institucional com triagem de escopo. Não representa urgência, qualidade ou vigência.", "",
             "selecao.net.br e selecao.site são famílias comprovadas pelo endereço cadastrado. Outros sinais (WordPress, ASP.NET, rotas /edital/ver ou /informacoes) constam como hipóteses no JSON. Mesma tecnologia não comprova o mesmo contrato documental.", "",
             "| # | Fonte / listagem catalogada | Família | Prioridade | Auditoria histórica | Sondagem atual | Docs candidatos / total amostrado | Pendências |",
             "|---|---|---|---|---|---|---|---|"]
    for row in inventory["sources"]:
        observed = "; ".join(f"{o['state']} ({o.get('http_status', '—')})" for o in row["url_observations"]) or "não executada"
        source = f"[{row['name']}]({row['listing_urls'][0]})"
        cells = [row["number"], source, row["family"], row["priority"], row["legacy_verification"], observed,
                 f"{row['document_evidence']['sample_contest_candidate_links']} / {row['document_evidence']['sample_distinct_links']}", "; ".join(row["pending"])]
        lines.append("| " + " | ".join(str(c).replace("|", "/").replace("\n", " ") for c in cells) + " |")
    lines += ["", "## Navegação observada nas fontes já implementadas", ""]
    for row in inventory["sources"]:
        if row["source_type"] not in SUPPORTED_SOURCES:
            continue
        tabs = [link for observation in row["url_observations"] for link in observation.get("status_tab_samples", [])]
        description = "; ".join(f"[{link['label'] or 'rota'}]({link['url']})" for link in tabs) or "nenhuma aba encontrada em anchors da amostra; formulários/JavaScript exigem inspeção específica"
        lines.append(f"- {row['banca']}: {description}. Paginação e fim da listagem não foram certificados pela sondagem.")
    lines += ["", "## Reuso, identidade e escopo", "",
              "Consulplan e Instituto Consulplan compartilham o nome de banca no catálogo e permanecem como **alias candidato**, sem fusão automática de fontes ou concursos. A reconciliação exige comparar editais, IDs e órgãos.", "",
              "As 36 seleções institucionais exigem decisão por edital. Links com bolsa/fomento/pesquisador foram separados de sinais de concurso/contratação no JSON; essa triagem lexical não exclui uma instituição inteira nem publica oportunidades acadêmicas como concursos.", "",
              "Grupos adicionais candidatos a reuso, derivados do HTML e dos links atuais: " + "; ".join(f"{g['technology']} ({g['source_count']} fontes)" for g in inventory["observed_reuse_candidates"]) + ". As evidências e as fontes de cada grupo estão no JSON; esses grupos não promovem automaticamente a prioridade nem habilitam adaptadores.", "",
              "## Como reproduzir e interpretar", "",
              "Execute, a partir de backend: .venv/Scripts/python.exe scripts/tenderproof_inventory.py --live. Para gerar apenas a matriz do catálogo, omita --live. Use --listing-only para dispensar a amostra de detalhe.", "",
              "A sondagem usa quatro fontes concorrentes, até 1 MiB de texto por resposta, 25 s por URL e três redirects. Examina todas as listagens cadastradas e até um detalhe com URL observado por fonte. Downloads PDF não são feitos. TLS permanece verificado e destinos devem resolver publicamente. Treze redirects observados na primeira sondagem pública foram revisados explicitamente (onze variantes www, o subdomínio novo da Elo e o portal do governo de Tocantins); o catálogo permanece intacto. Outros novos hosts param para revisão. Nunca se usa login, cookies de navegador ou credenciais. Assinaturas em queries de links documentais são removidas dos artefatos e URLs privadas descartadas.", "",
              "local_network_denied identifica recusa local de socket (WinError 10013), e não falha da banca. DNS, TLS, timeouts, HTTP e destinos pendentes têm estados separados. Um 200 pode ser HTML vazio, bloqueio, página institucional ou listagem parcial; não prova concursos atuais nem cobertura completa.", "",
              "O JSON adjacente preserva URLs, horários, hashes dos corpos completos, cadeias de redirect, tecnologia sugerida pelo HTML, abas/paginação, amostras de detalhe/documentos e sinais de escopo. A auditoria anterior permanece identificada pela data e não é sobrescrita."]
    destination.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
