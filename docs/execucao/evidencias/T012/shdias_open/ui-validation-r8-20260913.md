# SHDias / concurso 34 — validação UI R8

**Resultado:** `SHDIAS_UI_R8_ACCEPTED`.

Smoke real read-only executado via Playwright Python + Chromium já instalado, com login local e sem clicar ações mutantes.

- `/inicio`: build exibiu 34 concursos e o registro `CONCURSO PÚBLICO CPMH 001/2026 - Guarda`, Município de Hortolândia e SHDias.
- `/concurso/34`: resumo exibiu taxa `R$ 63,25`; cargos `301` e `302`; 12 e 28 vagas; remuneração `R$ 3.971,37`; prova `27/09/2026`; sem `undefined`.
- Após reload, taxa, códigos, vagas e ausência de `undefined` permaneceram. O texto integral variou apenas em conteúdo dinâmico, não nos campos validados.
- `/salvos`: `0 itens salvos`.
- `/notificacoes`: alerta original do piloto e novo concurso visíveis.
- Checkpoint observado pela UI: HTTP 200 e 34 concursos; contagens de fontes/seleções não foram expostas pela resposta.

Evidências: `ui-validation-r8-20260913.json`, `ui-validation-r8-inicio.png` e `ui-validation-r8-detail34.png` nesta pasta.
