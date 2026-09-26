# SHDias / concurso 34 — validação UI R7

**Resultado:** `PARTIAL_UI` — defeito preciso: taxa de inscrição não aparece na UI como `R$ 63,25`; o detalhe mostra `Taxa de inscrição: valor ainda não confirmado`, embora o histórico registre `63.25`.

Validação real read-only via Playwright Python + Chromium instalado, com login local e sem clicar ações mutantes:

- `/inicio`: 34 concursos; exibe `CONCURSO PÚBLICO CPMH 001/2026 - Guarda`, Município de Hortolândia e SHDias.
- `/concurso/34`: códigos 301 e 302; 12 e 28 vagas imediatas; remuneração `R$ 3.971,37`; prova `27/09/2026`; sem `undefined`.
- Reabertura/reload preservou os campos observados, mas o texto integral variou em conteúdo dinâmico; não foi declarado “estável” byte a byte.
- `/salvos`: `0 itens salvos`.
- `/notificacoes`: alerta original do piloto e novo concurso visíveis.
- Checkpoint UI-observado: HTTP 200, 34 concursos; resposta não expôs contagens de fontes/seleções.

Screenshots: `ui-validation-r7-inicio.png` e `ui-validation-r7-detail34.png`. JSON sanitizado: `ui-validation-r7-20260913.json`.
