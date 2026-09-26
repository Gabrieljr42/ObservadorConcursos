"""Fail-closed offline parser for OMNI/Osvaldo Cruz contest 16 (246).

The PDF is historical (Edital 002/2024).  The printed spelling ``Médio
Ginecologista`` is intentionally preserved; this parser does not silently
correct source text.  No network, catalogue write, or publication is done.
"""
from __future__ import annotations

import base64
import hashlib
import re
from io import BytesIO
from typing import Any

from pypdf import PdfReader
from app.tenderproof.contracts import ExtractedField, FieldState

ARTIFACT_ID = "art-0a483f2ba1"
EXPECTED_SHA256 = "3503bf2995deba3d836da647369fd7a83ef2b220de10179900eafa4667841deb"
EXPECTED_BYTES = 396219
EXPECTED_PAGES = 23
SOURCE = "omni_open"
EXTERNAL_ID = "246"
CONCURSO_ID = 16
SOURCE_ID = 18
DETAIL_URL = "https://portal.omniconcursospublicos.com.br/informacoes/246/"
DOCUMENT_URL = "https://anexos.cdn.selecao.net.br/uploads/412/concursos/246/anexos/C2cjgnwNV6LmKcL1xoFVN7ptWDimvRO8VEU8TnJB.pdf"

_ROWS = [
    ("Bibliotecário", 1, "2327.96", "40h", "Curso de Nível Superior na Área e registro no órgão da classe", "15.00"),
    ("Chefe de Controle Interno", 0, "3682.45", "40h", "Ensino Superior", "15.00"),
    ("Cirurgião Dentista", 0, "3682.45", "20h", "Curso de Nível Superior na Área e registro no órgão da classe", "15.00"),
    ("Contador", 1, "8572.64", "40h", "Curso de Nível Superior em Contabilidade e registro no CRC", "15.00"),
    ("Coveiro", 0, "1556.49", "40h", "Ser alfabetizado", "10.00"),
    ("Cozinheiro", 1, "1556.49", "40h", "Alfabetizado e ter experiência no preparo e distribuição de refeições.", "10.00"),
    ("Dentista", 1, "3682.45", "20h", "Curso de Nível Superior na Área e registro no órgão da classe", "15.00"),
    ("Encanador", 0, "1872.33", "40h", "Ensino Fundamental Completo", "12.00"),
    ("Engenheiro de Segurança do Trabalho", 0, "3682.45", "40h", "Curso de Nível Superior, Registro no CREA ou CAU e pós – graduação em Engenharia de Segurança do Trabalho.", "15.00"),
    ("Farmacêutico Bioquímico", 0, "2327.96", "20h", "Curso de Nível Superior em Farmácia Bioquímica.", "15.00"),
    ("Fonoaudiólogo", 1, "2327.96", "20h", "Curso de Nível Superior Completo e registro no CRFA.", "15.00"),
    ("Médico Clínico Geral", 1, "3682.45", "10h", "Curso de Nível Superior em Medicina e registro no CRM.", "15.00"),
    ("Médico Geriatra", 1, "3682.45", "10h", "Curso de Nível Superior em medicina, especialização na área de Medicina Geriátrica e registro no CRM", "15.00"),
    ("Médio Ginecologista", 1, "3682.45", "10h", "Curso de Nível Superior em medicina, especialização na área e registro no CRM", "15.00"),
    ("Médico do Trabalho", 0, "3682.45", "10h", "Curso de Nível Superior em medicina, especialização na área e registro no CRM", "15.00"),
    ("Médico Pediatra", 1, "3682.45", "10h", "Curso de Nível Superior em medicina, especialização na área e registro no CRM", "15.00"),
    ("Padeiro", 0, "1872.33", "40h", "Ensino Fundamental Completo", "13.00"),
    ("Tratorista", 1, "1688.20", "40h", "Ensino Fundamental Completo e CNH “D” ou superior", "13.00"),
]


