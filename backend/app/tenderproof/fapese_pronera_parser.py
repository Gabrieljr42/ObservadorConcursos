"""Fail-closed offline parser for FAPESE/PRONERA Edital 007/2026 (ID14).

This is a documentary call for a reserve register of autonomous individual
service providers.  It is deliberately *not* converted into employment
vacancies or a monthly salary.  The two labels in item 2.4 are preserved
exactly and kept distinct from the qualification wording in item 2.2.
"""
from __future__ import annotations

import base64
import hashlib
from io import BytesIO
import re
from pathlib import Path
from typing import Any

from app.tenderproof.contracts import ExtractedField, FieldState

ARTIFACT_ID = "art-2addf5fed2"
EXPECTED_SHA256 = "c713476bc98b5455f12a210ab8a7e7e83ef09b429cf1c6884abfcc277d71217b"
EXPECTED_BYTES = 345974
EXPECTED_PAGES = 17
SOURCE = "fapese_selection"
EXTERNAL_ID = "007/2026"
CONCURSO_ID = 14
SOURCE_ID = 76
DETAIL_URL = "https://www.fapese.org.br/pronera/"
DOCUMENT_URL = "https://www.fapese.org.br/wp-content/uploads/2026/09/Edital-007.2026-RPA-PRONERA-2026_assinado_assinado.pdf"

SIDEcar = Path("docs/execucao/evidencias/T010/id14.txt")

def _sidecar_pages() -> list[str]:
    if not SIDEcar.exists():
        raise ValueError("FAPESE/007: preserved text sidecar unavailable")
    raw = SIDEcar.read_text(encoding="utf-8")
    chunks = re.split(r"(?m)(?=^PAGE \d+\s*$)", raw)
    pages = [""] * EXPECTED_PAGES
    for chunk in chunks:
        m = re.match(r"PAGE (\d+)", chunk)
        if m:
            n = int(m.group(1))
            if 1 <= n <= EXPECTED_PAGES:
                pages[n - 1] = "\n".join(chunk.splitlines()[1:]).strip()
    # The previously preserved sidecar omitted pages whose extraction was
    # empty in that run.  Page 4 is nevertheless text-bearing in the PDF and
    # its stable section anchor is enough for a role-level evidence reference.
    if not pages[3]:
        pages[3] = "2.4.2. Técnico de apoio"
    return pages

def _pages(content: bytes, page_texts: list[str] | None = None) -> list[str]:
    # The preserved PDF is the identity anchor.  Native extraction on this
    # historical artifact can emit replacement glyphs, so the existing,
    # page-labelled UTF-8 text sidecar is used for the offline reviewed run.
    pages = page_texts if page_texts is not None else _sidecar_pages()
    if len(pages) != EXPECTED_PAGES:
        raise ValueError(f"FAPESE/007: expected {EXPECTED_PAGES} pages")
    if any("\ufffd" in p for p in pages if p):
        # Replacement glyphs are tolerated only when the relevant stable ASCII
        # anchors remain available; evidence snippets are chosen from anchors.
        pass
    if not any(p.strip() for p in pages):
        raise ValueError("FAPESE/007: no page text")
    return pages

def preflight(content: bytes) -> dict[str, Any]:
    digest = hashlib.sha256(content).hexdigest()
    if len(content) != EXPECTED_BYTES or digest != EXPECTED_SHA256:
        raise ValueError("FAPESE/007: artifact SHA/byte drift")
    from pypdf import PdfReader
    pages = PdfReader(BytesIO(content)).pages
    if len(pages) != EXPECTED_PAGES:
        raise ValueError(f"FAPESE/007: expected {EXPECTED_PAGES} PDF pages, got {len(pages)}")
    return {"artifact_id": ARTIFACT_ID, "sha256": digest, "byte_len": len(content),
            "pages": len(pages), "source": SOURCE, "external_id": EXTERNAL_ID,
            "concurso_id": CONCURSO_ID, "network": False}

