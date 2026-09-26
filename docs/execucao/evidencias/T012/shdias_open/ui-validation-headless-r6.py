from __future__ import annotations

import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
ACCESS = ROOT / "backend/.tenderproof/local-pilot/ACESSO-LOCAL.md"

def credential(label: str) -> str:
    text = ACCESS.read_text(encoding="utf-8")
    match = re.search(rf"^{re.escape(label)}:\s*([^\r\n]+)", text, re.M)
    if not match:
        raise RuntimeError(f"credencial local ausente: {label}")
    return match.group(1).strip(" `")

def body(page) -> str:
    return page.locator("body").inner_text(timeout=20000)

def main() -> None:
    result = {"mode": "headless_playwright_real_ui", "mutations": False, "errors": [], "screenshots": []}
    print("headless:start", flush=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(10000)
        page.on("pageerror", lambda error: result["errors"].append(str(error)))
        checkpoint_responses = []
        def capture_checkpoint(response):
            if response.url.endswith("/api/sync/checkpoint"):
                item = {"status": response.status}
                try:
                    payload = response.json()
                    item.update({"concursos": len(payload.get("concursos", [])), "fontes": len(payload.get("fontes", [])), "selections": len(payload.get("selections", [])) if isinstance(payload.get("selections"), list) else None})
                except Exception:
                    item["json"] = False
                checkpoint_responses.append(item)
        page.on("response", capture_checkpoint)
        checkpoint = {}
        try:
            page.goto("http://localhost:13000/login", wait_until="domcontentloaded", timeout=60000)
            print("headless:login-loaded", flush=True)
            page.wait_for_timeout(2000)
            email = page.get_by_placeholder("E-mail", exact=True)
            if email.count():
                email.fill(credential("E-mail"))
                page.get_by_placeholder("Senha", exact=True).fill(credential("Senha"))
                page.get_by_text("Entrar", exact=True).click()
                page.wait_for_timeout(5000)
                checkpoint = {"observed_after_login": True}
                print("headless:login-clicked", flush=True)
            page.wait_for_url("**/inicio", timeout=60000)
            print("headless:inicio", flush=True)
            page.wait_for_timeout(1000)
            inicio = body(page)
            result["inicio"] = {"url": page.url, "contains_shdias": "SHDias" in inicio, "contains_hortolandia": "Hortolândia" in inicio or "Hortolandia" in inicio, "contains_title": "001/2026" in inicio, "text_excerpt": inicio[:5000]}
            result["assets"] = page.locator("script[src]").evaluate_all("els => els.map(e => e.src)")
            inicio_png = OUT / "ui-validation-r8-inicio.png"
            page.screenshot(path=str(inicio_png), full_page=True)
            result["screenshots"].append(str(inicio_png))
            page.goto("http://localhost:13000/concurso/34", wait_until="domcontentloaded", timeout=60000)
            print("headless:detail", flush=True)
            page.wait_for_timeout(800)
            detail = body(page)
            page.reload(wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(500)
            detail_reload = body(page)
            result["detail"] = {"url": page.url, "contains_source": "SHDias" in detail, "contains_orgao": "Hortolândia" in detail or "Hortolandia" in detail, "contains_edital": "001/2026" in detail, "contains_prova": "27/09/2026" in detail or "2026-09-27" in detail, "contains_taxa": "63,25" in detail or "63.25" in detail, "contains_visible_fee": bool(re.search(r"Taxa de inscrição:\s*(?:R\$\s*)?63[,.]25", detail)), "contains_cargo_301": "301" in detail, "contains_cargo_302": "302" in detail, "contains_12": "12" in detail, "contains_28": "28" in detail, "contains_salary": "3.971,37" in detail or "3971.37" in detail, "no_undefined": "undefined" not in detail, "reload_no_undefined": "undefined" not in detail_reload, "reload_contains_visible_fee": bool(re.search(r"Taxa de inscrição:\s*(?:R\$\s*)?63[,.]25", detail_reload)), "reload_contains_codes_and_vacancies": all(token in detail_reload for token in ("301", "302", "12", "28")), "reload_stable": detail_reload == detail, "duplicate_title_count": detail.count("001/2026"), "text_excerpt": detail[:7000]}
            detail_png = OUT / "ui-validation-r8-detail34.png"
            page.screenshot(path=str(detail_png), full_page=True)
            result["screenshots"].append(str(detail_png))
            page.goto("http://localhost:13000/salvos", wait_until="domcontentloaded", timeout=60000)
            print("headless:salvos", flush=True)
            page.wait_for_timeout(500)
            result["salvos"] = {"url": page.url, "text_excerpt": body(page)[:2500], "mutating_controls_clicked": False}
            page.goto("http://localhost:13000/notificacoes", wait_until="domcontentloaded", timeout=60000)
            print("headless:notificacoes", flush=True)
            page.wait_for_timeout(500)
            result["notificacoes"] = {"url": page.url, "text_excerpt": body(page)[:2500], "mutating_controls_clicked": False}
            result["checkpoint"] = {"login_observed": checkpoint, "responses": checkpoint_responses}
            result["result"] = "SHDIAS_UI_VALIDATED_HEADLESS" if all(result["detail"].get(key) for key in ("contains_source", "contains_orgao", "contains_edital", "contains_prova", "contains_visible_fee", "contains_cargo_301", "contains_cargo_302", "contains_12", "contains_28", "contains_salary", "no_undefined", "reload_no_undefined", "reload_contains_visible_fee", "reload_contains_codes_and_vacancies")) else "PARTIAL_UI"
        finally:
            browser.close()
    (OUT / "ui-validation-r8-20260913.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"result": result.get("result"), "checkpoint": result.get("checkpoint"), "detail": result.get("detail", {}), "errors": result.get("errors", []), "screenshots": result.get("screenshots", [])}, ensure_ascii=False))

if __name__ == "__main__":
    main()
