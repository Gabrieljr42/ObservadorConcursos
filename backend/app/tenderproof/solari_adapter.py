"""TenderProof — adaptador Solari com ciclo de vida real por etapa.

Verificado contra o SDK Python instalado (``solari-browser==0.1.3``) e
``docs.getsolari.com``:

- ``Solari(api_key, region='us-west', base_url=None)`` com contexto assíncrono;
  ``await solari.launch(recording=..., stealth=..., proxy=..., captcha=...)``
  devolve ``BrowserSession`` (patchright 1.62.x via wire protocol; o SDK traz
  o próprio cliente — sem ``patchright install chromium``).
- ``BrowserSession``: ``.id``, ``await new_page()``, ``await close()``
  (fecha o browser e envia DELETE via ``release_and_wait``; idempotente).
  O SDK 0.1.3 não faz polling nessa função: esta aplicação exige GET com
  status released/expired antes de registrar encerramento confirmado. Também aceita
  ``async with``.
- Replay: ``await solari.sessions.get_replay_url(session_id)`` →
  ``ReplayUrl(url, expires_in_seconds, ...)``; fica pronto alguns segundos
  após o ``close`` — daí o polling limitado **após** o encerramento, sem
  reabrir browser. ``SolariError`` carrega ``status``/``code`` (404 =
  ainda não disponível).
- Downloads no Python 1.62: ``page.expect_download()`` + ``download.path()`` /
  ``save_as()`` — **sem** ``create_read_stream``. O SDK materializa o arquivo
  antes da verificação de tamanho: aplicamos pré-checagem de Content-Length
  quando disponível (fallback via request) e pós-checagem obrigatória, com
  remoção do temporário. Limitação documentada, não streaming real.
- Captura de rede: ``page.on("response", ...)`` registrado **antes** da
  navegação; corpos lidos após a navegação só para URLs relevantes, com teto
  de quantidade/tamanho. Sem cookies, tokens ou cabeçalhos armazenados.

Ciclo de vida (nunca manter browser aberto esperando seleção humana):

- ``open_listing``: sessão curta própria (abre → navega → fecha → replay).
- ``open_detail``: abre sessão que **permanece aberta** para compartilhar
  contexto com ``download``/``observed_json``.
- ``download``: reutiliza o contexto do detalhe (clique com espera prévia;
  fallback para request no mesmo contexto).
- ``close``: encerra, faz polling do replay e libera a ponte assíncrona.
  Idempotente, nunca levanta; encerramento depende de confirmação remota.

Ponte sync/async: cada adaptador mantém uma thread com event loop próprio;
objetos assíncronos nascem e morrem dentro dela (sem leaks entre
``asyncio.run``). Prazo total por fase via ``wait_for`` além dos timeouts
por ação.
"""

from __future__ import annotations

from app.tenderproof.pdf_header import has_pdf_header
from app.tenderproof.solari_budget import configured_budget

import asyncio
import hashlib
import json
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Protocol, TypeVar

from app.tenderproof.security import TenderProofSettings, validate_destination, validate_redirect_chain

T = TypeVar("T")