def _pages(content: bytes) -> list[str]:
    reader = PdfReader(BytesIO(content))
    if len(reader.pages) != EXPECTED_PAGES:
        raise ValueError(f"OMNI/246: expected {EXPECTED_PAGES} pages, got {len(reader.pages)}")
    pages = [(page.extract_text() or "") for page in reader.pages]
    if any("\ufffd" in page for page in pages):
        raise ValueError("OMNI/246: U+FFFD residual in native extraction")
    if any(not page.strip() for page in pages):
        raise ValueError("OMNI/246: empty page in native extraction")
    return pages


def preflight(content: bytes) -> dict[str, Any]:
    digest = hashlib.sha256(content).hexdigest()
    if len(content) != EXPECTED_BYTES or digest != EXPECTED_SHA256:
        raise ValueError("OMNI/246: artifact SHA/byte drift")
    pages = _pages(content)
    return {"artifact_id": ARTIFACT_ID, "sha256": digest, "byte_len": len(content),
            "pages": len(pages), "source": SOURCE, "external_id": EXTERNAL_ID,
            "concurso_id": CONCURSO_ID, "network": False}


def _evidence(page: int, snippet: str, evidence_id: str) -> dict[str, Any]:
    if not snippet.strip() or "\ufffd" in snippet:
        raise ValueError("OMNI/246: invalid evidence snippet")
    return {"evidence_id": evidence_id, "artifact_id": ARTIFACT_ID,
            "document_sha256": EXPECTED_SHA256, "source_url": DOCUMENT_URL,
            "page_number": page, "snippet": snippet, "method": "pypdf-native-text",
            "method_version": "omni-osvaldo-cruz-246/1"}


def _row_snippet(text: str, name: str, next_names: list[str]) -> str:
    start = text.find(name)
    if start < 0:
        # Table extraction can wrap long names; locate the stable first token.
        start = text.find(name.split()[0])
    if start < 0:
        raise ValueError(f"OMNI/246: row missing: {name}")
    ends = [text.find(candidate, start + len(name)) for candidate in next_names]
    ends = [end for end in ends if end >= 0]
    return text[start:min(ends) if ends else len(text)].strip()


def parse(content: bytes, *, page_texts: list[str] | None = None) -> dict[str, Any]:
    preflight(content)
    pages = page_texts if page_texts is not None else _pages(content)
    if len(pages) != EXPECTED_PAGES or any("\ufffd" in page for page in pages):
        raise ValueError("OMNI/246: supplied page text is incomplete or contains U+FFFD")
    if "OSVALDO CRUZ" not in pages[0] or "002/2024" not in pages[0] or "OMNI" not in pages[0]:
        raise ValueError("OMNI/246: identity drift")
    if "12/01/2025" not in "\n".join(pages[21:23]):
        raise ValueError("OMNI/246: historical exam date not found")
    page1, page2 = pages[0], pages[1]
    names1 = [row[0] for row in _ROWS[:13]]
    names2 = [row[0] for row in _ROWS[13:]]
    cargos = []
    for index, (name, immediate, salary, hours, requirement, fee) in enumerate(_ROWS):
        page_number, text, names = (1, page1, names1) if index < 13 else (2, page2, names2)
        snippet = _row_snippet(text, name, names[index + 1:] if index < 13 else names2[index - 13 + 1:])
        if f"R$ {salary[:1]}.{salary[1:4]},{salary[5:]}" not in snippet or hours not in snippet:
            raise ValueError(f"OMNI/246: incomplete row: {name}")
        cargos.append({"nome": name, "vagas_imediatas": immediate,
                       "cadastro_reserva": immediate == 0,
                       "vagas_ampla_concorrencia": immediate if immediate else 0,
                       "remuneracao": salary, "moeda": "BRL",
                       "remuneracao_observacao": "salário base mensal",
                       "jornada": hours, "requisitos": requirement,
                       "taxa_inscricao": fee,
                       "evidence": [_evidence(page_number, snippet, f"cargo-{index + 1}")]})
    identity_snippet = next((line.strip() for line in pages[21].splitlines()
                             if "PREFEITURA MUNICIPAL DE OSVALDO CRUZ" in line and "002/2024" in line), None)
    if not identity_snippet:
        raise ValueError("OMNI/246: identity/evidence line absent")
    prova_match = re.search(r"12/01/2025[^\n]{0,120}Realiza[çc][aã]o da Prova Escrita Objetiva", pages[21], re.I)
    if not prova_match:
        raise ValueError("OMNI/246: exam-date evidence absent")
    prova_evidence = _evidence(22, prova_match.group(0), "prova-data")
    return {"identity": {"concurso_id": CONCURSO_ID, "source_id": SOURCE_ID,
                          "source": SOURCE, "external_id": EXTERNAL_ID,
                          "title": "Concurso Público - 002/2024 - Prefeitura Municipal de Osvaldo Cruz -SP",
                          "orgao": "Prefeitura Municipal de Osvaldo Cruz", "uf": "SP",
                          "edital_numero": "002/2024", "detail_url": DETAIL_URL},
            "cargos": cargos, "prova_data": "2025-01-12", "retificacoes": [],
            "identity_evidence": _evidence(22, identity_snippet, "identity-orgao-edital"),
            "prova_evidence": prova_evidence,
            "reference_only": True, "pending_fields": []}


