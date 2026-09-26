from datetime import datetime, timezone

from app.tenderproof.contracts import Artifact, FieldState, PageText
from app.tenderproof.fields import _evidence
from app.tenderproof.ibam_caruaru_jobs import (
    EXPECTED_ANNEX_ARTIFACT_SHA256,
    extract_caruaru_jobs,
)


TABLE = """PREFEITURA MUNICIPAL DE CARUARU - PE
CONCURSO PÚBLICO - EDITAL No 01/2026
ANEXO I
CARGOS, VAGAS, REQUISITOS, JORNADA DE TRABALHO, VENCIMENTOS E ATRIBUIÇÕES TÍPICAS
TOTAL DE VAGAS AC PcD PPP CH VENCIMENTO
001 Auditor Fiscal Municipal Graduação de Nível Superior em qualquer área 10 07 01 02 40h R$ 6.000,00
002 Analista Fiscal Municipal – Tecnologia da Informação Diploma de Bacharel ou Tecnólogo em Ciência da Computação 02 01 01 40h R$ 2.500,00
003 Analista Fiscal Municipal – Engenharia Civil Diploma de Bacharel em Engenharia Civil 02 01 01 40h R$ 2.500,00
004 Analista Fiscal Municipal – Contabilidade Diploma de Bacharel em Contabilidade 02 01 01 40h R$ 2.500,00
005 Analista Fiscal Municipal – Direito Diploma de Bacharel em Direito 02 01 01 40h R$ 2.500,00
006 Analista Fiscal Municipal – Área Geral de Ensino Superior Diploma de conclusão de Curso Superior de Graduação 02 01 01 40h R$ 2.500,00"""


def _artifact(sha=EXPECTED_ANNEX_ARTIFACT_SHA256):
    return Artifact(
        artifact_id="art-ibam-caruaru-edital-test",
        sha256=sha,
        byte_len=123,
        url_requested="https://www.ibam-concursos.org.br/documento/ed-pmc0126f.pdf",
        url_final="https://www.ibam-concursos.org.br/documento/ed-pmc0126f.pdf",
        content_type="application/pdf",
        downloaded_at=datetime.now(timezone.utc),
    )


def test_caruaru_rows_keep_total_and_quotas_without_general_cr():
    artifact = _artifact()
    pages = [
        PageText(artifact_id=artifact.artifact_id, page_number=1, text=TABLE),
        PageText(
            artifact_id=artifact.artifact_id,
            page_number=8,
            text="5.1.1. Será cobrado a título de inscrição o valor de R$ 97,00.",
        ),
    ]
    field = extract_caruaru_jobs(
        artifact,
        pages,
        _evidence,
        source="ibam_open",
        external_id="364",
    )

    assert field is not None and field.state == FieldState.SUPPORTED
    assert len(field.value) == 6
    auditor = field.value[0]
    assert auditor["vagas_imediatas"] == 10
    assert auditor["vagas_ampla_concorrencia"] == 7
    assert auditor["vagas_pcd"] == 1
    assert auditor["vagas_ppp"] == 2
    assert auditor["cadastro_reserva"] is None
    assert "não confirmado" in auditor["cadastro_reserva_observacao"]
    assert auditor["remuneracao"] == "6000.00"
    assert "gratificações" in auditor["remuneracao_observacao"]
    assert auditor["prova_inicio"] == "09:10"
    assert field.value[-1]["prova_inicio"] == "16:10"
    assert all(job["taxa_inscricao"] == "97.00" for job in field.value)
    assert all(item.document_sha256 == EXPECTED_ANNEX_ARTIFACT_SHA256 for item in field.evidence)


def test_opening_edital_reference_does_not_fabricate_cargo_table():
    artifact = _artifact()
    page = PageText(
        artifact_id=artifact.artifact_id,
        page_number=1,
        text="Os cargos, vagas, requisitos, jornada e vencimentos constam do Anexo I.",
    )
    field = extract_caruaru_jobs(
        artifact,
        [page],
        _evidence,
        source="ibam_open",
        external_id="364",
    )

    assert field is not None and field.state == FieldState.FAILED
    assert "Anexo I" in field.reason


def test_same_named_document_with_different_hash_is_unsupported():
    artifact = _artifact("0" * 64)
    assert extract_caruaru_jobs(
        artifact,
        [],
        _evidence,
        source="ibam_open",
        external_id="364",
    ) is None
