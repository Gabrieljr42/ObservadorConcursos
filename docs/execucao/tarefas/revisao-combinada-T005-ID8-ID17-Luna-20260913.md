# Revisão combinada T005 / ID8 / ID17 — Luna

Data: 2026-09-13. Revisão read-only; sem rede, deploy, importação ou mutação.

## Decisão

- **API/backend:** **ACEITA para deploy**, no escopo dos três fluxos revisados.
- **T005 Barra Longa (elo_open/129):** **ACEITA para importação e proposta isoladas**, não para approve/apply. O artefato local tem 429261 bytes e SHA `a5a7ff…ef5a2`; parser fail-closed extrai exatamente 7 cargos e `fields.py` exige `storage_path`, impedindo fallback genérico. Testes direcionados T005 passaram 4/4; receipt/preflight e proposta isolada estão sem mutação.
- **ID8 (idib_open/362):** **DEVOLVIDO para liberação operacional da proposta**. O código atual preserva global=60 e permite somente source+external+SHA+bytes exatos (75 páginas); checks confirmaram 75/60 e rejeição de 74/76, SHA, fonte e bytes divergentes. Contudo, `revisao-independente-ID8-Luna-20260913.json`, preflight e receipt ainda registram o resultado anterior `HTTP 422 page_limit`; falta receipt novo demonstrando `_revalidate → create_proposal` com o run `tp-reviewed-02d010…` e ausência de proposta em falhas.
- **T011/ID17 r8:** **ACEITA para importação e proposta corretivas**, sem novo approve/apply. Envelope/receipt r6, SHA/bytes, 27 requisitos limpos e revisão r8 conferem; revisão pós-apply registra versão 85 idempotente.

## Checks executados

`pytest`: T005+ID8 isolados 7/7; no conjunto publicação/review/import regressivo, 50 passaram e 4 falharam apenas por caminhos relativos de fixtures quando executado da raiz (ao executar do diretório backend, 52 passaram e 2 falharam pelo caminho relativo inverso do fixture ID8); suíte proporcional backend 89 pass, 2 falhas de inventário histórico (`listing_urls_catalogued` 106 vs fixture 103 e SHA de `tenderproof-sources-99.json`). `compileall` passou. Nenhuma rede foi usada.

## Bloqueio preciso

Somente ID8: atualizar/reexecutar evidência operacional do create_proposal com a exceção pinada; não elevar o limite global nem liberar dispatch antes disso. ID17/T005 permanecem separados e não autorizam apply.
