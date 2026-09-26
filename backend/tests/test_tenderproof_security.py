"""TenderProof Fase 1 — allowlist, redirects, destinos privados e limites."""

import pytest

from app.tenderproof.security import (
    DEFAULT_ALLOWLIST,
    DestinationBlocked,
    TenderProofSettings,
    validate_destination,
    validate_redirect_chain,
)


def test_ibgp_hosts_are_allowed():
    assert validate_destination("https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp") == (
        "novo.ibgpconcursos.com.br"
    )
    assert validate_destination("https://novo.ibgpconcursos.com.br/rest/concurso/download/edital/1/?file=x") == (
        "novo.ibgpconcursos.com.br"
    )


def test_off_allowlist_host_is_rejected():
    with pytest.raises(DestinationBlocked):
        validate_destination("https://evil.example.com/edital.pdf")
    with pytest.raises(DestinationBlocked):
        validate_destination("https://ibgpconcursos.com.br.evil.com/x.pdf")


def test_private_local_and_metadata_destinations_are_rejected():
    for url in (
        "http://127.0.0.1/edital.pdf",
        "http://10.0.0.5/edital.pdf",
        "http://192.168.0.10/edital.pdf",
        "http://172.16.4.4/edital.pdf",
        "http://localhost:8000/edital.pdf",
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/x",
        "ftp://novo.ibgpconcursos.com.br/edital.pdf",
    ):
        try:
            validate_destination(url)
        except DestinationBlocked:
            continue
        raise AssertionError(f"destino deveria ser bloqueado: {url}")


def test_redirect_chain_validates_every_hop():
    ok = [
        "https://novo.ibgpconcursos.com.br/a",
        "https://novo.ibgpconcursos.com.br/b.pdf",
    ]
    assert validate_redirect_chain(ok) == ok[-1]
    with pytest.raises(DestinationBlocked):
        validate_redirect_chain([
            "https://novo.ibgpconcursos.com.br/a",
            "https://evil.example.com/b.pdf",
        ])


def test_extra_allowlist_hosts_are_configurable(monkeypatch):
    monkeypatch.setenv("TENDERPROOF_ALLOWLIST_EXTRA", "cdn.ibgp.example, arquivos.ibgp.example")
    settings = TenderProofSettings.from_env()
    assert "cdn.ibgp.example" in settings.allowlist_hosts
    assert validate_destination("https://arquivos.ibgp.example/edital.pdf", allowlist=settings.allowlist_hosts)


def test_limits_are_capped_and_concurrency_is_one(monkeypatch):
    monkeypatch.setenv("TENDERPROOF_MAX_CANDIDATES", "99")
    settings = TenderProofSettings.from_env()
    assert settings.limits.max_candidates == 5  # teto do MVP
    assert settings.limits.max_concurrency == 1
    assert settings.stealth is False and settings.proxy is None and settings.captcha is False
