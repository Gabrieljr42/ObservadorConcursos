from unittest.mock import MagicMock

from app.connectors.dedicated.fatec import FATECSelectionConnector


def test_fatec_table_emits_only_active_personnel_rows():
    html = """
    <table>
      <tr><th>DATA</th><th>NUMERO</th><th>PERÍODO</th><th>DESCRICAO</th><th>ARQUIVOS</th></tr>
      <tr><td>09/07/2026 (EM ANDAMENTO)</td><td>2026/3010088-01</td>
          <td>10/07/2026 a 24/07/2026</td><td>CONTRATAÇÃO CLT: ANALISTA DE PROJETOS</td>
          <td><a href="/docs/edital-1.pdf">EDITAL</a><a href="/docs/resultado.pdf">RESULTADO</a></td></tr>
      <tr><td>31/03/2026 (EM ANDAMENTO)</td><td>2026/5030061-01</td>
          <td>28/04/2026 a 06/05/2026</td><td>SELEÇÃO DE AUXILIAR FINANCEIRO</td>
          <td><a href="/docs/edital-2.pdf">EDITAL</a></td></tr>
      <tr><td>28/01/2025 (ENCERRADO)</td><td>2025/1</td><td>01/02/2025 a 02/02/2025</td>
          <td>PROCESSO SELETIVO PARA CONTRATAÇÃO DE ASSISTENTE</td><td><a href="/old.pdf">EDITAL</a></td></tr>
    </table>
    """
    connector = FATECSelectionConnector()
    connector._fetch_html = MagicMock(return_value=html)

    result = connector.crawl_with_diagnostics()

    assert result.run_data.candidates_found == 2
    assert result.run_data.candidates_rejected == 0
    assert len(result.items) == 2
    assert result.items[0]['external_id'] == '2026-3010088-01'
    assert result.items[0]['link_edital'].endswith('/docs/edital-1.pdf')
    assert len(result.items[0]['raw_data']['publications']) == 2