async def confirm_browser_released(client: Any, session_id: str, timeout: float = 8.0) -> bool:
    """DELETE acknowledgement is not closure: require a terminal provider GET.

    The installed SDK release_and_wait only issues DELETE (and accepts 404).
    A missing/failed GET remains unknown; never infer termination from 404.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            response = await asyncio.wait_for(client.sessions.get(session_id),
                timeout=max(0.01, min(3.0, deadline - time.monotonic())))
        except Exception:
            return False
        state = response.get("status") if isinstance(response, dict) else getattr(response, "status", None)
        if state in ("released", "expired"):
            return True
        if state != "active":
            return False
        await asyncio.sleep(min(0.5, max(0.0, deadline - time.monotonic())))
    return False

_RESPONSE_WATCH_SUBSTRING = "/rest/concurso"
_GOTO_TIMEOUT_MS = 45_000
_WAIT_ANCHOR_TIMEOUT_MS = 15_000
_DOWNLOAD_TIMEOUT_MS = 60_000


@dataclass(slots=True)
class SolariConfig:
    api_key: str | None = None
    base_url: str | None = None
    region: str = "us-west"
    recording: bool = True
    stealth: bool = False
    proxy: str | None = None
    captcha: bool = False

    @classmethod
    def from_env(cls) -> SolariConfig:
        return cls(
            api_key=os.getenv("SOLARI_API_KEY"),
            base_url=os.getenv("SOLARI_BASE_URL") or None,
            region=os.getenv("SOLARI_REGION", "us-west"),
            recording=os.getenv("TENDERPROOF_RECORDING", "true").lower() != "false",
            stealth=os.getenv("TENDERPROOF_STEALTH", "false").lower() == "true",
            proxy=os.getenv("TENDERPROOF_PROXY") or None,
            captcha=os.getenv("TENDERPROOF_CAPTCHA", "false").lower() == "true",
        )

    @property
    def configured(self) -> bool:
        return bool(self.api_key)


@dataclass(slots=True)
class ObservedJson:
    url: str
    status: int
    # Caminho do campo em resposta JSON (ex.: "meta.nome") — preenchido pelo
    # serviço quando um campo específico é observado.
    json_path: str | None = None
    payload: Any = None


@dataclass(slots=True)
class SessionRecord:
    phase: str  # "discovery" | "detail"
    session_id: str | None = None
    replay_url: str | None = None
    replay_status: str = "pending"  # available | pending | disabled | failed
    replay_note: str | None = None
    closed: bool = False
    close_requested: bool = False


@dataclass(slots=True)
class DownloadedBytes:
    url_requested: str
    url_final: str
    content: bytes
    content_type: str | None = None
    redirect_chain: list[str] = field(default_factory=list)
    downloaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # Mecanismo efetivo: "click" (expect_download) ou "request" (mesmo contexto).
    mechanism: str = "request"
    pagination_headers: dict[str, str] = field(default_factory=dict)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


class SolariNotConfigured(Exception):
    """Credenciais Solari ou SDK ausentes: verificação real pendente."""


class HtmlBlockError(ValueError):
    """O download materializou HTML (bloqueio/erro) em vez de PDF."""


class SolariDriver(Protocol):
    """Protocolo síncrono mínimo para aquisição rastreável."""

    session_id: str | None

    def open_listing(self, url: str) -> str:
        """Abre a listagem e retorna o HTML após espera real."""
        ...

    def open_detail(self, url: str) -> str:
        """Abre o detalhe do concurso e retorna o HTML (sessão mantida)."""
        ...

    def observed_json(self) -> list[ObservedJson]:
        ...

    def download(self, url: str, *, max_bytes: int) -> DownloadedBytes:
        ...

    def replay_url(self) -> str | None:
        """Link temporário do replay, se já disponível (pode ser None)."""
        ...

    @property
    def replay_available(self) -> bool:
        ...

    def session_records(self) -> list[SessionRecord]:
        """Sessões por etapa, com estado do replay."""
        ...

    def diagnostics(self) -> list[str]:
        """Notas operacionais (sem segredos)."""
        ...

    def close(self) -> None:
        """Encerra a sessão. Idempotente; seguro em ``finally``."""
        ...


def _get_solari_class() -> Any:
    """Seam de importação (substituível por doubles nos testes)."""
    import solari_browser

    return solari_browser.Solari


def _get_solari_error_class() -> Any:
    import solari_browser.errors

    return solari_browser.errors.SolariError


async def poll_replay_url(
    config: SolariConfig,
    session_id: str,
    *,
    budget_s: float,
    interval_s: float,
) -> tuple[str, str | None, str]:
    """Consulta o replay só pelo control-plane (sem browser).

    Retorna (status, url|None, nota). 404 = ainda não disponível (pending);
    sem recording = disabled; outro erro = failed com motivo higienizado.
    """
    if not config.recording:
        return "disabled", None, "recording desativado na configuração"
    if not session_id:
        return "failed", None, "sessão sem ID; replay impossível"
    error_class = _get_solari_error_class()
    cls = _get_solari_class()
    kwargs: dict[str, Any] = {"api_key": config.api_key, "region": config.region}
    if config.base_url:
        kwargs["base_url"] = config.base_url
    client = cls(**kwargs)
    started = time.monotonic()
    attempts = 0
    last_note = "não disponível ainda"
    try:
        await client.__aenter__()
        try:
            while time.monotonic() - started < budget_s:
                attempts += 1
                try:
                    remaining = max(0.01, budget_s - (time.monotonic() - started))
                    result = await asyncio.wait_for(client.sessions.get_replay_url(session_id), timeout=remaining)
                    url = result.url if hasattr(result, "url") else result.get("url")
                    if not url:
                        return "failed", None, "resposta de replay sem URL"
                    return "available", url, f"disponível após {attempts} tentativa(s)"
                except TimeoutError:
                    return "pending", None, "consulta de replay excedeu o prazo; sem nova sessão"
                except Exception as exc:  # noqa: BLE001
                    if isinstance(exc, error_class) and (
                        getattr(exc, "status", None) == 404
                    ):
                        last_note = f"tentativa {attempts}: ainda não disponível"
                        await asyncio.sleep(min(interval_s, max(0, budget_s - (time.monotonic() - started))))
                        continue
                    return "failed", None, SolariBrowserAdapter._safe_error(exc)
        finally:
            try:
                await client.__aexit__(None, None, None)
            except BaseException:  # noqa: BLE001
                pass
    except BaseException as exc:  # noqa: BLE001 - cliente nem abriu
        return "failed", None, SolariBrowserAdapter._safe_error(exc)
    return "pending", None, f"{last_note}; prazo de {budget_s:.0f}s esgotado sem reabrir o browser"


class FakeSolariDriver:
    """Driver scriptado para testes offline. Material sintético explícito."""

    def __init__(
        self,
        *,
        listing_html: str = "",
        detail_html: str = "",
        observed: list[ObservedJson] | None = None,
        downloads: dict[str, DownloadedBytes] | None = None,
        session_id: str = "fake-session-001",
        replay_url: str | None = "https://replay.example/fake-session-001",
        fail_on: str | None = None,
    ) -> None:
        self._listing_html = listing_html
        self._detail_html = detail_html
        self._observed = list(observed or [])
        self._downloads = dict(downloads or {})
        self.session_id: str | None = session_id
        self._replay_url = replay_url
        self._fail_on = fail_on
        self.closed = False
        self.opened_urls: list[str] = []
        self.close_calls = 0

    def open_listing(self, url: str) -> str:
        if self._fail_on == "listing":
            raise RuntimeError("falha simulada na listagem")
        self.opened_urls.append(url)
        return self._listing_html

    def open_detail(self, url: str) -> str:
        if self._fail_on == "detail":
            raise RuntimeError("falha simulada no detalhe")
        self.opened_urls.append(url)
        return self._detail_html

    def observed_json(self) -> list[ObservedJson]:
        return list(self._observed)

    def download(self, url: str, *, max_bytes: int) -> DownloadedBytes:
        if self._fail_on == "download":
            raise RuntimeError("falha simulada no download")
        payload = self._downloads.get(url)
        if payload is None:
            raise RuntimeError(f"download não scriptado para {url}")
        if len(payload.content) > max_bytes:
            raise ValueError(f"conteúdo acima do limite de {max_bytes} bytes")
        return payload

    def replay_url(self) -> str | None:
        return self._replay_url

    @property
    def replay_available(self) -> bool:
        return self._replay_url is not None

    def session_records(self) -> list[SessionRecord]:
        return [
            SessionRecord(
                phase="discovery",
                session_id=self.session_id,
                replay_url=self._replay_url,
                replay_status="available" if self._replay_url else "pending",
                closed=self.closed,
            )
        ]

    def diagnostics(self) -> list[str]:
        return ["fake: material sintético, sem sessão real"]

    def close(self) -> None:
        self.close_calls += 1
        self.closed = True


class _AsyncBridge:
    """Thread com event loop próprio para a ponte sync/async do adaptador."""

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()

    def _serve(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._ready.set()
        self._loop.run_forever()

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._serve, daemon=True, name="tenderproof-solari")
        self._thread.start()
        self._ready.wait(timeout=10)

    def run(self, coro: Coroutine[Any, Any, T], *, timeout: float | None) -> T:
        self.start()
        assert self._loop is not None
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        try:
            return future.result(timeout=timeout)
        except TimeoutError:
            # Dá chance à limpeza (finally/except fecham o browser) antes de
            # devolver o controle; a sessão nunca deve vazar no timeout.
            future.cancel()
            try:
                future.result(timeout=10)
            except BaseException:  # noqa: BLE001 - o erro original prevalece
                pass
            raise

    def stop(self) -> None:
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread is not None:
            self._thread.join(timeout=10)
        self._thread = None
        self._loop = None


class SolariBrowserAdapter:
    """Adaptador real (opt-in). Exige ``solari-browser`` + ``SOLARI_API_KEY``.

    Não simula sucesso: sem credencial/SDK, levanta ``SolariNotConfigured``.
    """

    def __init__(
        self,
        config: SolariConfig | None = None,
        settings: TenderProofSettings | None = None,
        *,
        source: str = "ibgp_open",
        session_observer: Callable[[str, str | None], None] | None = None,
    ) -> None:
        self.config = config or SolariConfig.from_env()
        self.settings = settings or TenderProofSettings.from_env()
        from app.tenderproof.source_adapters import get_source_adapter
        self.source_adapter = get_source_adapter(source)
        self._session_observer = session_observer
        self._budget = configured_budget()
        self.session_id: str | None = None
        self._records: list[SessionRecord] = []
        self._diagnostics: list[str] = []
        self._observed: list[ObservedJson] = []
        self._bridge = _AsyncBridge()
        self._live: dict[str, Any] | None = None  # solari/browser/page da etapa detail
        self._cancel_state: dict[str, Any] | None = None  # para limpeza emergencial
        self._closed = False
        self._shutdown_in_progress = False
        self._detail_deadline: float | None = None

    # -- verificações -------------------------------------------------
    def _require(self) -> None:
        if not self.config.configured:
            raise SolariNotConfigured(
                "SOLARI_API_KEY ausente. Exporte localmente (ex.: $env:SOLARI_API_KEY=...; "
                "nunca pelo chat) e repita a execução real. Testes offline usam FakeSolariDriver."
            )
        try:
            _get_solari_class()
        except ImportError as exc:
            raise SolariNotConfigured(
                "Pacote 'solari-browser' não instalado. Verificação real pendente."
            ) from exc

    # -- protocolo síncrono -------------------------------------------
    def open_listing(self, url: str) -> str:
        self._require()
        self.source_adapter.validate_listing_url(url)
        validate_destination(url, allowlist=self.settings.allowlist_hosts)
        total = self.settings.limits.total_timeout_s
        try:
            return self._bridge.run(self._listing_flow(url), timeout=total)
        except TimeoutError as exc:
            self._emergency_close()
            raise TimeoutError(f"discovery excedeu o prazo total de {total:.0f}s") from exc
        except Exception:
            self._emergency_close()
            raise

    def open_detail(self, url: str) -> str:
        self._require()
        self.source_adapter.validate_detail_url(url)
        validate_destination(url, allowlist=self.settings.allowlist_hosts)
        if self._live is not None:
            raise RuntimeError("sessão de detalhe já aberta; encerre antes de reabrir")
        total = min(self.settings.limits.total_timeout_s, 240.0)
        self._detail_deadline = time.monotonic() + total
        try:
            return self._bridge.run(self._detail_flow(url), timeout=total)
        except TimeoutError as exc:
            self._emergency_close()
            self._abort_live()
            raise TimeoutError(f"detalhe excedeu o prazo total de {total:.0f}s") from exc
        except Exception:
            self._emergency_close()
            raise

    def observed_json(self) -> list[ObservedJson]:
        return list(self._observed)

    def download(self, url: str, *, max_bytes: int) -> DownloadedBytes:
        self._require()
        if self._live is None:
            raise RuntimeError("download exige detalhe aberto na mesma sessão (open_detail primeiro)")
        total = max(0.01, (self._detail_deadline or time.monotonic()) - time.monotonic())
        try:
            return self._bridge.run(self._download_flow(url, max_bytes), timeout=total)
        except TimeoutError as exc:
            raise TimeoutError(f"download excedeu o prazo total de {total:.0f}s") from exc

    def replay_url(self) -> str | None:
        for record in reversed(self._records):
            if record.replay_url:
                return record.replay_url
        return None

    @property
    def replay_available(self) -> bool:
        return any(r.replay_status == "available" and r.replay_url for r in self._records)

    def session_records(self) -> list[SessionRecord]:
        return list(self._records)

    def diagnostics(self) -> list[str]:
        return list(self._diagnostics)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._shutdown_in_progress = True
        try:
            if self._live is not None:
                try:
                    self._bridge.run(self._close_live_flow(), timeout=30)
                except Exception as exc:  # noqa: BLE001 - close nunca levanta
                    self._note(f"close: falha ao encerrar sessão ({self._safe_error(exc)}); encerramento não confirmado")
                    self._mark_live_closed()
                # Replay em orçamento próprio e limitado: nunca estoura o close
                # nem reabre browser; pode ser reconsultado depois pelo console.
                try:
                    budget = min(self.settings.limits.replay_deadline_s, 45.0)
                    interval = self.settings.limits.replay_poll_interval_s
                    self._bridge.run(self._poll_replay_flow("detail", budget, interval), timeout=budget + 20)
                except Exception as exc:  # noqa: BLE001
                    self._note(f"close: replay adiado ({self._safe_error(exc)})")
        finally:
            try:
                self._bridge.stop()
            except Exception:  # noqa: BLE001
                pass

    # -- fluxos assíncronos --------------------------------------------
    def _launch_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"recording": self.config.recording, "stealth": self.config.stealth, "retries": 0}
        if self.config.proxy:
            kwargs["proxy"] = self.config.proxy
        if self.config.captcha:
            kwargs["captcha"] = True
        return kwargs

    def _new_client(self) -> Any:
        cls = _get_solari_class()
        assert self.config.api_key
        # The SDK otherwise retries POST /sessions after uncertain responses;
        # that could create a second paid resource outside our durable journal.
        kwargs: dict[str, Any] = {"api_key": self.config.api_key, "region": self.config.region,
                                  "max_attempts": 1, "timeout_ms": 30000}
        if self.config.base_url:
            kwargs["base_url"] = self.config.base_url
        return cls(**kwargs)

    async def _budgeted_launch(self, solari):
        reservation = None
        if self._budget:
            if self.config.proxy or self.config.captcha or self.config.stealth:
                raise ValueError('Orçamento atual cobre somente navegador sem recursos adicionais')
            # Provider maximum, not our shorter job timeout: ambiguous creates
            # must remain reserved until their full possible lifetime is covered.
            maximum = os.getenv('TENDERPROOF_SOLARI_BROWSER_MAX_LIFETIME_SECONDS')
            if not maximum:
                raise ValueError('Verificar duração máxima do plano Solari antes da criação paga')
            reservation = self._budget.reserve('browser', maximum_seconds=maximum,
                hourly_usd='0.15', tariff='https://docs.getsolari.com/pricing; 2026-09-08; conservative Free browser rate')
        browser = await solari.launch(**self._launch_kwargs())
        if reservation:
            try:
                self._budget.created(reservation, browser.id)
            except Exception:
                await browser.close()
                raise
        return browser

    async def _listing_flow(self, url: str) -> str:
        self._shutdown_in_progress = False
        session_id: str | None = None
        solari_cm = self._new_client()
        solari = await solari_cm.__aenter__()
        browser = None
        try:
            if self._session_observer:
                self._session_observer("creating", None)
            browser = await self._budgeted_launch(solari)
            self._register_cancel(browser, solari_cm)
            self._cancel_state["phase"] = "discovery"
            session_id = browser.id
            self.session_id = session_id
            if self._session_observer:
                self._session_observer("created", session_id)
            page = await browser.new_page()
            self._attach_capture(page)
            async with self._navigation_guard(page, url, phase="discovery") as navigation:
                await navigation.goto()
                await self._await_listing_ready(page)
                await self._drain_capture()
                navigation.check()
                html = await page.content()
                navigation.check()
            record = SessionRecord(phase="discovery", session_id=session_id, closed=False)
            self._records.append(record)
            try:
                record.close_requested = True
                self._shutdown_in_progress = True
                await browser.close()  # inclui release_and_wait
                record.closed = await confirm_browser_released(solari, session_id)
            except BaseException as exc:
                self._note(f"discovery: browser.close falhou ({self._safe_error(exc)}); encerramento não confirmado")
            self._observe_closed(record)
            browser = None
            await self._fill_replay(record)
            return html
        except BaseException as exc:
            self._note(f"discovery: {self._safe_error(exc)}")
            raise
        finally:
            # Sem awaits pesados aqui: em tarefa cancelada eles falhariam; a
            # limpeza emergencial (corrotina nova) fecha o browser se restou.
            if browser is None:
                self._clear_cancel()
            try:
                await solari_cm.__aexit__(None, None, None)
            except BaseException:  # noqa: BLE001
                pass

    def _register_cancel(self, browser: Any, solari_cm: Any) -> None:
        self._cancel_state = {"browser": browser, "solari": solari_cm}

    def _clear_cancel(self) -> None:
        self._cancel_state = None

    def _observe_closed(self, record: SessionRecord) -> None:
        if record.closed and self._budget:
            self._budget.closed(record.session_id)
        if record.closed and self._session_observer:
            try:
                self._session_observer("closed", record.session_id)
            except Exception as exc:
                self._note("journal: fechamento remoto confirmado, mas persistência falhou ("
                           + self._safe_error(exc) + ")")
                raise

    def _emergency_close(self) -> None:
        """Fecha browser/cliente restantes numa corrotina NOVA (não cancelada)."""
        state, self._cancel_state = self._cancel_state, None
        if not state:
            return
        self._shutdown_in_progress = True

        record = next((r for r in self._records if r.session_id == state["browser"].id), None)
        if record is None:
            record = SessionRecord(phase=state.get("phase", "detail"), session_id=state["browser"].id)
            self._records.append(record)

        async def _close() -> None:
            try:
                record.close_requested = True
                await state["browser"].close()
                record.closed = await confirm_browser_released(state["solari"], state["browser"].id)
            except BaseException:
                record.replay_note = "limpeza emergencial sem confirmação de encerramento"
            finally:
                try:
                    self._observe_closed(record)
                finally:
                    try:
                        await state["solari"].__aexit__(None, None, None)
                    except BaseException:  # noqa: BLE001
                        pass

        try:
            self._bridge.run(_close(), timeout=20)
        except BaseException:  # noqa: BLE001
            pass
        self._note("limpeza emergencial: encerramento " + ("confirmado" if record.closed else "não confirmado"))

    async def _detail_flow(self, url: str) -> str:
        self._shutdown_in_progress = False
        solari_cm = self._new_client()
        solari = await solari_cm.__aenter__()
        browser = None
        try:
            if self._session_observer:
                self._session_observer("creating", None)
            browser = await self._budgeted_launch(solari)
            self._register_cancel(browser, solari_cm)
            self.session_id = browser.id
            if self._session_observer:
                self._session_observer("created", browser.id)
            page = await browser.new_page()
            self._attach_capture(page)
            navigation = self._navigation_guard(page, url, phase="detail")
            await navigation.__aenter__()
            await navigation.goto()
            await self._open_ibgp_edital_section(page, url)
            try:
                await page.locator("a[href$='.pdf'], a[href*='download']").first.wait_for(
                    timeout=_WAIT_ANCHOR_TIMEOUT_MS
                )
            except Exception:  # noqa: BLE001 - ausência de âncora não aborta
                self._note("detail: nenhuma âncora de documento aguardada a tempo")
            await self._drain_capture()
            navigation.check()
            html = await page.content()
            navigation.check()
            self._live = {"solari": solari_cm, "browser": browser, "page": page,
                          "session_id": browser.id, "navigation_guard": navigation}
            self._clear_cancel()
            return html
        except BaseException:
            if browser is None:
                try:
                    await solari_cm.__aexit__(None, None, None)
                except BaseException:
                    pass
            # Once a browser exists, the caller closes it in a fresh coroutine
            # so cancellation cannot prevent the emergency cleanup.
            raise

    def _expected_shutdown_error(self, exc: BaseException, *, stopping: bool | Callable[[], bool] = False) -> bool:
        is_stopping = stopping() if callable(stopping) else stopping
        if not (is_stopping or self._shutdown_in_progress):
            return False
        if isinstance(exc, asyncio.CancelledError):
            return True
        # Use the SDK's exception type, not a substring that could hide an
        # unrelated navigation or persistence failure with a similar message.
        try:
            from patchright._impl._errors import TargetClosedError
        except ImportError:
            return False
        return isinstance(exc, TargetClosedError)

    async def _cleanup_browser_call(self, operation: Callable, *, stopping: bool | Callable[[], bool] = False) -> None:
        try:
            await operation()
        except BaseException as exc:
            if not self._expected_shutdown_error(exc, stopping=stopping):
                raise

    def _navigation_guard(self, page: Any, requested_url: str, *, phase: str) -> Any:
        """Validate every navigation/asset hop before the browser receives it.

        Route callbacks do not reliably run again for a redirect. A main-frame
        redirect is therefore aborted, validated, and followed by a fresh goto;
        assets follow an explicit bounded fetch loop with automatic redirects
        disabled. The final page URL is checked again before using its HTML.
        """
        from urllib.parse import urljoin, urlsplit, urlunsplit

        adapter = self
        expected = self.source_adapter.candidate_from_url(requested_url) if phase == "detail" else None

        def canonical_listing(url):
            parts = urlsplit(url)
            return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), parts.query, ""))

        def validate(url, *, navigation):
            validate_destination(url, allowlist=adapter.settings.allowlist_hosts)
            if not navigation:
                return
            if phase == "discovery":
                adapter.source_adapter.validate_listing_url(url)
                # The public driver contract returns HTML for the requested
                # listing. Do not silently attach another page/tab to that URL.
                if canonical_listing(url) != canonical_listing(requested_url):
                    raise ValueError("redirect de navegação altera a listagem solicitada")
            else:
                found = adapter.source_adapter.candidate_from_url(url)
                if (found.source, found.external_id) != (expected.source, expected.external_id):
                    raise ValueError("redirect de navegação altera identidade do concurso")

        class _Guard:
            def __init__(self):
                self.redirect_to = None
                self.failure = None
                self.history = []
                self.stopping = False

            async def __aenter__(self):
                await page.context.route("**/*", self._check_route)
                return self

            async def _check_route(self, route):
                request = route.request
                is_main = request.is_navigation_request() and request.frame == page.main_frame
                response = None
                try:
                    target = request.url
                    chain = []
                    for _ in range(6):
                        validate(target, navigation=is_main)
                        if target in chain:
                            raise ValueError("redirect circular durante navegação")
                        chain.append(target)
                        response = await route.fetch(url=target, max_redirects=0, timeout=_GOTO_TIMEOUT_MS)
                        validate(response.url, navigation=is_main)
                        if 300 <= response.status < 400:
                            location = response.headers.get("location")
                            if not location:
                                raise ValueError("redirect de navegação sem Location")
                            destination = urljoin(target, location)
                            validate(destination, navigation=is_main)
                            if is_main:
                                if destination in self.history:
                                    raise ValueError("redirect circular durante navegação")
                                self.redirect_to = destination
                                await adapter._cleanup_browser_call(route.abort, stopping=lambda: self.stopping)
                                return
                            target = destination
                            await adapter._cleanup_browser_call(response.dispose, stopping=lambda: self.stopping)
                            response = None
                            continue
                        if not 200 <= response.status < 300:
                            raise ValueError(f"navegação HTTP {response.status}")
                        limit = 2 * 1024 * 1024 if is_main else adapter.settings.limits.max_download_bytes
                        length = response.headers.get("content-length")
                        if length and length.strip().isdigit() and int(length) > limit:
                            raise ValueError("resposta de navegação excede limite de bytes")
                        body = await response.body()
                        if len(body) > limit:
                            raise ValueError("resposta de navegação excede limite de bytes")
                        await route.fulfill(response=response, body=body)
                        return
                    raise ValueError("limite de redirects durante navegação excedido")
                except asyncio.CancelledError as exc:
                    if not adapter._expected_shutdown_error(exc, stopping=self.stopping):
                        raise
                except Exception as exc:
                    if adapter._expected_shutdown_error(exc, stopping=self.stopping):
                        return
                    if is_main:
                        self.failure = exc
                    adapter._note("navegação: requisição bloqueada (" + adapter._safe_error(exc) + ")")
                    await adapter._cleanup_browser_call(route.abort, stopping=lambda: self.stopping)
                finally:
                    if response is not None:
                        await adapter._cleanup_browser_call(response.dispose, stopping=lambda: self.stopping)

            async def goto(self):
                current = requested_url
                for _ in range(6):
                    validate(current, navigation=True)
                    self.history.append(current)
                    self.redirect_to = None
                    try:
                        await page.goto(current, wait_until="domcontentloaded", timeout=_GOTO_TIMEOUT_MS)
                    except Exception:
                        if self.failure is not None:
                            raise self.failure
                        if self.redirect_to is None:
                            raise
                    if self.redirect_to is not None:
                        current = self.redirect_to
                        continue
                    self.check()
                    return
                raise ValueError("limite de redirects durante navegação excedido")

            def check(self):
                if self.failure is not None:
                    raise self.failure
                validate(page.url, navigation=True)

            async def __aexit__(self, *exc):
                self.stopping = True
                await adapter._cleanup_browser_call(
                    lambda: page.context.unroute("**/*", self._check_route), stopping=True,
                )
                return False

        return _Guard()

    async def _open_ibgp_edital_section(self, page: Any, url: str) -> None:
        """Expand only the official IBGP edital accordion observed in its HTML."""
        from urllib.parse import urlsplit
        parsed = urlsplit(url)
        if parsed.hostname != "novo.ibgpconcursos.com.br" or parsed.path != "/concurso.jsp":
            return
        try:
            toggle = page.locator("a[href='#collapseTwo']").first
            if await toggle.count():
                await toggle.click(timeout=5000)
        except Exception:
            self._note("detail: seção edital IBGP não expandida; identidade/documento continuam obrigatórios")

    async def _download_flow(self, url: str, max_bytes: int) -> DownloadedBytes:
        assert self._live is not None
        page = self._live["page"]
        self._live["navigation_guard"].check()
        context = page.context
        # Guarda de rota: cada hop (inclusive redirects mediados pelo browser)
        # é pré-validado contra a allowlist ANTES de qualquer byte trafegar.
        async with self._route_guard(context):
            # Caminho 1: clique com espera registrada ANTES da ação.
            anchor = await self._find_anchor(page, url)
            if anchor is None:
                self._note("download: sem âncora correspondente; via request (caminho legítimo)")
                return await self._download_via_request(context, url, max_bytes)
            try:
                return await self._download_via_click(page, anchor, url, max_bytes)
            except (ValueError, TypeError, AttributeError):
                # HTML de bloqueio/erro já diagnosticado: refazer via request
                # só mascararia a causa (normalmente o mesmo bloqueio).
                raise
            except Exception as exc:  # noqa: BLE001
                self._note(f"download: clique falhou ({self._safe_error(exc)}); via request")
                return await self._download_via_request(context, url, max_bytes)

    def _route_guard(self, context: Any) -> Any:
        """Guarda de allowlist por hop, instalado só durante o download."""
        adapter = self

        class _Guard:
            async def __aenter__(self) -> None:
                self.stopping = False
                async def _check(route: Any) -> None:
                    try:
                        from app.tenderproof.security import validate_destination

                        validate_destination(route.request.url, allowlist=adapter.settings.allowlist_hosts)
                    except Exception:  # noqa: BLE001 - destino proibido: bloqueia antes de acessar
                        adapter._note("rota: destino fora da allowlist bloqueado antes do acesso")
                        await adapter._cleanup_browser_call(route.abort, stopping=lambda: self.stopping)
                        return
                    # route handlers only see the first URL of redirects.
                    # Fetch one hop; abort redirects so download can use the
                    # explicit HTTP chain instead of letting the browser follow.
                    response = None
                    try:
                        response = await route.fetch(max_redirects=0, timeout=_DOWNLOAD_TIMEOUT_MS)
                        if 300 <= response.status < 400:
                            adapter._note("download: redirect do clique interrompido; usar cadeia HTTP validada")
                            await adapter._cleanup_browser_call(route.abort, stopping=lambda: self.stopping)
                            return
                        body = await response.body()
                        if len(body) > adapter.settings.limits.max_download_bytes:
                            adapter._note("download: resposta do clique acima do limite")
                            await adapter._cleanup_browser_call(route.abort, stopping=lambda: self.stopping)
                            return
                        await route.fulfill(response=response, body=body)
                    except asyncio.CancelledError as exc:
                        if not adapter._expected_shutdown_error(exc, stopping=self.stopping):
                            raise
                    except Exception as exc:
                        if adapter._expected_shutdown_error(exc, stopping=self.stopping):
                            return
                        adapter._note("download: falha na requisição interceptada")
                        await adapter._cleanup_browser_call(route.abort, stopping=lambda: self.stopping)
                    finally:
                        if response is not None:
                            await adapter._cleanup_browser_call(response.dispose, stopping=lambda: self.stopping)

                self._handler = _check
                await context.route("**/*", _check)

            async def __aexit__(self, *exc: Any) -> bool:
                self.stopping = True
                await adapter._cleanup_browser_call(
                    lambda: context.unroute("**/*", self._handler), stopping=True,
                )
                return False

        return _Guard()

    async def _close_live_flow(self) -> None:
        self._shutdown_in_progress = True
        assert self._live is not None
        live, self._live = self._live, None
        record = SessionRecord(phase="detail", session_id=live.get("session_id"), closed=False)
        self._records.append(record)
        try:
            record.close_requested = True
            await live["browser"].close()  # inclui release_and_wait
            record.closed = await confirm_browser_released(live["solari"], live["session_id"])
        except BaseException as exc:  # noqa: BLE001 - inclui cancelamento
            self._note(f"detail: browser.close falhou ({self._safe_error(exc)}); encerramento não confirmado")
        finally:
            try:
                self._observe_closed(record)
            finally:
                navigation = live.get("navigation_guard")
                try:
                    if navigation is not None:
                        await navigation.__aexit__(None, None, None)
                finally:
                    try:
                        await live["solari"].__aexit__(None, None, None)
                    except BaseException:  # noqa: BLE001
                        pass

    async def _poll_replay_flow(self, phase: str, budget_s: float, interval_s: float) -> None:
        """Consulta o replay de uma etapa já encerrada, com cliente novo."""
        record = next(
            (r for r in reversed(self._records) if r.phase == phase and not r.replay_url), None
        )
        if record is None or not record.session_id:
            return
        await self._fill_replay(record, deadline_s=budget_s, interval_s=interval_s)

    def _abort_live(self) -> None:
        live, self._live = self._live, None
        if live is not None:
            self._records.append(
                SessionRecord(
                    phase="detail", session_id=live.get("session_id"),
                    replay_status="failed", replay_note="fase abortada por timeout",
                    closed=False,
                )
            )

    def _mark_live_closed(self) -> None:
        if self._live is not None:
            session_id = self._live.get("session_id")
            self._live = None
            self._records.append(
                SessionRecord(phase="detail", session_id=session_id, replay_status="pending",
                              replay_note="encerramento não confirmado", closed=False)
            )

    # -- espera real ----------------------------------------------------
    async def _await_listing_ready(self, page: Any) -> None:
        try:
            await page.locator(", ".join(self.source_adapter.ready_selectors)).first.wait_for(timeout=_WAIT_ANCHOR_TIMEOUT_MS)
            return
        except Exception:  # noqa: BLE001
            pass
        try:
            await page.wait_for_response(lambda r: self._matches_source_response(r.url), timeout=10_000)
        except Exception:  # noqa: BLE001
            self._note("discovery: sem âncora de concurso nem resposta REST observada")

    # -- captura de rede -------------------------------------------------
    def _matches_source_response(self, url: str) -> bool:
        from urllib.parse import urlsplit
        parts = urlsplit(url)
        return parts.hostname in self.source_adapter.allowed_hosts and any(parts.path.startswith(path) for path in self.source_adapter.observed_url_paths)

    def _attach_capture(self, page: Any) -> None:
        seen: list[Any] = []
        page.on("response", lambda response: seen.append(response) if len(seen) < 500 else None)
        if self._live is not None:
            self._live["seen_responses"] = seen
        else:
            self._pending_seen = seen

    async def _drain_capture(self) -> None:
        seen: list[Any] = getattr(self, "_pending_seen", None) or (
            self._live.get("seen_responses", []) if self._live else []
        )
        if hasattr(self, "_pending_seen"):
            delattr(self, "_pending_seen")
        limits = self.settings.limits
        kept = 0
        for response in seen:
            try:
                url = response.url
            except Exception:  # noqa: BLE001
                continue
            if not self._matches_source_response(url):
                continue
            if kept >= limits.max_observed_json:
                self._note(f"rede: teto de {limits.max_observed_json} JSONs atingido")
                break
            try:
                status = response.status
                payload = await response.json()
            except Exception as exc:  # noqa: BLE001
                self._note(f"rede: resposta ilegível ({self._safe_error(exc)})")
                continue
            try:
                text = json.dumps(payload, ensure_ascii=False, default=str)
            except Exception:  # noqa: BLE001
                self._note("rede: payload não serializável")
                continue
            if len(text) > limits.max_json_bytes:
                payload = {"_truncated": True, "_preview": text[: limits.max_json_bytes]}
            self._observed.append(ObservedJson(url=url, status=status, payload=payload))
            kept += 1

    # -- download ----------------------------------------------------------
    async def _find_anchor(self, page: Any, url: str) -> Any | None:
        handle = await page.evaluate_handle(
            """(target) => {
              const abs = (h) => { try { return new URL(h, document.baseURI).href; } catch (e) { return null; } };
              return ([...document.querySelectorAll('a[href]')].find((a) => abs(a.getAttribute('href')) === target) || null);
            }""",
            url,
        )
        element = handle.as_element() if handle else None  # síncrono no Python
        if element is None:
            try:
                await handle.dispose()
            except Exception:  # noqa: BLE001
                pass
            return None
        return element

    async def _download_via_click(self, page: Any, anchor: Any, url: str, max_bytes: int) -> DownloadedBytes:
        async with page.expect_download(timeout=_DOWNLOAD_TIMEOUT_MS) as download_info:
            await anchor.click()
        download = await download_info.value
        try:
            from pathlib import Path
            from tempfile import TemporaryDirectory

            failure = await download.failure()
            if failure:
                raise RuntimeError("download interrompido pelo navegador")
            # path() não existe em conexões remotas; save_as transfere o stream.
            with TemporaryDirectory(prefix="tenderproof-") as directory:
                local_path = Path(directory) / "edital.pdf"
                await download.save_as(local_path)
                if local_path.stat().st_size > max_bytes:
                    raise ValueError(f"conteúdo acima do limite de {max_bytes} bytes")
                raw = local_path.read_bytes()
        finally:
            try:
                await download.delete()
            except Exception:  # noqa: BLE001 - limpeza best-effort
                pass
        final_url = download.url or url
        validate_redirect_chain(
            [url, final_url] if final_url != url else [url],
            allowlist=self.settings.allowlist_hosts,
        )
        self._ensure_pdf_bytes(raw, max_bytes, mechanism="click")
        self._note("download: via clique (expect_download)")
        return DownloadedBytes(
            url_requested=url,
            url_final=final_url,
            content=raw,
            content_type=None,
            redirect_chain=[url, final_url] if final_url != url else [url],
            mechanism="click",
        )

    async def _download_via_request(self, context: Any, url: str, max_bytes: int) -> DownloadedBytes:
        from urllib.parse import urljoin

        chain = [url]
        for hop in range(6):
            validate_redirect_chain(chain, allowlist=self.settings.allowlist_hosts)
            # Browser routes do not intercept APIRequestContext. Follow manually.
            response = await context.request.get(
                chain[-1], timeout=_DOWNLOAD_TIMEOUT_MS, max_redirects=0
            )
            try:
                status = response.status
                headers = {k.lower(): v for k, v in (response.headers or {}).items()}
                if status in (301, 302, 303, 307, 308):
                    location = headers.get("location")
                    if not location:
                        raise ValueError("redirect sem Location")
                    destination = urljoin(chain[-1], location)
                    validate_redirect_chain(
                        [destination], allowlist=self.settings.allowlist_hosts
                    )
                    if destination in chain or hop == 5:
                        raise ValueError("limite ou ciclo de redirects")
                    chain.append(destination)
                    continue
                if not 200 <= status < 300:
                    raise RuntimeError(f"download HTTP {status}")
                length = headers.get("content-length")
                if length and length.strip().isdigit() and int(length) > max_bytes:
                    raise ValueError(f"conteúdo acima do limite de {max_bytes} bytes (Content-Length)")
                content_type = headers.get("content-type")
                if content_type and "html" in content_type.lower():
                    raise HtmlBlockError("página HTML recebida no lugar de PDF (content-type)")
                raw = await response.body()
                self._ensure_pdf_bytes(raw, max_bytes, mechanism="request")
                self._note("download: via request no mesmo contexto")
                return DownloadedBytes(
                    url_requested=url, url_final=chain[-1], content=raw,
                    content_type=content_type, redirect_chain=chain, mechanism="request",
                )
            finally:
                await self._cleanup_browser_call(response.dispose)
        raise ValueError("limite de redirects")

    def _ensure_pdf_bytes(self, raw: bytes, max_bytes: int, *, mechanism: str) -> None:
        # Limitação documentada: o SDK materializa o arquivo antes desta
        # verificação (sem create_read_stream no Python 1.62); Content-Length
        # é pré-checado quando disponível e o temporário é removido.
        _ = mechanism
        if len(raw) > max_bytes:
            raise ValueError(f"conteúdo acima do limite de {max_bytes} bytes")
        if not raw:
            raise ValueError("download vazio")
        text_head = raw[:2048].lstrip()[:64].lower()
        if has_pdf_header(raw):
            return
        if text_head.startswith((b"<!doctype html", b"<html", b"<head", b"<body")):
            raise HtmlBlockError("página HTML recebida no lugar de PDF")
        raise ValueError("conteúdo não parece ser PDF (bytes iniciais inválidos)")

    # -- replay -------------------------------------------------------------
    async def _fill_replay(
        self,
        record: SessionRecord,
        *,
        deadline_s: float | None = None,
        interval_s: float | None = None,
    ) -> None:
        if not self.config.recording:
            record.replay_status = "disabled"
            record.replay_note = "recording desativado na configuração"
            return
        if not record.session_id:
            record.replay_status = "failed"
            record.replay_note = "sessão sem ID; replay impossível"
            return
        deadline = deadline_s if deadline_s is not None else self.settings.limits.replay_deadline_s
        interval = interval_s if interval_s is not None else self.settings.limits.replay_poll_interval_s
        status, url, note = await poll_replay_url(
            self.config, record.session_id or "", budget_s=deadline, interval_s=interval
        )
        record.replay_status = status  # type: ignore[assignment]
        record.replay_url = url
        record.replay_note = note
        if status == "available" and (self.session_id == record.session_id or not self.session_id):
            self.session_id = record.session_id
        elif status == "failed":
            self._note(f"replay: falha definitiva ({note})")
        return

    def _note(self, message: str) -> None:
        self._diagnostics.append(message)

    @staticmethod
    def _safe_error(exc: BaseException, *, limit: int = 160) -> str:
        """Classe + mensagem higienizada (redige endpoints/credenciais)."""
        text = str(exc)
        for pattern in ("ws://", "wss://", "cdp", "token=", "key=", "api_key", "slr_live_", "sb_live_"):
            if pattern in text.lower():
                return f"{exc.__class__.__name__}: [detalhe suprimido por segurança]"
        return f"{exc.__class__.__name__}: {text[:limit]}"


def collect_session_info(driver: SolariDriver) -> tuple[list[SessionRecord], list[str]]:
    """Coleta registros de sessão/diagnóstico de qualquer driver do protocolo."""
    records: list[SessionRecord] = []
    notes: list[str] = []
    session_records = getattr(driver, "session_records", None)
    if callable(session_records):
        try:
            records = list(session_records() or [])
        except Exception:  # noqa: BLE001
            pass
    diagnostics = getattr(driver, "diagnostics", None)
    if callable(diagnostics):
        try:
            notes = [str(item) for item in (diagnostics() or [])]
        except Exception:  # noqa: BLE001
            pass
    return records, notes