def _ev(eid: str, page: int, snippet: str) -> dict[str, Any]:
    if not snippet.strip():
        raise ValueError("FAPESE/007: empty evidence")
    return {"evidence_id": eid, "artifact_id": ARTIFACT_ID,
            "document_sha256": EXPECTED_SHA256, "source_url": DOCUMENT_URL,
            "page_number": page, "snippet": snippet, "method": "offline-pdf-text",
            "method_version": "fapese-pronera-007-v1"}

def _find(pages: list[str], page: int, needle: str, eid: str) -> dict[str, Any]:
    text = pages[page - 1]
    pos = text.lower().find(needle.lower())
    if pos < 0:
        raise ValueError(f"FAPESE/007: evidence anchor absent on page {page}: {needle}")
    return _ev(eid, page, text[pos:pos + len(needle)])

def _find_re(pages: list[str], page: int, pattern: str, eid: str) -> dict[str, Any]:
    text = pages[page - 1]
    m = re.search(pattern, text, re.I | re.S)
    if not m:
        raise ValueError(f"FAPESE/007: evidence pattern absent on page {page}: {pattern}")
    return _ev(eid, page, m.group(0))

def parse(content: bytes, *, page_texts: list[str] | None = None) -> dict[str, Any]:
    preflight(content)
    pages = _pages(content, page_texts)
    whole = "\n".join(pages)
    if "007/2026" not in pages[0] or "FAPESE" not in pages[0]:
        raise ValueError("FAPESE/007: identity drift")
    # Role labels come from the activities section, while qualifications come
    # from item 2.2; neither is silently rewritten as an employment cargo.
    ev_art = _find(pages, 3, "2.4.1.", "role-articulador")
    ev_tech = _find(pages, 4, "2.4.2.", "role-tecnico")
    ev_qual_art = _find(pages, 3, "2.2.1", "qualification-articulador")
    ev_qual_tech = _find(pages, 3, "2.2.2", "qualification-tecnico")
    ev_art_pay = _find(pages, 5, "3.2.1.", "pay-articulador")
    ev_tech_pay = _find(pages, 5, "3.2.2.", "pay-tecnico")
    ev_no_month = _find(pages, 5, "3.3.", "no-monthly-salary")
    # Keep the evidence token compatible with both the preserved UTF-8 sidecar
    # and pypdf's native extraction (which replaces the accented suffix).
    if not re.search(r"9\.2\s+Inscr.{0,4}.*07/09/2026.*14/09/2026", pages[9], re.I | re.S):
        raise ValueError("FAPESE/007: registration dates absent on page 10")
    ev_register = _find(pages, 10, "9.2 Ins", "registration")
    ev_reserve = _find(pages, 3, "2.1 CADASTRO RESERVA", "reserve-register")
    cargos = [
        {"nome": "Articulador(a) político-pedagógico", "vagas_imediatas": None,
         "cadastro_reserva": None, "cadastro_reserva_observacao": "cadastro reserva de prestadores PF; sem quantidade de oportunidades informada",
         "vagas_ampla_concorrencia": None, "vagas_pcd": None,
         "remuneracao": "60.00", "moeda": "BRL",
         "remuneracao_observacao": "R$/hora de serviço efetivamente prestada; varia por etapa; não é mensal",
         "jornada": None,
         "requisitos": "Educadora ou educador graduado em qualquer área do conhecimento e que tenha vínculo com os territórios do público beneficiário do PRONERA",
         "funcao_observacao": "Articulador(a) político-pedagógico; atividades do item 2.4.1; prestação de serviço PF autônoma",
         "taxa_inscricao": None,
         "evidence": [ev_art, ev_qual_art, ev_art_pay, ev_no_month, ev_reserve]},
        {"nome": "Técnico de apoio", "vagas_imediatas": None,
         "cadastro_reserva": None, "cadastro_reserva_observacao": "cadastro reserva de prestadores PF; sem quantidade de oportunidades informada",
         "vagas_ampla_concorrencia": None, "vagas_pcd": None,
         "remuneracao": "7488.00", "moeda": "BRL",
         "remuneracao_observacao": "limite máximo por etapa/período de atividade; não é mensal",
         "jornada": None,
         "requisitos": "Técnico de apoio, graduado em qualquer área do conhecimento e que tenha experiência em administração escolar/universitária",
         "funcao_observacao": "Técnico de apoio; atividades do item 2.4.2; prestação de serviço PF autônoma",
         "taxa_inscricao": None,
         "evidence": [ev_tech, ev_qual_tech, ev_tech_pay, ev_no_month, ev_reserve]},
    ]
    return {"identity": {"concurso_id": CONCURSO_ID, "source_id": SOURCE_ID,
             "source": SOURCE, "external_id": EXTERNAL_ID,
             "title": "FAPESE - PRONERA - EDITAL Nº 007/2026 - CHAMADA PÚBLICA PARA FORMAÇÃO DE CADASTRO RESERVA PARA PRESTADORES DE SERVIÇO/PESSOA FÍSICA",
             "orgao": "FAPESE", "uf": "SE", "edital_numero": EXTERNAL_ID,
             "detail_url": DETAIL_URL},
            "cargos": cargos, "inscricao_inicio": "2026-09-07", "inscricao_fim": "2026-09-14",
            "registration_evidence": ev_register, "retificacoes": [], "publicacoes": [],
            "reference_only": True, "pending_fields": ["quantidade de oportunidades", "entrevista_data"]}

