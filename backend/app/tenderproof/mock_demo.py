"""TenderProof — fixtures sintéticas do modo ``mock`` (demonstração offline).

Todo material aqui é SINTÉTICO e marcado como tal (``is_synthetic_sample``).
Nunca apresentar como observação oficial.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.tenderproof.demo_pdf import make_text_pdf
from app.tenderproof.solari_adapter import DownloadedBytes, FakeSolariDriver, ObservedJson

LISTING_HTML = """<html><body>
<h1>Inscricoes abertas</h1>
<a href="/concurso.jsp?cod=42">Concurso Prefeitura Municipal de Exemplo MG cod 42</a>
<a href="/concurso.jsp?cod=77">Processo Seletivo Saude Exemplo cod 77</a>
</body></html>"""

DETAIL_HTML_42 = """<html><body>
<h1>Concurso Prefeitura Municipal de Exemplo MG cod 42</h1>
<p>concurso.jsp?cod=42 — Edital n. 01/2026</p>
<a href="https://novo.ibgpconcursos.com.br/rest/concurso/download/edital/42/?file=site/anexos/42/edital_01_2026.pdf">Edital n. 01/2026 Prefeitura Municipal de Exemplo</a>
<a href="https://novo.ibgpconcursos.com.br/rest/concurso/download/edital/43/?file=site/anexos/42/gabarito_prova.pdf">Gabarito oficial da prova objetiva</a>
<a href="https://novo.ibgpconcursos.com.br/rest/concurso/download/edital/44/?file=site/anexos/42/comunicado_01.pdf">Comunicado 01</a>
</body></html>"""

EDITAL_URL_42 = (
    "https://novo.ibgpconcursos.com.br/rest/concurso/download/edital/42/"
    "?file=site/anexos/42/edital_01_2026.pdf"
)

PDF_PAGE_1 = (
    "PREFEITURA MUNICIPAL DE EXEMPLO\n"
    "Concurso Publico Prefeitura Municipal de Exemplo MG\n"
    "Edital n. 01/2026 de abertura de concurso publico\n"
    "As inscricoes estarao abertas de 10/03/2026 a 20/04/2026 pelo site da banca.\n"
    "Cargo de Agente Administrativo com vencimento de R$ 3.500,00 mensais.\n"
    "concurso.jsp?cod=42"
)

MOCK_BASELINE = {
    "titulo": "Concurso Prefeitura Municipal de Exemplo MG cod 42",
    "orgao": "Prefeitura Municipal De Exemplo",
    "edital_numero": "01/2026",
    "inscricao_inicio": "2026-03-10",
    # Baseline propositalmente desatualizada em 1 dia para demonstrar DIVERGE
    # entre observações de momentos distintos (não é erro automático do crawler).
    "inscricao_fim": "2026-04-19",
    "salario_min": "3500.00",
    "salario_max": "3500.00",
}
MOCK_BASELINE_COLLECTED_AT = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
MOCK_BASELINE_ORIGIN = "mock: snapshot sintético prévio (demonstração offline)"


def build_mock_driver() -> FakeSolariDriver:
    pdf_bytes = make_text_pdf([PDF_PAGE_1])
    return FakeSolariDriver(
        listing_html=LISTING_HTML,
        detail_html=DETAIL_HTML_42,
        observed=[
            ObservedJson(
                url="https://novo.ibgpconcursos.com.br/rest/concurso/42",
                status=200,
                json_path="meta.nome",
                payload={"meta": {"nome": "Concurso Prefeitura Municipal de Exemplo MG cod 42"}},
            )
        ],
        downloads={
            EDITAL_URL_42: DownloadedBytes(
                url_requested=EDITAL_URL_42,
                url_final=EDITAL_URL_42,
                content=pdf_bytes,
                content_type="application/pdf",
                redirect_chain=[EDITAL_URL_42],
            )
        },
        session_id="mock-session-001",
        replay_url="https://replay.example/mock-session-001",
    )
