# Validação UI CPCON 35 — R13 (2026-09-13)

**Resultado: PASS_UI_SYNC** (Playwright + Chromium headless, somente leitura; `mutations=false`).

## Escopo e evidência

- Build implantado em `http://localhost:13000`; duas sessões autenticadas independentes.
- `/inicio` e `/busca` exibiram `PROCESSO SELETIVO SIMPLIFICADO Nº 002/2026`, Universidade Estadual da Paraíba e CPCon / UEPB Concursos; `/busca` mostrou 35 seleções.
- `/concurso/35` abriu após navegação direta, hard reload e nova sessão com conteúdo estável.
- Identidade visível: título, órgão, edital `002/2026`; banca CPCon / UEPB Concursos.
- Exatamente seis cargos canônicos, todos visíveis com vaga e `R$ 3.768,36`: Técnico em Laboratório (Esterilização) 1; Microbiologia de Alimentos 1; Eletrotécnica 2; Química 1; Química e Fertilidade do Solo 1; Histopatologia Oral 1.
- Cronograma coerente com campos ausentes no envelope: inscrições “Data não informada” e prova “Pendente de conferência”; nenhuma data inventada.
- Sem `undefined`, `NaN` ou HTML bruto; reload e segunda sessão mantiveram os mesmos dados.
- `/salvos`: `0 itens salvos`; `/notificacoes`: alerta original visível e notificação do novo CPCON; nenhum controle mutante acionado.
- Checkpoint observado via fluxo de login: HTTP 200, `concursos=35` em quatro respostas; receipt R13 confirma version 93/outbox 93/notifications 92/favorites 0/alerts 1 e `cargo_count=6`.

## Nota de roteamento

`/listagem` isolada retornou 404 (rota não exposta pelo build); a listagem funcional é `/inicio`/`/busca`, que foram validadas. Isso não foi tratado como falha de dados/UI.

## Artefatos

- JSON sanitizado: `ui-validation-r13-20260913.json`
- Script de reprodução: `ui-validation-r13-headless.py`
- Capturas: `ui-validation-r13-inicio.png`, `ui-validation-r13-busca.png`, `ui-validation-r13-detail35.png`, `ui-validation-r13-salvos.png`, `ui-validation-r13-notificacoes.png`
- Fonte esperada: `live-envelope-ready-r9.json`; aplicação: `live-apply-receipt-r13-20260913.json`.