def build_reviewed_payload(content: bytes, *, owner_user_id: int = 1,
                           observed_at: str = "2026-09-13T00:00:00Z",
                           page_texts: list[str] | None = None) -> dict[str, Any]:
    parsed = parse(content, page_texts=page_texts)
    # ReviewedField carries the canonical evidence list.  Do not duplicate
    # evidence inside each cargo value: the real importer strips that legacy
    # duplication before hashing, so emitting it here would create a false
    # run-id mismatch (same cargo semantics, different envelope shape).
    cargo_values = [{key: value for key, value in cargo.items() if key != "evidence"}
                    for cargo in parsed["cargos"]]
    return {"schema": "tenderproof.reviewed-run.v1", "source": SOURCE,
            "concurso_id": CONCURSO_ID, "external_id": EXTERNAL_ID,
            "title": parsed["identity"]["title"], "detail_url": DETAIL_URL,
            "reference_only": True, "pending_fields": [], "owner_user_id": owner_user_id,
            "observed_at": observed_at,
            "artifact": {"artifact_id": ARTIFACT_ID, "sha256": EXPECTED_SHA256,
                         "byte_len": EXPECTED_BYTES, "url_requested": DOCUMENT_URL,
                         "url_final": DOCUMENT_URL, "content_type": "application/pdf",
                         "downloaded_at": observed_at,
                         "content_base64": base64.b64encode(content).decode()},
            "fields": [
                {"field_name": "cargos", "value": cargo_values,
                 "evidence": [e for cargo in parsed["cargos"] for e in cargo["evidence"]]},
                {"field_name": "prova_data", "value": "2025-01-12",
                 "original_value": "12/01/2025", "evidence": [parsed["prova_evidence"]]},
            ]}


def derive(parsed: dict[str, Any]) -> dict[str, Any]:
    return {"identity": parsed["identity"], "cargos": parsed["cargos"],
            "prova_data": parsed["prova_data"], "retificacoes": parsed["retificacoes"]}


def extract_prova_data(artifact, pages, evidence) -> ExtractedField:
    """Extract the historical exam date from the preserved timetable page."""
    page = next((p for p in pages if p.page_number == 22), None)
    if page is None or page.error or page.truncated:
        return ExtractedField(field_name="prova_data", state=FieldState.FAILED,
                              reason="OMNI/246: cronograma page 22 unavailable")
    match = re.search(r"12/01/2025[^\n]{0,120}Realiza[çc][aã]o da Prova Escrita Objetiva", page.text, re.I)
    if not match:
        return ExtractedField(field_name="prova_data", state=FieldState.UNKNOWN,
                              reason="OMNI/246: historical exam date not reproduced")
    snippet = match.group(0)
    return ExtractedField(field_name="prova_data", state=FieldState.SUPPORTED,
                          value="2025-01-12", original_value="12/01/2025",
                          evidence=[evidence(artifact=artifact, page=page, snippet=snippet)])
