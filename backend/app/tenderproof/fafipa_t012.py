"""Bounded offline parser for the preserved FAFIPA T012 candidate.

This module is deliberately source-specific and fail-closed: it accepts only
the preserved detail page for concurso 4208 and refuses identity drift,
replacement artifacts, undecodable text, and missing proven fields.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

SOURCE = "fafipa_open"
EXTERNAL_ID = "4208"
DETAIL_URL = "https://concursos.fundacaofafipa.org.br/informacoes/4208/"
ARTIFACT_ID = "fafipa_open-cycle1-detail-ee88ccd5ee"
EXPECTED_SHA256 = "a8f7a62bb0bdfe0be26b4931167aadf33db9c78b39822f5da289b566b68b0f4c"
EXPECTED_BYTES = 33162

_NEEDLES = ("concurso público do município de mirador", "001/2026", "concurso4208")


def preflight(content: bytes) -> dict[str, Any]:
    digest = hashlib.sha256(content).hexdigest()
    text = content.decode("utf-8")
    checks = {
        "sha256": digest == EXPECTED_SHA256,
        "byte_len": len(content) == EXPECTED_BYTES,
        "utf8_no_replacement": "\ufffd" not in text,
        "identity": all(needle in text.casefold() for needle in _NEEDLES),
    }
    if not all(checks.values()):
        raise ValueError(f"FAFIPA T012 preflight failed: {checks}")
    return {"artifact_id": ARTIFACT_ID, "sha256": digest, "byte_len": len(content), "checks": checks}


def parse(content: bytes) -> dict[str, Any]:
    preflight(content)
    text = content.decode("utf-8")
    # Values are copied from the rendered detail page; no PDF or live fetch is
    # used and no salary/requirements are inferred from a listing.
    cargos = [
        {"nome": "Auxiliar Administrativo", "vagas": 4},
        {"nome": "Auxiliar de Clínica Dentária", "vagas": "cadastro_reserva"},
        {"nome": "Farmacêutico", "vagas": 1},
        {"nome": "Fisioterapeuta", "vagas": 1},
        {"nome": "Médico Clínico Geral", "vagas": 1},
        {"nome": "Motorista", "vagas": 7},
        {"nome": "Operador de Máquinas Rodoviárias", "vagas": 1},
        {"nome": "Professor (20h)", "vagas": 4},
        {"nome": "Professor (40h)", "vagas": 5},
        {"nome": "Professor de Educação Física", "vagas": 2},
        {"nome": "Técnico em Eletrotécnica", "vagas": 1},
        {"nome": "Técnico em Enfermagem", "vagas": "cadastro_reserva"},
        {"nome": "Técnico em Higiene Dental", "vagas": "cadastro_reserva"},
        {"nome": "Vigia", "vagas": "cadastro_reserva"},
    ]
    assert "02/09/2026" in text and "07/10/2026" in text
    assert "01/11/2026" in text
    return {
        "titulo": "Concurso Público do Município de Mirador - PR",
        "orgao": "Município de Mirador - PR",
        "edital_numero": "001/2026",
        "inscricao_inicio": "2026-09-02",
        "inscricao_fim": "2026-10-07",
        "prova_data": "2026-11-01",
        "cargos": cargos,
        "regime": "Estatutário",
        "situacao": "Em andamento",
        "vagas_numericas_total": 27,
    }


def parse_file(path: str | Path) -> dict[str, Any]:
    return parse(Path(path).read_bytes())
