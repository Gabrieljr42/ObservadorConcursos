from __future__ import annotations

import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
ACCESS = ROOT / "backend/.tenderproof/local-pilot/ACESSO-LOCAL.md"
BASE = "http://localhost:13000"


def credential(label: str) -> str:
    text = ACCESS.read_text(encoding="utf-8")
    match = re.search(rf"^{re.escape(label)}:\s*([^\r\n]+)", text, re.M)
    if not match:
        raise RuntimeError(f"credencial local ausente: {label}")
    return match.group(1).strip(" `")


def text(page) -> str:
    return page.locator("body").inner_text(timeout=20000)


def login(page, result: dict) -> None:
    page.goto(BASE + "/login", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(1200)
    email = page.get_by_placeholder("E-mail", exact=True)
    if email.count():
        email.fill(credential("E-mail"))
        page.get_by_placeholder("Senha", exact=True).fill(credential("Senha"))
        page.get_by_text("Entrar", exact=True).click()
        page.wait_for_timeout(3500)
    page.wait_for_url("**/inicio", timeout=60000)
    result.setdefault("login", []).append({"url": page.url, "mutations": False})


def goto_snapshot(page, route: str, result: dict, shot: str | None = None) -> str:
    page.goto(BASE + route, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(900)
    value = text(page)
    item = {"url": page.url, "text_excerpt": value[:5000], "no_undefined": "undefined" not in value,
            "no_nan": "NaN" not in value, "no_raw_html": not bool(re.search(r"<\/?(?:html|body|div|script)\b", value, re.I))}
    if shot:
        path = OUT / shot
        page.screenshot(path=str(path), full_page=True)
        item["screenshot"] = str(path)
    result[route.strip("/").replace("/", "_") or "root"] = item
    return value


def main() -> None:
    result = {"schema": "t012.cpcon.ui-validation-r13.v1", "mode": "headless_playwright_real_ui",
              "mutations": False, "errors": [], "screenshots": [], "expected_source": 35,
              "expected_external_id": "processo-seletivo-simplificado-no-002-2026"}
    checkpoint = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(12000)
        page.on("pageerror", lambda error: result["errors"].append(str(error)))

        def response_probe(response):
            if response.url.endswith("/api/sync/checkpoint"):
                item = {"status": response.status}
                try:
                    payload = response.json()
                    item["keys"] = sorted(payload.keys()) if isinstance(payload, dict) else []
                    for key in ("concursos", "fontes", "selections"):
                        if isinstance(payload, dict) and isinstance(payload.get(key), list):
                            item[key] = len(payload[key])
                except Exception:
                    item["json"] = False
                checkpoint.append(item)
        page.on("response", response_probe)
        try:
            login(page, result)
            inicio = goto_snapshot(page, "/inicio", result, "ui-validation-r13-inicio.png")
            result["inicio"]["contains_cpcon"] = "PROCESSO SELETIVO SIMPLIFICADO" in inicio
            result["inicio"]["contains_uepb"] = "Universidade Estadual da Paraíba" in inicio
            # Exercise the normal listing/search routes without submitting any mutating action.
            list_text = goto_snapshot(page, "/listagem", result, "ui-validation-r13-listagem.png")
            busca_text = goto_snapshot(page, "/busca", result, "ui-validation-r13-busca.png")
            result["listagem"]["contains_cpcon"] = "PROCESSO SELETIVO SIMPLIFICADO" in list_text
            result["busca"]["contains_cpcon"] = "PROCESSO SELETIVO SIMPLIFICADO" in busca_text

            detail = goto_snapshot(page, "/concurso/35", result, "ui-validation-r13-detail35.png")
            result["detail"] = result["concurso_35"]
            before = detail
            page.reload(wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(700)
            after = text(page)
            result["detail"]["reload"] = {"no_undefined": "undefined" not in after, "no_nan": "NaN" not in after,
                                             "stable": before == after, "text_excerpt": after[:9000]}
            result["detail"]["identity"] = {
                "title": "PROCESSO SELETIVO SIMPLIFICADO Nº 002/2026" in detail,
                "orgao": "Universidade Estadual da Paraíba" in detail,
                "edital": "002/2026" in detail,
                "source_or_external": ("CPCON" in detail or "cpcon" in detail.lower() or "processo-seletivo-simplificado-no-002-2026" in detail),
            }
            cargos = [
                ("Técnico em Laboratório (Esterilização)", 1),
                ("Técnico em Laboratório (Microbiologia de Alimentos)", 1),
                ("Técnico em Laboratório (Eletrotécnica)", 2),
                ("Técnico em Laboratório (Química)", 1),
                ("Técnico em Laboratório (Química e Fertilidade do Solo)", 1),
                ("Técnico em Laboratório (Histopatologia Oral)", 1),
            ]
            cargo_checks = []
            for name, vacancies in cargos:
                cargo_checks.append({"nome": name, "nome_visivel": name in detail,
                                     "vagas_visiveis": bool(re.search(rf"{re.escape(name)}[\s\S]{{0,900}}?{vacancies}\s+vaga", detail, re.I)),
                                     "remuneracao_visivel": bool(re.search(rf"{re.escape(name)}[\s\S]{{0,1200}}?(?:R\$\s*)?3[.,]768[.,]36", detail, re.I))})
            result["detail"]["cargos"] = cargo_checks
            result["detail"]["cargo_count_text"] = len(re.findall(r"Técnico em Laboratório", detail, re.I))
            result["detail"]["remuneracao_expected"] = "3.768,36" in detail or "3768.36" in detail
            result["detail"]["dates"] = {"has_unsubstantiated_prova": bool(re.search(r"27/09/2026|2026-09-27", detail)),
                                            "has_absence_marker": bool(re.search(r"não informado|não confirmad|pendente", detail, re.I))}
            result["detail"]["no_undefined"] = "undefined" not in detail and "undefined" not in after
            result["detail"]["no_nan"] = "NaN" not in detail and "NaN" not in after

            salvos = goto_snapshot(page, "/salvos", result, "ui-validation-r13-salvos.png")
            result["salvos"]["zero"] = bool(re.search(r"0\s*(?:itens?|concursos?)\s*salvos|nenhum.*salvo|ainda não há", salvos, re.I))
            notificacoes = goto_snapshot(page, "/notificacoes", result, "ui-validation-r13-notificacoes.png")
            result["notificacoes"]["cpcon_visible"] = "PROCESSO SELETIVO SIMPLIFICADO" in notificacoes or "002/2026" in notificacoes
            result["notificacoes"]["original_alert_visible"] = bool(re.search(r"alerta|notifica", notificacoes, re.I))
            result["checkpoint"] = checkpoint
            result["new_session"] = {}

            # New browser context proves persisted UI without reusing the first session.
            context2 = browser.new_context()
            page2 = context2.new_page()
            page2.set_default_timeout(12000)
            login(page2, result)
            page2.goto(BASE + "/concurso/35", wait_until="domcontentloaded", timeout=60000)
            page2.wait_for_timeout(700)
            second = text(page2)
            result["new_session"] = {"url": page2.url, "title": "PROCESSO SELETIVO SIMPLIFICADO Nº 002/2026" in second,
                                     "six_cargos": all(name in second for name, _ in cargos),
                                     "no_undefined": "undefined" not in second, "no_nan": "NaN" not in second}
            context2.close()
            all_cargos = all(x["nome_visivel"] and x["vagas_visiveis"] and x["remuneracao_visivel"] for x in cargo_checks)
            result["result"] = "PASS_UI_SYNC" if (result["inicio"]["contains_cpcon"] and result["detail"]["identity"]["title"] and result["detail"]["identity"]["orgao"] and result["detail"]["identity"]["edital"] and len(cargo_checks) == 6 and all_cargos and result["detail"]["reload"]["no_undefined"] and result["detail"]["no_nan"] and result["new_session"]["six_cargos"] and result["new_session"]["no_undefined"] and result["salvos"]["zero"]) else "UI_SYNC_DEFECT"
        finally:
            browser.close()
    out_json = OUT / "ui-validation-r13-20260913.json"
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"result": result.get("result"), "errors": result.get("errors"), "checkpoint": result.get("checkpoint"), "cargo_checks": result.get("detail", {}).get("cargos"), "screenshots": [v.get("screenshot") for v in result.values() if isinstance(v, dict) and v.get("screenshot")]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
