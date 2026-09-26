from datetime import datetime, timezone

from app.tenderproof.contracts import Artifact, DiscoveredCandidate, PageText
from app.tenderproof.fields import extract_fields


def artifact(name: str) -> Artifact:
    return Artifact(
        artifact_id=f"art-{name}", sha256="a" * 64, byte_len=10,
        url_requested="https://example.test/doc.pdf", url_final="https://example.test/doc.pdf",
        downloaded_at=datetime.now(timezone.utc),
    )


def test_quadrix_annex_registration_and_exam_rows_are_literal():
    candidate = DiscoveredCandidate(
        candidate_id="quadrix-3057", source="quadrix_open", external_id="3057",
        title_observed="Secretaria Municipal de Educação - Prefeitura Municipal de Cristalina de Goiás",
        detail_url_observed="https://quadrix.org.br/informacoes/3057/",
        observed_at=datetime.now(timezone.utc),
    )
    text = (
        "PREFEITURA MUNICIPAL DE CRISTALINA/GOIÁS\nSECRETARIA MUNICIPAL DE EDUCAÇÃO\n"
        "CONCURSO PÚBLICO EDITAL Nº 1, DE 7 DE JULHO DE 2026\n"
        "Período de solicitação de inscrição, exclusivamente por meio do sistema eletrônico de inscrição\n"
        "07/08 a 10/09/2026\nAplicação das provas objetiva e discursiva\n18/10/2026"
    )
    fields = {f.field_name: f for f in extract_fields(candidate=candidate, artifact=artifact("quadrix"), pages=[PageText(artifact_id="art-quadrix", page_number=40, text=text)])}
    assert fields["inscricao_inicio"].value == "2026-08-07"
    assert fields["inscricao_fim"].value == "2026-09-10"
    assert fields["prova_data"].value == "2026-10-18"


def test_msconcursos_prefers_cris_and_reads_annex_dates():
    candidate = DiscoveredCandidate(
        candidate_id="ms-48", source="msconcursos_open", external_id="48",
        title_observed="Concurso Público - Consórcio Regional Intermunicipal de Saúde (CRIS) - Edital 02/2026",
        detail_url_observed="https://msconcursos.com.br/concurso/48/",
        observed_at=datetime.now(timezone.utc),
    )
    text = (
        "CONSÓRCIO REGIONAL INTERMUNICIPAL DE SAÚDE -CRIS.\n"
        "EDITAL Nº 02/2026 – CONCURSO PÚBLICO.\n"
        "PARA O MUNICÍPIO DE TUPÃ (SP).\n"
        "PERÍODO DE INSCRIÇÕES. 30/04/2026 a 31/05/2026.\n"
        "REALIZAÇÃO DA PROVA OBJETIVA. 14/06/2026."
    )
    fields = {f.field_name: f for f in extract_fields(candidate=candidate, artifact=artifact("ms"), pages=[PageText(artifact_id="art-ms", page_number=12, text=text)])}
    assert fields["orgao"].value == "CONSÓRCIO REGIONAL INTERMUNICIPAL DE SAÚDE - CRIS"
    assert fields["inscricao_inicio"].value == "2026-04-30"
    assert fields["inscricao_fim"].value == "2026-05-31"
    assert fields["prova_data"].value == "2026-06-14"
