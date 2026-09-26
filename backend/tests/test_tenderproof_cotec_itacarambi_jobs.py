from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.tenderproof.contracts import (
    Artifact,
    DiscoveredCandidate,
    DocumentCandidate,
    FieldState,
    PageText,
    SupplementaryDocument,
)
from app.tenderproof.cotec_itacarambi_jobs import (
    EXPECTED_ARTIFACT_SHA256,
    extract_itacarambi_jobs,
    extract_itacarambi_jobs_v2,
)
from app.tenderproof.fields import _evidence
from app.tenderproof import supplementary_fields


TABLE = """CÂMARA MUNICIPAL DE ITACARAMBI - MG
EDITAL 01/2026
ANEXO I - ESPECIFICAÇÃO DOS CARGOS
CÓD.
01 Agente Administrativo 01 01 CR Ensino Médio Completo e conhecimentos básicos de informática. 30 horas semanais R$ 1.621,00 R$ 75,00
02 Auxiliar de Serviços Gerais** CR CR CR Ensino Fundamental Completo 30 horas semanais R$ 1.621,00 R$ 65,00
03 Controlador Interno 01 01 CR Ensino Superior Completo em Administração, Ciências Contábeis, Economia ou Direito. 30 horas semanais R$ 3.737,48 R$ 95,00
04 Motorista** CR CR CR Ensino Médio Completo e CNH na categoria “D”. 30 horas semanais R$ 1.965,45 R$ 75,00
05 Técnico Legislativo 01 01 CR Ensino Médio Completo e conhecimentos básicos de informática. 30 horas semanais R$ 3.203,55 R$ 75,00
06 Telefonista/Recepcionista 01 01 CR Ensino Médio Completo e conhecimentos básicos de informática. 30 horas semanais R$ 1.621,00 R$ 75,00
07 Vigia 01 01 CR Ensino Fundamental Completo Escala de 12h x 36h R$ 1.621,00 R$ 65,00
CR – Cadastro de Reserva."""


def _artifact(sha=EXPECTED_ARTIFACT_SHA256):
    return Artifact(
        artifact_id="art-cotec-itacarambi-anexo1-test",
        sha256=sha,
        byte_len=101882,
        url_requested="https://anexos-r2.selecao.net.br/uploads/846/concursos/32/anexos/26f6b740-d572-4213-b269-7d88674780b9.pdf",
        url_final="https://anexos-r2.selecao.net.br/uploads/846/concursos/32/anexos/26f6b740-d572-4213-b269-7d88674780b9.pdf",
        content_type="application/pdf",
        downloaded_at=datetime.now(timezone.utc),
    )


def test_itacarambi_table_transcription_keeps_cr_and_values_by_role():
    artifact = _artifact()
    page = PageText(artifact_id=artifact.artifact_id, page_number=1, text=TABLE)
    field = extract_itacarambi_jobs(artifact, [page], _evidence, source="cotec_open", external_id="32")

    assert field is not None and field.state == FieldState.SUPPORTED
    assert len(field.value) == 7
    assert field.value[0]["nome"] == "Agente Administrativo"
    assert field.value[0]["vagas_imediatas"] == 1
    assert field.value[0]["cadastro_reserva"] is True
    assert field.value[0]["remuneracao"] == "1621.00"
    assert field.value[1]["vagas_imediatas"] == 0
    assert field.value[1]["cadastro_reserva"] is True
    assert field.value[2]["remuneracao"] == "3737.48"
    assert field.value[6]["jornada"] == "Escala de 12h x 36h"
    assert all(item.document_sha256 == EXPECTED_ARTIFACT_SHA256 for item in field.evidence)
    assert all(item.page_number == 1 and item.snippet in TABLE for item in field.evidence)


def test_same_named_table_with_different_bytes_is_unsupported():
    artifact = _artifact("0" * 64)
    page = PageText(artifact_id=artifact.artifact_id, page_number=1, text=TABLE)

    assert extract_itacarambi_jobs(artifact, [page], _evidence, source="cotec_open", external_id="32") is None


def test_v2_separates_pcD_reserve_from_general_cr():
    artifact = _artifact()
    page = PageText(artifact_id=artifact.artifact_id, page_number=1, text=TABLE)
    field = extract_itacarambi_jobs_v2(artifact, [page], _evidence, source="cotec_open", external_id="32")

    assert field is not None and field.state == FieldState.SUPPORTED
    assert field.value[0]["cadastro_reserva"] is False
    assert field.value[0]["vagas_pcd_reserva"] == "CR"
    assert "PcD" in field.value[0]["cadastro_reserva_observacao"]
    assert field.value[1]["cadastro_reserva"] is True
    assert "geral" in field.value[1]["cadastro_reserva_observacao"]


def _supplement(reason):
    artifact = _artifact()
    document = DocumentCandidate(
        doc_id="itacarambi-anexo",
        title="ANEXO I - ESPECIFICAÇÃO DOS CARGOS",
        url_requested=artifact.url_requested,
        url_final=artifact.url_final,
        kind="anexo",
        reason_chosen=reason,
    )
    return SupplementaryDocument(document=document, artifact=artifact)


def _candidate():
    return DiscoveredCandidate(
        candidate_id="cotec_open-32",
        title_observed="Câmara Municipal de Itacarambi/MG",
        detail_url_observed="https://www.cotec.fadenor.com.br/informacoes/32/",
        external_id="32",
        source="cotec_open",
        observed_at=datetime.now(timezone.utc),
    )


class _CotecAdapter:
    def validate_document_url(self, url, candidate):
        assert url == _artifact().url_final


class _Store:
    def load_artifact_bytes(self, artifact):
        return b"x" * 101882


def test_v1_supplement_is_blocked_as_superseded_interpretation(monkeypatch):
    monkeypatch.setattr(supplementary_fields, "get_source_adapter", lambda source: _CotecAdapter())
    settings = SimpleNamespace(limits=SimpleNamespace(max_download_bytes=1_000_000, max_pages=10))

    with pytest.raises(HTTPException) as exc:
        supplementary_fields.supplement_fields(
            _candidate(), [], [_supplement("Documento suplementar observado no detalhe COTEC/32")],
            _Store(), settings, 1,
        )

    assert exc.value.status_code == 422
    assert exc.value.detail == "superseded_document_interpretation"


def test_v2_supplement_reproduces_jobs(monkeypatch):
    monkeypatch.setattr(supplementary_fields, "get_source_adapter", lambda source: _CotecAdapter())
    class _Digest:
        def hexdigest(self):
            return EXPECTED_ARTIFACT_SHA256
    monkeypatch.setattr(supplementary_fields.hashlib, "sha256", lambda content: _Digest())
    monkeypatch.setattr(
        supplementary_fields,
        "extract_pages_isolated",
        lambda *args, **kwargs: ([PageText(artifact_id=_artifact().artifact_id, page_number=1, text=TABLE)], 1, 1, False, []),
    )
    settings = SimpleNamespace(limits=SimpleNamespace(max_download_bytes=1_000_000, max_pages=10))

    result = supplementary_fields.supplement_fields(
        _candidate(), [], [_supplement("v2: Anexo com escopo PcD separado")], _Store(), settings, 1,
    )

    cargo = next(item for item in result if item.field_name == "cargos")
    assert cargo.state == FieldState.SUPPORTED
    assert cargo.value[0]["cadastro_reserva"] is False
    assert cargo.value[0]["vagas_pcd_reserva"] == "CR"
