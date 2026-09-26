# SHDias / concurso 34 — validação UI headless R6

**Resultado:** `PARTIAL_UI` (não aceito como confirmação integral dos campos esperados).

Execução real read-only em Playwright Python + Chromium já instalado, contra `http://localhost:13000`, usando login local sem registrar credencial. Nenhum botão mutante foi clicado.

Confirmado na listagem `/inicio`:

- 34 concursos listados;
- `CONCURSO PÚBLICO CPMH 001/2026 - Guarda`;
- `Município de Hortolândia`;
- `SHDias Consultoria e Concursos`.

No detalhe `/concurso/34`, confirmado: SHDias, Município de Hortolândia, edital `001/2026`, prova `27/09/2026`, remuneração `R$ 3.971,37`, e dois cargos femininos/masculinos. A UI **não** exibiu códigos 301/302, vagas 12/28, nem taxa `63,25`: mostrou vagas e taxa “ainda não confirmadas”. Também exibiu `Requisitos: undefined`.

`/salvos` mostrou `0 itens salvos`. `/notificacoes` mostrou o alerta ativo do piloto e o novo concurso. O checkpoint UI-observado retornou HTTP 200 e 34 concursos; não expôs contagem de fontes/seleções (campos ausentes/zero), portanto não confirma 33 fontes/34 seleções.

Screenshots e JSON sanitizado: `ui-validation-r6-inicio.png`, `ui-validation-r6-detail34.png`, `ui-validation-r6-20260913.json`.
