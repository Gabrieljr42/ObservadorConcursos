from datetime import datetime, timezone

from app.tenderproof.contracts import Artifact, DiscoveredCandidate, PageText
from app.tenderproof.fields import _extract_orgao


def test_contemax_orgao_drops_normative_tail_but_preserves_evidence():
    candidate = DiscoveredCandidate(
        candidate_id="contemax-cubati",
        source="contemax_open",
        external_id="concursos-em-andamento/prefeitura-municipal-de-cubati-pb",
        title_observed="PREFEITURA MUNICIPAL DE CUBATI-PB",
        detail_url_observed="https://www.contemaxconsultoria.com.br/site/wp-content/uploads/2024/09/Edital-CUBATI.pdf",
        observed_at=datetime.now(timezone.utc),
    )
    artifact = Artifact(
        artifact_id="art-contemax-cubati-test",
        sha256="a" * 64,
        byte_len=10,
        url_requested="https://www.contemaxconsultoria.com.br/site/wp-content/uploads/2024/09/Edital-CUBATI.pdf",
        url_final="https://www.contemaxconsultoria.com.br/site/wp-content/uploads/2024/09/Edital-CUBATI.pdf",
        downloaded_at=datetime.now(timezone.utc),
    )
    text = (
        "Concurso Público n.º 001/2024\n"
        "REGULAMENTA O CONCURSO PÚBLICO PARA PROVIMENTO DE CARGOS DO QUADRO "
        "PERMANENTE DE PESSOAL DA PREFEITURA MUNICIPAL DE CUBATI E ADOTA OUTRAS "
        "PROVIDÊNCIAS.\n"
    )
    field = _extract_orgao(
        candidate,
        artifact,
        [PageText(artifact_id=artifact.artifact_id, page_number=2, text=text)],
    )
    assert field.state.value == "supported"
    assert field.value == "Prefeitura Municipal De Cubati"
    assert field.evidence and "E ADOTA OUTRAS PROVIDÊNCIAS" in field.evidence[0].snippet
