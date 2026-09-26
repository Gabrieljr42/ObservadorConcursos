"""TenderProof Fase 1 — limites, allowlist e validação de destinos.

Decisões (documentadas para auditoria):

- Allowlist explícita: apenas o host oficial IBGP e hosts documentais
  verificados. Redirects para fora da allowlist são rejeitados.
- Destinos privados/locais/metadados de infraestrutura são bloqueados
  (10/8, 172.16/12, 192.168/16, 127/8, 169.254.169.254, ::1, .local etc.).
- Tamanho validado durante a transferência quando Content-Length existe e
  após o conteúdo real recebido.
- Concorrência fixa em 1 (execuções sob demanda, sem paralelismo).
"""

from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass, field
from urllib.parse import urlparse
from urllib.parse import unquote

# Hosts oficiais IBGP verificados no catálogo do projeto.
DEFAULT_ALLOWLIST: tuple[str, ...] = (
    "novo.ibgpconcursos.com.br",
    "ibgpconcursos.com.br",
    "portal.imeso.com.br",
    "cdn.imeso.com.br",
    "s3.us-east-1.amazonaws.com",
)

METADATA_HOSTS = {"169.254.169.254", "169.254.169.253", "metadata.google.internal"}
LOCAL_SUFFIXES = (".local", ".localhost", ".internal", ".lan", ".home", ".corp")


@dataclass(slots=True)
class TenderProofLimits:
    max_candidates: int = 5
    max_navigations: int = 12
    max_attempts: int = 2
    max_download_bytes: int = 30 * 1024 * 1024
    max_documents: int = 10
    max_concurrency: int = 1
    total_timeout_s: float = 300.0
    max_pages: int = 60
    # Observação de rede: teto de respostas JSON preservadas e tamanho útil.
    max_observed_json: int = 20
    max_json_bytes: int = 65536
    # Replay: prazo total de polling após o encerramento (sem reabrir browser).
    replay_deadline_s: float = 60.0
    replay_poll_interval_s: float = 5.0


@dataclass(slots=True)
class TenderProofSettings:
    allowlist_hosts: tuple[str, ...] = DEFAULT_ALLOWLIST
    limits: TenderProofLimits = field(default_factory=TenderProofLimits)
    stealth: bool = False
    proxy: str | None = None
    captcha: bool = False

    @classmethod
    def from_env(cls) -> TenderProofSettings:
        extra = os.getenv("TENDERPROOF_ALLOWLIST_EXTRA", "").strip()
        hosts = list(DEFAULT_ALLOWLIST)
        if extra:
            for item in extra.split(","):
                item = item.strip().lower().lstrip(".")
                if item and item not in hosts:
                    hosts.append(item)

        def _int(name: str, default: int) -> int:
            try:
                return int(os.getenv(name, str(default)))
            except ValueError:
                return default

        def _float(name: str, default: float) -> float:
            try:
                return float(os.getenv(name, str(default)))
            except ValueError:
                return default

        limits = TenderProofLimits(
            max_candidates=min(_int("TENDERPROOF_MAX_CANDIDATES", 5), 5),
            max_navigations=_int("TENDERPROOF_MAX_NAVIGATIONS", 12),
            max_attempts=_int("TENDERPROOF_MAX_ATTEMPTS", 2),
            max_download_bytes=_int("TENDERPROOF_MAX_DOWNLOAD_BYTES", 30 * 1024 * 1024),
            max_documents=_int("TENDERPROOF_MAX_DOCUMENTS", 10),
            max_concurrency=1,
            total_timeout_s=_float("TENDERPROOF_TOTAL_TIMEOUT_S", 300.0),
            max_pages=_int("TENDERPROOF_MAX_PAGES", 60),
            max_observed_json=_int("TENDERPROOF_MAX_OBSERVED_JSON", 20),
            max_json_bytes=_int("TENDERPROOF_MAX_JSON_BYTES", 65536),
            replay_deadline_s=_float("TENDERPROOF_REPLAY_DEADLINE_S", 60.0),
            replay_poll_interval_s=_float("TENDERPROOF_REPLAY_POLL_S", 5.0),
        )
        return cls(
            allowlist_hosts=tuple(hosts),
            limits=limits,
            stealth=os.getenv("TENDERPROOF_STEALTH", "false").lower() == "true",
            proxy=os.getenv("TENDERPROOF_PROXY") or None,
            captcha=os.getenv("TENDERPROOF_CAPTCHA", "false").lower() == "true",
        )


class DestinationBlocked(Exception):
    pass


def _host_allowed(host: str, allowlist: tuple[str, ...]) -> bool:
    host = host.lower().rstrip(".")
    for allowed in allowlist:
        allowed = allowed.lower().rstrip(".")
        if allowed == "s3.us-east-1.amazonaws.com":
            if host == allowed:
                return True
            continue
        if host == allowed or host.endswith("." + allowed):
            return True
    return False


def validate_destination(url: str, *, allowlist: tuple[str, ...] = DEFAULT_ALLOWLIST) -> str:
    """Valida um destino de navegação/download. Retorna o host normalizado.

    Levanta ``DestinationBlocked`` para: host fora da allowlist, IP literal
    privado/local, hostname local/metadados.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise DestinationBlocked(f"esquema não permitido: {parsed.scheme or '(ausente)'}")
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.username or parsed.password or parsed.port not in (None, 80, 443):
        raise DestinationBlocked("credenciais/porta não permitidas no destino")
    if host == "s3.us-east-1.amazonaws.com":
        path = unquote(parsed.path)
        if not path.startswith("/cdn.imeso.com.br/edital/") or any(p in (".", "..") for p in path.split("/")) or "\\" in path:
            raise DestinationBlocked("bucket/caminho S3 fora do escopo documental IMESO")
    if not host:
        raise DestinationBlocked("URL sem host")
    if host in METADATA_HOSTS:
        raise DestinationBlocked(f"host de metadados de infraestrutura bloqueado: {host}")
    if host == "localhost" or host.endswith(LOCAL_SUFFIXES):
        raise DestinationBlocked(f"destino local bloqueado: {host}")
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            raise DestinationBlocked(f"IP privado/local bloqueado: {host}")
        # IP público literal: exige allowlist reversa — por padrão, bloqueia,
        # pois os hosts oficiais são DNS, não literais.
        raise DestinationBlocked(f"IP literal não está na allowlist: {host}")
    except ValueError:
        pass
    if not _host_allowed(host, allowlist):
        raise DestinationBlocked(f"host fora da allowlist: {host}")
    return host


def validate_redirect_chain(
    urls: list[str],
    *,
    allowlist: tuple[str, ...] = DEFAULT_ALLOWLIST,
) -> str:
    """Valida cada salto de redirect. Retorna a URL final."""
    if not urls:
        raise DestinationBlocked("cadeia de redirects vazia")
    for url in urls:
        validate_destination(url, allowlist=allowlist)
    return urls[-1]