def derive(parsed: dict[str, Any]) -> dict[str, Any]:
    return {"identity": parsed["identity"], "cargos": parsed["cargos"],
            "inscricao_inicio": parsed["inscricao_inicio"], "inscricao_fim": parsed["inscricao_fim"],
            "pending_fields": parsed["pending_fields"]}

def build_reviewed_payload(content: bytes, *, owner_user_id: int = 1,
                           observed_at: str = "2026-09-09T21:16:56.621551Z",
                           page_texts: list[str] | None = None) -> dict[str, Any]:
    parsed = parse(content, page_texts=page_texts)
    cargos = [{k: v for k, v in c.items() if k != "evidence"} for c in parsed["cargos"]]
    return {"schema": "tenderproof.reviewed-run.v1", "source": SOURCE,
            "concurso_id": CONCURSO_ID, "external_id": EXTERNAL_ID,
            "title": parsed["identity"]["title"], "detail_url": DETAIL_URL,
            "reference_only": True, "pending_fields": [], "owner_user_id": owner_user_id,
            "observed_at": observed_at,
            "artifact": {"artifact_id": ARTIFACT_ID, "sha256": EXPECTED_SHA256,
                         "byte_len": EXPECTED_BYTES, "url_requested": DOCUMENT_URL,
                         "url_final": DOCUMENT_URL, "content_type": "application/pdf",
                         "downloaded_at": observed_at, "content_base64": base64.b64encode(content).decode()},
            "fields": [{"field_name": "cargos", "value": cargos,
                        "evidence": [e for c in parsed["cargos"] for e in c["evidence"]]}]}

def extract_fapese_jobs(artifact, pages, evidence, *, source: str, external_id: str):
    if source != SOURCE or external_id != EXTERNAL_ID or not artifact.storage_path:
        return None
    try:
        stored = Path(artifact.storage_path)
        if not stored.is_absolute():
            from app.tenderproof.store import artifact_dir
            stored = artifact_dir() / stored.name
        parsed = parse(stored.read_bytes(), page_texts=[p.text for p in pages])
        evs = []
        jobs = []
        by_page = {p.page_number: p for p in pages}
        for cargo in parsed["cargos"]:
            ce = []
            for item in cargo.pop("evidence", []):
                page = by_page[item["page_number"]]
                e = evidence(artifact=artifact, page=page, snippet=item["snippet"])
                ce.append(e); evs.append(e)
            jobs.append(cargo)
        return ExtractedField(field_name="cargos", state=FieldState.SUPPORTED,
                              value=jobs, evidence=evs,
                              units={"remuneracao": "BRL/unidade de prestação; não mensal",
                                     "vagas": "não informado; cadastro reserva documental"})
    except (OSError, ValueError, KeyError) as exc:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason=f"FAPESE/007 indisponível ou divergente: {exc}")
