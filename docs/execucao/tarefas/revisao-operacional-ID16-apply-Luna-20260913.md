# Revisão operacional pré-apply — ID16

Data: 2026-09-13. Read-only; nenhum piloto foi operado.

## Veredito: ACCEPT_OPERATION_ID16_APPLY

Liberar uma única sequência approve → apply → replay idempotente exclusivamente para:

- proposta `tpp-1a0fc40cc8df713e6958de0f43efc032`;
- hash `ecfc21e9b02707be162761e86ab7f149dd1a011e7d038e37d8f4c8572d2aaee1`;
- owner `1`, estado `proposed`, concurso `16`, run `tp-reviewed-01c65a37fe15ca4b54898d7e0774a7f7`;
- campos exatos `cargos` e `prova_data` (18 cargos: 10 imediatos + 8 CR; prova `2025-01-12`). Identidade e inscrições permanecem inalteradas.

O gate corrigido registra baseline 90 versões/90 outbox/89 notificações/162 cargos/95 propostas após a criação da proposta, com a revisão documental no-op previamente aprovada e `pending_after=false`. O resultado esperado da aplicação é versão 91, outbox 91, notificação 90 e 180 cargos; replay não cria novos efeitos nem envia push. `tpp-bdb86b21341b923ed50b5346fcc3ddb6` permanece **NEVER_APPROVE/NEVER_APPLY**.

Checks read-only: gate `gate-ID16-corrected-01c65-proposal-20260913.json`; 5 testes direcionados de apply/replay/rollback/concurrency passaram. Não aprovar outros campos/propostas e abortar se hash, estado, baseline ou contagens diferirem.
