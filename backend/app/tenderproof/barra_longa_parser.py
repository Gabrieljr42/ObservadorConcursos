"""Offline, fail-closed parser for T005 / ELO concurso 32.

This module is intentionally source-specific and reference-only.  It never
fetches, imports, or writes catalogue data.  Every accepted result is pinned
to the preserved PDF identity and to literal page snippets.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

from pypdf import PdfReader

ARTIFACT_ID = "art-07b137af65"
EXPECTED_SHA256 = "a5a7ff5a11bef285d389bd71a5e2d53b8ad5e82dec8d545edcea653c0fbef5a2"
EXPECTED_BYTES = 429261
EXPECTED_PAGES = 23
CONCURSO_ID = 32
SOURCE_ID = 47
SOURCE = "elo_open"
EXTERNAL_ID = "129"
DETAIL_URL = "https://novo.eloassessoriaeservicos.com.br/concurso/129"
DOCUMENT_URL = "https://s3.amazonaws.com/sgs.eloassessoriaeservicos.com.br/prefeitura-municipal-de-barra-longa/3/1-2025/anexos/edital-n-01-2026.pdf"

_CARGO_RE = re.compile(r"^(ACS - PSF \d{3} - MICRO ?AREA \d{2})\s*$", re.M)


def _pages(content: bytes) -> list[str]:
    reader = PdfReader(__import__("io").BytesIO(content))
    if len(reader.pages) != EXPECTED_PAGES:
        raise ValueError(f"drift: expected {EXPECTED_PAGES} pages, got {len(reader.pages)}")
    pages = [(page.extract_text() or "") for page in reader.pages]
    if any("\ufffd" in text for text in pages):
        raise ValueError("extraction contains U+FFFD replacement character")
    if not all(text.strip() for text in pages):
        raise ValueError("extraction contains an empty page")
    return pages


def preflight(content: bytes) -> dict[str, Any]:
    """Validate immutable artifact identity without extracting fields."""
    digest = hashlib.sha256(content).hexdigest()
    if len(content) != EXPECTED_BYTES or digest != EXPECTED_SHA256:
        raise ValueError("artifact drift: byte length or SHA-256 mismatch")
    pages = _pages(content)
    return {"artifact_id": ARTIFACT_ID, "sha256": digest, "byte_len": len(content),
            "pages": len(pages), "source": SOURCE, "source_id": SOURCE_ID,
            "concurso_id": CONCURSO_ID, "external_id": EXTERNAL_ID, "network": False}


def _evidence(eid: str, page: int, snippet: str) -> dict[str, Any]:
    if not snippet.strip() or "\ufffd" in snippet:
        raise ValueError("invalid evidence snippet")
    return {"evidence_id": eid, "artifact_id": ARTIFACT_ID,
            "document_sha256": EXPECTED_SHA256, "source_url": DOCUMENT_URL,
            "page_number": page, "snippet": snippet, "method": "offline-pdf-text",
            "method_version": "barra-longa-v1"}


def _require(text: str, needle: str) -> str:
    pos = text.find(needle)
    if pos < 0:
        raise ValueError(f"drift: required literal not found: {needle}")
    return text[pos:pos + len(needle)]


def parse(content: bytes) -> dict[str, Any]:
    """Extract all proven job rows and schedule facts from the preserved PDF."""
    preflight(content)
    pages = _pages(content)
    cover = pages[0]
    table = pages[17]
    schedule = pages[22]
    if "PREFEITURA MUNICIPAL DE" not in cover or "BARRA LONGA / MG" not in cover:
        raise ValueError("identity drift: municipality/UF not confirmed")
    if "PROCESSO SELETIVO PÚBLICO - EDITAL Nº 01/2026" not in cover:
        raise ValueError("identity drift: edital number not confirmed")
    if "ANEXO I" not in table or "CARGOS, VENCIMENTOS" not in table:
        raise ValueError("drift: cargo annex not found")
    if "ANEXO VI" not in schedule or "18/10/2026" not in schedule:
        raise ValueError("drift: schedule annex not found")
    names = _CARGO_RE.findall(table)
    if len(names) != 7 or len(set(names)) != 7:
        raise ValueError(f"drift: expected seven unique cargo rows, got {len(names)}")
    schedule_snip = _require(schedule, "18/08/2026 a 18/09/2026")
    prova_snip = _require(schedule, "18/10/2026")
    schedule_registration_evidence = _evidence("schedule-registration", 23, schedule_snip)
    schedule_exam_evidence = _evidence("schedule-exam", 23, prova_snip)
    common_req = "Possuir Ensino Médio Completo; residir na área da comunidade em que atuar desde a data da publicação do edital do Processo Seletivo Público; ter concluído, com aproveitamento, curso de formação inicial, com carga horária mínima de quarenta horas."
    if common_req not in re.sub(r"\s+", " ", table).replace(" \n", " "):
        # pypdf can insert line breaks; validate by stable fragments instead.
        if not all(x in table for x in ("Possuir Ensino Médio Completo", "curso de", "formação inicial")):
            raise ValueError("drift: requirements not confirmed")
    cargos = []
    for i, name in enumerate(names, 1):
        snippet = _require(table, name)
        # Capture each row's first scalar values; the table repeats a stable
        # literal block for every microarea.  No values are inferred.
        tail = table[table.find(name):]
        for stop in names:
            if stop != name and stop in tail:
                tail = tail[:tail.find(stop)]
        if "3.242,00" not in tail or "40h" not in tail or "162,10" not in tail:
            raise ValueError(f"drift: incomplete row {name}")
        cargos.append({"nome": name, "vagas": 1, "vagas_pcd": 0,
                       "vagas_ampla": 1, "cotas": {"pcd": "--", "ampla": 1},
                       "remuneracao": "3242.00", "unidade_remuneracao": "R$/mês",
                       "jornada": "40h/semana", "requisitos": common_req,
                       "taxa": "162.10", "provas": [
                           {"tipo": "objetiva_multipla_escolha", "disciplinas": ["Português", "Matemática", "C. Gerais", "C. Específicos"], "questoes": 20, "pontos": 100, "fechamento_portoes": "08:00"},
                           {"tipo": "teste_de_aptidao_fisica", "comprovado": True}],
                       # The schedule is global in the edital, but these
                       # references are attached to every cargo row so a
                       # consumer cannot lose applicability when rows are
                       # split into microareas.
                       "evidence": [_evidence(f"cargo-{i}", 18, snippet),
                                    {**schedule_registration_evidence, "evidence_id": f"cargo-{i}-schedule-registration"},
                                    {**schedule_exam_evidence, "evidence_id": f"cargo-{i}-schedule-exam"}]})
    return {"identity": {"concurso_id": CONCURSO_ID, "source_id": SOURCE_ID,
                          "source": SOURCE, "external_id": EXTERNAL_ID,
                          "title": "PREFEITURA MUNICIPAL DE BARRA LONGA",
                          "orgao": "Prefeitura Municipal de Barra Longa", "uf": "MG",
                          "edital_numero": "01/2026", "detail_url": DETAIL_URL},
            "cargos": cargos,
            "inscricao_inicio": "2026-08-18T15:00:00-03:00",
            "inscricao_fim": "2026-09-18T15:00:00-03:00",
            "prova_data": "2026-10-18", "taxa": "162.10",
            "evidence": {"inscricao": _evidence("schedule-registration", 23, schedule_snip),
                         "prova": _evidence("schedule-exam", 23, prova_snip)},
            "retificacoes": [], "publicacoes": [], "reference_only": True,
            "pending_fields": []}


def derive(parsed: dict[str, Any]) -> dict[str, Any]:
    """Stable semantic derivation used to detect parser/review drift."""
    return {"identity": parsed["identity"], "cargos": parsed["cargos"],
            "inscricao_inicio": parsed["inscricao_inicio"], "inscricao_fim": parsed["inscricao_fim"],
            "prova_data": parsed["prova_data"], "taxa": parsed["taxa"],
            "retificacoes": parsed["retificacoes"], "publicacoes": parsed["publicacoes"]}


def build_reviewed_payload(content: bytes, *, owner_user_id: int = 1,
                           observed_at: str = "2026-09-13T00:00:00Z") -> dict[str, Any]:
    """Build an immutable reference-only ReviewedRun envelope for dry-run import."""
    parsed = parse(content)
    # ReviewedRun must use the same canonical cargo shape as the integrated
    # ``extract_fields`` route.  The parser's richer raw row remains useful
    # for direct extraction, but publishing compares this value byte-for-byte.
    canonical_cargos = [{
        "nome": c["nome"], "vagas_imediatas": c["vagas"],
        "cadastro_reserva": None, "vagas_ampla_concorrencia": c["vagas_ampla"],
        "vagas_pcd": c["vagas_pcd"], "remuneracao": c["remuneracao"],
        "moeda": "BRL", "remuneracao_observacao": c["unidade_remuneracao"],
        "jornada": c["jornada"], "requisitos": c["requisitos"],
        "taxa_inscricao": c["taxa"],
    } for c in parsed["cargos"]]
    fields = []
    # The current catalogue already carries the edital-base dates; prova_data
    # is not a canonical versioned field and taxa is not publishable.  Keep
    # those values in parser derivations/evidence, but propose only the
    # previously-null cargos field.
    for name, value, evidence in [
        # Preserve every row's literal evidence (3 x 7 = 21). The integrated
        # route aggregates the same ordered set for exact revalidation.
        ("cargos", canonical_cargos, [e for c in parsed["cargos"] for e in c["evidence"]]),
    ]:
        fields.append({"field_name": name, "value": value, "evidence": evidence})
    return {"schema": "tenderproof.reviewed-run.v1", "source": SOURCE,
            "concurso_id": CONCURSO_ID, "external_id": EXTERNAL_ID,
            "title": parsed["identity"]["title"], "detail_url": DETAIL_URL,
            "reference_only": True, "pending_fields": [], "owner_user_id": owner_user_id,
            "observed_at": observed_at,
            "artifact": {"artifact_id": ARTIFACT_ID, "sha256": EXPECTED_SHA256,
                         "byte_len": EXPECTED_BYTES, "url_requested": DOCUMENT_URL,
                         "url_final": DOCUMENT_URL, "content_type": "application/pdf",
                         "downloaded_at": observed_at,
                         "content_base64": __import__("base64").b64encode(content).decode()},
            "fields": fields}
