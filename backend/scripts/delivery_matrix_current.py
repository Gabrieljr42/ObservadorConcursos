"""Build the current, source-by-source delivery matrix.

This is a read-only composition step.  It combines the historical source
status with a fresh delivery snapshot and the application/document-review
receipts.  It deliberately never changes ``tenderproof-product-status.json``
and never treats a successful detail run or an enabled adapter as full source
integration.

The script can run on the host (using the preserved delivery snapshot) or in
the pilot container (using ``/var/lib/observador/.../delivery-current-*.json``).
Pass ``--snapshot`` when the fresh runtime receipt is not visible from the
current filesystem.
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
COMPLETION = ROOT / "backend" / ".tenderproof" / "product-completion"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value


def first_existing(paths: Iterable[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def latest_glob(patterns: Iterable[str]) -> Path | None:
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(Path(path) for path in glob.glob(pattern))
    return max(matches, key=lambda path: path.stat().st_mtime) if matches else None


def choose_snapshot(explicit: str | None) -> tuple[Path, bool]:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise FileNotFoundError(f"snapshot not found: {path}")
        return path, path.name.startswith("delivery-current-")

    fresh = latest_glob(
        [
            str(COMPLETION / "delivery-current-*.json"),
            "/var/lib/observador/tenderproof/product-completion/delivery-current-*.json",
        ]
    )
    if fresh:
        return fresh, True

    # The host checkout may not expose the pilot volume.  This fallback keeps
    # the output useful while making the evidence unambiguous; a container run
    # with the fresh receipt will replace it without touching the history.
    historical = COMPLETION / "delivery-snapshot-20260909-final.json"
    if historical.exists():
        return historical, False
    raise FileNotFoundError("no delivery-current snapshot and no preserved final snapshot")


def choose_api_current(explicit: str | None) -> Path | None:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise FileNotFoundError(f"API current receipt not found: {path}")
        return path
    return latest_glob(
        [
            str(COMPLETION / "delivery-api-current-*.json"),
            "/var/lib/observador/tenderproof/product-completion/delivery-api-current-*.json",
        ]
    )


def choose_optional_receipt(explicit: str | None, patterns: Iterable[str]) -> Path | None:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise FileNotFoundError(f"receipt not found: {path}")
        return path
    return latest_glob(patterns)


def value(obj: Any, *keys: str, default: Any = None) -> Any:
    for key in keys:
        if isinstance(obj, dict) and key in obj:
            return obj[key]
    return default


def text(value_: Any) -> str:
    if value_ is None:
        return ""
    if isinstance(value_, (dict, list)):
        return json.dumps(value_, ensure_ascii=False, separators=(",", ":"))
    return str(value_)


def unique(items: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        clean = str(item).strip()
        if clean and clean not in seen:
            result.append(clean)
            seen.add(clean)
    return result


def flatten_evidence(value_: Any) -> list[str]:
    """Extract paths/URLs from status evidence without dumping findings."""
    found: list[str] = []
    if isinstance(value_, str):
        if value_.startswith(("backend/", "docs/", "runtime:", "/var/", "http://", "https://")):
            found.append(value_)
    elif isinstance(value_, list):
        for item in value_:
            found.extend(flatten_evidence(item))
    elif isinstance(value_, dict):
        for key, item in value_.items():
            if key.lower() in {"evidence", "reference", "path", "url", "artifact"}:
                found.extend(flatten_evidence(item))
            elif key.lower() not in {"finding", "next_action", "scope"}:
                # Requirement objects often keep evidence one level deeper.
                found.extend(flatten_evidence(item))
    return unique(found)


def read_inventory(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))
    if len(rows) != 99:
        raise ValueError(f"expected 99 inventory rows, got {len(rows)}: {path}")
    return [{str(k): text(v) for k, v in row.items()} for row in rows]


def requirement_gaps(status: dict[str, Any]) -> list[str]:
    requirements = status.get("requirements") or {}
    labels = {
        "official_addresses_and_content_scope": "endereços oficiais/escopo",
        "details_and_all_document_types": "detalhes e tipos documentais",
        "complete_fields_with_provenance": "campos aplicáveis e proveniência",
        "amendments_and_history": "retificações e histórico",
        "catalogue_publication_and_sync": "publicação e sincronização",
        "recurring_operation_and_recovery": "operação recorrente e recuperação",
    }
    gaps: list[str] = []
    for key, label in labels.items():
        state = text(value(requirements.get(key), "state", default="unverified"))
        if state not in {"complete", "verified"}:
            gaps.append(f"{label}={state}")
    return gaps


# These are the eight source-specific conditions documented in
# docs/ENTREGA-BLOQUEIOS-FONTES.md.  Keeping the proof here prevents a generic
# "no adapter" or "no run" from being mislabeled as an external outage.
EXTERNAL_BLOCKS: dict[str, dict[str, str]] = {
    "aocp_open": {
        "proof": "HTTP 403 challenge at official root/listing and alternate public address",
        "evidence": "backend/.tenderproof/product-completion/missing-sources/20260908T204606Z/report.json | backend/.tenderproof/product-completion/remaining-bancas/public-addresses-20260909T184942Z/report.json | backend/.tenderproof/product-completion/remaining-bancas-solari-20260909/report.json",
        "resume": "Retomar quando houver acesso público legítimo sem desafio ou feed oficial acessível; confirmar escopo e só então implementar aquisição.",
    },
    "seprod_open": {
        "proof": "TLS validation fails with expired certificate on configured and institutional hosts; HTTP redirects to HTTPS failure",
        "evidence": "backend/.tenderproof/product-completion/seprod/initial-verification.json | backend/.tenderproof/product-completion/seprod/instituto-verification.json",
        "resume": "Retomar após correção legítima do certificado ou endereço oficial atual com TLS válido; não desativar TLS.",
    },
    "unifil_open": {
        "proof": "HTTP 403 browser challenge on listing and detail routes in ordinary acquisition",
        "evidence": "backend/.tenderproof/product-completion/unifil-solari/report.json | backend/.tenderproof/product-completion/unifil-solari/public-routes-verification.json | backend/.tenderproof/product-completion/remaining-bancas/public-addresses-20260909T184942Z/report.json",
        "resume": "Retomar após acesso público legítimo ou feed oficial acessível que permita provar descoberta atual; não contornar o desafio.",
    },
    "leandroferreira_open": {
        "proof": "Configured domain does not resolve DNS; institutional identity and compatible scope are unconfirmed",
        "evidence": "backend/.tenderproof/product-completion/missing-sources/20260908T204606Z/report.json | backend/.tenderproof/product-completion/remaining-bancas/20260909T164344Z/report.json | backend/.tenderproof/product-completion/new-sources/20260909T004654Z/verification.json",
        "resume": "Retomar após confirmação institucional do endereço oficial atual; não substituir por município homônimo.",
    },
    "iuds_open": {
        "proof": "TLS certificate expired on configured host and portal.iuds.org.br; HTTP redirects to invalid HTTPS",
        "evidence": "backend/.tenderproof/product-completion/new-sources/20260909T004654Z/verification.json | backend/.tenderproof/product-completion/remaining-bancas/20260909T164344Z/alternate-public-addresses.json",
        "resume": "Retomar após endereço oficial com certificado válido ou correção do servidor; provar descoberta atual sem desativar TLS.",
    },
    "idgran_open": {
        "proof": "Configured domain fails DNS resolution; official identity and alternate address remain unconfirmed",
        "evidence": "backend/.tenderproof/product-completion/missing-sources/20260908T204606Z/report.json | backend/.tenderproof/product-completion/remaining-bancas/20260909T164344Z/report.json | backend/.tenderproof/product-completion/new-sources/20260909T004654Z/verification.json",
        "resume": "Retomar após evidência institucional de domínio atual e compatível; não substituir por banca de nome semelhante.",
    },
    "oppus_open": {
        "proof": "HTTP 403 challenge; later HTTP 200 contained incompatible Italian gambling articles without selection links",
        "evidence": "backend/.tenderproof/product-completion/new-sources/20260909T004654Z/verification.json | backend/.tenderproof/product-completion/remaining-bancas/20260909T164344Z/report.json | backend/.tenderproof/product-completion/remaining-bancas-solari-20260909/report.json",
        "resume": "Retomar após confirmação da identidade institucional e listagem de concursos compatível; não publicar artigos nem associar automaticamente o domínio histórico.",
    },
    "fapemat_selection": {
        "proof": "Official aliases redirect or fail with connection reset before current editais content is acquired",
        "evidence": "backend/.tenderproof/product-completion/fapemat/discovery-20260909T151214Z/verification.json | backend/.tenderproof/product-completion/fapemat/public-aliases-20260909T192447Z/report.json | backend/.tenderproof/product-completion/fapemat/solari-recheck-20260909/report.json",
        "resume": "Retomar quando o serviço responder normalmente; validar rota de editais e escopo de seleções antes de implementar e repetir a coleta.",
    },
}

# A pending document is not automatically a human dependency.  Pedrinhas has
# an authorized internal amendment path, while Ibiúna has a real identity
# conflict in the three new PDFs and needs an authority decision on the
# document-to-contest link.
HUMAN_DEPENDENCIES: dict[str, dict[str, str]] = {
    "abcp_open": {
        "proof": "backend/.tenderproof/product-completion/ibiuna-review-20260909/decision-draft.json",
        "resume": "Obter decisão da autoridade sobre o vínculo dos três PDFs (cabeçalho PROCESSO SELETIVO 001/2026 versus edital-base 002/2026); registrar a decisão, então aplicar somente efeitos documentalmente comprovados e sincronizar.",
    },
}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", default=str(ROOT / "docs" / "entrega-fontes-2026-09-09.csv"))
    parser.add_argument("--status", default=str(ROOT / "docs" / "tenderproof-product-status.json"))
    parser.add_argument("--snapshot", help="fresh delivery-current JSON; auto-detected when omitted")
    parser.add_argument("--api-current", help="latest delivery-api-current JSON; auto-detected when omitted")
    parser.add_argument("--failed-sources", help="latest bounded failed-source receipt; auto-detected when omitted")
    parser.add_argument("--failed-tenderproof", help="latest failed TenderProof receipt; auto-detected when omitted")
    parser.add_argument("--pedrinhas-applied", help="Pedrinhas applied receipt; auto-detected when omitted")
    parser.add_argument("--app", default=str(COMPLETION / "delivery-app-20260909.json"))
    parser.add_argument("--pending", default=str(COMPLETION / "delivery-pending-api-20260909.json"))
    parser.add_argument("--result", action="append", default=[], help="additional result JSON; may be repeated")
    parser.add_argument("--output", default=str(ROOT / "docs" / "entrega-fontes-atual.csv"))
    args = parser.parse_args()

    inventory_path = Path(args.inventory)
    status_path = Path(args.status)
    snapshot_path, is_fresh = choose_snapshot(args.snapshot)
    api_current_path = choose_api_current(args.api_current)
    failed_sources_path = choose_optional_receipt(
        args.failed_sources,
        [
            str(COMPLETION / "delivery-failed-sources-*/report.json"),
            "/var/lib/observador/tenderproof/product-completion/delivery-failed-sources-*/report.json",
        ],
    )
    failed_tenderproof_path = choose_optional_receipt(
        args.failed_tenderproof,
        [
            str(COMPLETION / "delivery-failed-tenderproof-*/tenderproof-real-runs.json"),
            "/var/lib/observador/tenderproof/product-completion/delivery-failed-tenderproof-*/tenderproof-real-runs.json",
        ],
    )
    pedrinhas_applied_path = choose_optional_receipt(
        args.pedrinhas_applied,
        [
            str(COMPLETION / "delivery-pedrinhas-applied-*.json"),
            "/var/lib/observador/tenderproof/product-completion/delivery-pedrinhas-applied-*.json",
        ],
    )
    inventory = read_inventory(inventory_path)
    historical = load_json(status_path)
    snapshot = load_json(snapshot_path)
    api_current = load_json(api_current_path) if api_current_path else {}
    failed_sources = load_json(failed_sources_path) if failed_sources_path else {}
    failed_tenderproof = load_json(failed_tenderproof_path) if failed_tenderproof_path else {}
    app = load_json(Path(args.app)) if Path(args.app).exists() else {}
    pending_api = load_json(Path(args.pending)) if Path(args.pending).exists() else {}

    if not isinstance(historical, dict) or not isinstance(snapshot, dict):
        raise ValueError("status and snapshot inputs must be JSON objects")
    if not isinstance(api_current, dict):
        api_current = {}
    if not isinstance(failed_sources, dict):
        failed_sources = {}
    if not isinstance(failed_tenderproof, dict):
        failed_tenderproof = {}
    if not isinstance(app, dict):
        app = {}

    historical_by_source = {
        text(item.get("source")): item for item in historical.get("sources", []) if item.get("source")
    }
    source_by_number = {
        text(item.get("number")): text(item.get("source"))
        for item in historical.get("sources", [])
        if item.get("number") is not None and item.get("source")
    }
    source_by_number.update(
        {text(item.get("numero")): item["fonte"] for item in inventory if item.get("numero")}
    )
    snapshot_by_source = {
        text(item.get("source")): item for item in snapshot.get("sources", []) if item.get("source")
    }
    snapshot_catalogue_by_id: dict[str, dict[str, Any]] = {}
    for contest in snapshot.get("catalogue", []):
        if contest.get("id") is not None:
            snapshot_catalogue_by_id[text(contest["id"])] = contest

    # The API receipt is newer than the DB snapshot for applied amendments.
    # Merge its current fields into the snapshot records so source identity is
    # retained while dates/review state come from the real API checkpoint.
    api_catalogue = api_current.get("catalogue") if isinstance(api_current, dict) else None
    if isinstance(api_catalogue, list) and api_catalogue:
        current_catalogue = []
        for api_contest in api_catalogue:
            if not isinstance(api_contest, dict):
                continue
            contest_id = text(api_contest.get("id"))
            merged = dict(snapshot_catalogue_by_id.get(contest_id, {}))
            merged.update(api_contest)
            current_catalogue.append(merged)
    else:
        current_catalogue = list(snapshot.get("catalogue", []))

    catalogue_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    catalogue_by_id: dict[str, dict[str, Any]] = {}
    for contest in current_catalogue:
        source_id = text(contest.get("source_id"))
        source = source_by_number.get(source_id, source_id)
        catalogue_by_source[source].append(contest)
        if contest.get("id") is not None:
            catalogue_by_id[text(contest["id"])] = contest

    pending_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if isinstance(api_catalogue, list) and api_catalogue:
        pending_items = [item for item in current_catalogue if (item.get("review") or {}).get("pending", False)]
    elif isinstance(pending_api, dict):
        pending_items = pending_api.get("pending", pending_api.get("items", []))
    elif isinstance(pending_api, list):
        pending_items = pending_api
    else:
        pending_items = []
    for item in pending_items:
        if not isinstance(item, dict) or not (item.get("review") or {}).get("pending", False):
            continue
        contest_id = text(value(item, "id", "concurso_id", "contest_id"))
        contest = catalogue_by_id.get(contest_id)
        if contest:
            pending_by_source[source_by_number.get(text(contest.get("source_id")), text(contest.get("source_id")))].append(item)
    app_details: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for detail in app.get("verified_details", []):
        app_details[text(detail.get("source"))].append(detail)

    failed_source_by_name = {
        text(item.get("source")): item
        for item in failed_sources.get("sources", [])
        if isinstance(item, dict) and item.get("source")
    }
    failed_tenderproof_by_name = {
        text(item.get("source")): item
        for item in failed_tenderproof.get("sources", [])
        if isinstance(item, dict) and item.get("source")
    }

    # Additional receipts are evidence inputs only. They never override the
    # historical source status by themselves.
    result_paths = [Path(path) for path in args.result if Path(path).exists()]
    result_paths.extend(
        path
        for path in sorted(COMPLETION.glob("delivery-result-*.json"))
        if path not in result_paths
    )
    result_evidence = [str(path) for path in result_paths]
    snapshot_evidence = str(snapshot_path)
    api_evidence = str(api_current_path) if api_current_path else ""
    failed_sources_evidence = str(failed_sources_path) if failed_sources_path else ""
    failed_tenderproof_evidence = str(failed_tenderproof_path) if failed_tenderproof_path else ""
    api_ui_verified = api_current.get("ui_verified") if api_current else None
    api_version_count = text((api_current.get("counts") or {}).get("versions")) if api_current else ""
    api_notification_count = text((api_current.get("counts") or {}).get("notifications")) if api_current else ""
    rows: list[dict[str, str]] = []

    for item in inventory:
        source = item["fonte"]
        old = historical_by_source.get(source, {})
        current = snapshot_by_source.get(source, {})
        catalogues = catalogue_by_source.get(source, [])
        pending = pending_by_source.get(source, [])
        app_items = app_details.get(source, [])
        blocked = EXTERNAL_BLOCKS.get(source)
        implementation = text(old.get("implementation_state"),) or "unknown"
        adapter = item.get("adaptador", "")
        historical_success = int(item.get("coletas_detalhe_bem_sucedidas_historicas") or 0)
        enabled = text(current.get("enabled"))
        latest_cycle = current.get("latest_cycle") or {}
        jobs = current.get("historical_detail_jobs") or {}
        current_success = int(jobs.get("succeeded") or 0)
        published_ids = [text(c.get("id")) for c in catalogues if c.get("id") is not None]
        failed_source = failed_source_by_name.get(source, {})
        failed_run = failed_tenderproof_by_name.get(source, {})
        failed_outcome = text(failed_source.get("outcome"))
        failed_listing_status = text((failed_source.get("listing") or [{}])[0].get("status"))
        failed_detail_count = len(failed_source.get("details") or [])
        failed_document_count = len(failed_source.get("documents") or [])
        run_execution = text(failed_run.get("execution_status"))
        run_validation = text(failed_run.get("validation_status"))
        run_error = text(failed_run.get("error"))
        run_fields = failed_run.get("fields") or []
        run_field_states: dict[str, int] = defaultdict(int)
        for field in run_fields:
            if isinstance(field, dict):
                run_field_states[text(field.get("state", "unknown"))] += 1
        recent_receipt_summary: list[str] = []
        if failed_source:
            recent_receipt_summary.append(
                f"bounded={failed_outcome or 'unknown'}, listing_http={failed_listing_status or 'unknown'}, details={failed_detail_count}, documents={failed_document_count}"
            )
        if failed_run:
            field_summary = ",".join(f"{key}={value_}" for key, value_ in sorted(run_field_states.items())) or "none"
            recent_receipt_summary.append(
                f"tenderproof={run_execution or 'unknown'}/{run_validation or 'unknown'}, fields={field_summary}, review_required={text((failed_run.get('review_manifest') or {}).get('review_required'))}"
            )
        recent_receipt_summary = unique(recent_receipt_summary)

        human_dependency = HUMAN_DEPENDENCIES.get(source)
        if blocked:
            objective = "bloqueada_externamente"
        elif human_dependency:
            objective = "dependencia_humana"
        else:
            objective = "parcial"

        gaps = requirement_gaps(old)
        if blocked:
            gaps = ["aquisição corrente interrompida antes de descoberta utilizável", *gaps]
        elif human_dependency:
            titles = [text(doc.get("title", doc.get("kind"))) for p in pending for doc in p.get("review", {}).get("documents", [])]
            if titles:
                gaps.insert(0, "revisão humana dos documentos: " + ", ".join(unique(titles)))
            else:
                gaps.insert(0, "revisão humana do pacote documental pendente")
            gaps.insert(0, "conflito de identidade/vínculo documental requer decisão de autoridade")
        elif pending:
            gaps.insert(0, "retificação/documento novo pendente de aplicação interna; autorização já registrada")
        if not adapter:
            gaps.insert(0, "sem adaptador registrado; descoberta/aquisição ainda não executada")
        elif historical_success == 0 and current_success == 0:
            gaps.insert(0, "nenhum trabalho de detalhe bem-sucedido no histórico disponível")
        if catalogues:
            gaps.insert(0, "catálogo publicado não equivale a cobertura integral da fonte")
            if api_current:
                gaps = [gap for gap in gaps if not gap.startswith("publicação e sincronização=")]
                if api_ui_verified is False:
                    gaps.insert(0, "verificação visual/UI ainda não confirmada (API atual verificada)")
        if failed_source or failed_run:
            if run_error:
                gaps.insert(0, f"receipt recente: {run_error[:240]}")
            elif failed_outcome and failed_outcome != "detail_acquired":
                gaps.insert(0, f"receipt recente: {failed_outcome} (escopo delimitado)")
            elif failed_run and run_validation != "valid":
                gaps.insert(0, f"receipt TenderProof recente: execution={run_execution or 'unknown'}, validation={run_validation or 'unknown'}")
            elif not catalogues:
                gaps.insert(0, "coleta recente sem publicação no catálogo")
        if source == 'legalle_open' and not catalogues:
            gaps.insert(0, 'Garibaldi 04/2025: revisão preservada confirma Secretário de Escola até20h→40h e resultado/homologação22/12/2025; composição dos efeitos ainda não implementada/publicada')
        if source == 'elo_open' and not catalogues:
            gaps.insert(0, 'Barra Longa 01/2026: rascunho de revisão confirma TAF→títulos e novos prazos de títulos/resultado; publicação inicial composta ainda pendente')
        if source == 'avancasp_open' and not catalogues:
            gaps.insert(0, 'Itapecerica da Serra 02/2026: prorrogação de inscrições04→07/05, pagamento05→08/05 e prova prática25→26/07; documentos preservados, composição/aplicação pendentes')
        if source in {'fapemig_selection', 'fapesq_selection', 'fapepi_selection'} and not catalogues:
            gaps.insert(0, 'Pacote documental 2026 preservado identifica financiamento/bolsa sem vínculo empregatício; modalidade não publicável como emprego pelo contrato atual, sem converter auxílio em salário')
        gaps = unique(gaps)

        if catalogues:
            scope = (
                f"Fonte {source}: {len(catalogues)} concurso(s) publicado(s) no catálogo "
                f"(IDs {','.join(published_ids)}); execução delimitada aos campos/documentos aprovados desses registros."
            )
        elif historical_success > 0:
            scope = (
                f"Fonte {source}: somente os runs históricos com detalhe bem-sucedido "
                f"({historical_success} no inventário; {current_success} no snapshot atual) e seus documentos preservados."
            )
        elif adapter:
            scope = f"Fonte {source}: adaptador/configuração registrados; nenhum detalhe bem-sucedido confirmado neste recorte."
        else:
            scope = f"Fonte {source}: inventário nominal; não há adaptador nem coleta de detalhe confirmada."

        proof: list[str] = [
            f"{status_path.as_posix()}#sources[{source}]",
            f"{inventory_path.as_posix()}#fonte={source}",
            snapshot_evidence,
        ]
        proof.extend(flatten_evidence(old.get("requirements", {})))
        proof.extend(flatten_evidence(old.get("findings", [])))
        proof.extend(result_evidence)
        if api_evidence:
            proof.append(api_evidence)
        if failed_sources_evidence and failed_source:
            proof.append(f"{failed_sources_evidence}#sources[source={source}]")
        if failed_tenderproof_evidence and failed_run:
            proof.append(f"{failed_tenderproof_evidence}#sources[source={source}]")
        if pedrinhas_applied_path and source == "fenix_open":
            proof.append(str(pedrinhas_applied_path))
        if source == 'legalle_open':
            proof.append('runtime:/var/lib/observador/tenderproof/product-completion/delivery-legalle-review-20260909T220726095061Z.json')
        if source == 'elo_open':
            proof.append('runtime:/var/lib/observador/tenderproof/product-completion/delivery-elo-effects-draft-20260909.json')
        if source == 'avancasp_open':
            proof.append('backend/.tenderproof/product-completion/delivery-next-avancasp-effects-20260909.json')
        if source in {'fapemig_selection', 'fapesq_selection', 'fapepi_selection'}:
            proof.append('backend/.tenderproof/product-completion/delivery-next-bounded-cases-20260909.json')
        if catalogues:
            proof.append(f"{snapshot_evidence}#catalogue[contest_ids={','.join(published_ids)}]")
        if app_items:
            proof.append(f"{Path(args.app).as_posix()}#verified_details[source={source}]")
        if pending:
            proof.append(f"{api_evidence or Path(args.pending).as_posix()}#pending[contest_source={source}]")
        if blocked:
            proof.extend(blocked["evidence"].split(" | "))
            proof.append("docs/ENTREGA-BLOQUEIOS-FONTES.md")
        if human_dependency:
            proof.append(human_dependency["proof"])
        proof = unique(proof)

        if blocked:
            resume = blocked["resume"]
        elif human_dependency:
            resume = human_dependency["resume"]
        elif pending:
            resume = "Conferir o documento pendente, registrar os efeitos comprovados e sincronizar; a aplicação deve seguir a autorização e a revisão documental vigente."
        elif not adapter:
            resume = "Implementar aquisição após confirmar o endereço/escopo da fonte; executar detalhe, identidade, revisão, publicação e sincronização com evidência."
        elif historical_success == 0 and current_success == 0:
            resume = "Examinar o erro/ciclo preservado e obter uma coleta de detalhe delimitada; não repetir acesso sem hipótese concreta."
        else:
            resume = "Retomar pelos runs preservados: conferir campos e retificações, preparar/aprovar proposta, sincronizar e repetir o ciclo para cobrir o escopo declarado."

        rows.append(
            {
                "numero": item.get("numero", ""),
                "fonte": source,
                "nome": item.get("nome", ""),
                "status_objetivo": objective,
                "escopo_verificavel": scope,
                "fato_objetivo": (
                    blocked["proof"]
                    if blocked
                    else "Conflito de identidade: cabeçalho PROCESSO SELETIVO 001/2026 versus edital-base 002/2026"
                    if human_dependency
                    else f"Receipt recente: {run_error[:240]}"
                    if run_error
                    else f"Receipt recente: {failed_outcome} (escopo delimitado)"
                    if failed_outcome and failed_outcome != "detail_acquired"
                    else "Retificação aplicada na API atual; verificação visual/UI ainda não confirmada"
                    if source == "fenix_open" and api_current
                    else "API atual confirmou detalhe e revisão no recorte publicado"
                    if api_current and catalogues
                    else "Coleta recente preservada; publicação e revisão permanecem pendentes"
                    if failed_source or failed_run
                    else ""
                ),
                "lacunas": " | ".join(gaps),
                "evidencia_especifica": " | ".join(proof),
                "condicao_retomada": resume,
                "adaptador_historico": adapter,
                "implementation_state_historico": implementation,
                "enabled_snapshot": enabled,
                "ciclo_atual": text(latest_cycle.get("cycle_id")),
                "ciclo_status": text(latest_cycle.get("status")),
                "detalhes_sucesso_snapshot": str(current_success),
                "detalhes_sucesso_historicos_csv": str(historical_success),
                "concursos_no_aplicativo": ",".join(published_ids),
                "ui_verificada_api_atual": text(api_ui_verified),
                "versoes_api_atual": api_version_count,
                "notificacoes_api_atual": api_notification_count,
                "receipts_recentes": " | ".join(recent_receipt_summary),
                "erro_receipt_recente": run_error or text(failed_source.get("error")),
                "documentos_pendentes": " | ".join(
                    text(doc.get("title", doc.get("kind")))
                    for p in pending
                    for doc in p.get("review", {}).get("documents", [])
                ),
                "acao_minima": resume,
            }
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)

    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[row["status_objetivo"]] += 1
    print(
        json.dumps(
            {
                "output": str(output),
                "sources": len(rows),
                "status_counts": dict(counts),
                "snapshot": str(snapshot_path),
                "snapshot_is_fresh_delivery_current": is_fresh,
                "api_current": str(api_current_path) if api_current_path else None,
                "failed_sources": str(failed_sources_path) if failed_sources_path else None,
                "failed_tenderproof": str(failed_tenderproof_path) if failed_tenderproof_path else None,
                "pedrinhas_applied": str(pedrinhas_applied_path) if pedrinhas_applied_path else None,
                "historical_status_preserved": True,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
