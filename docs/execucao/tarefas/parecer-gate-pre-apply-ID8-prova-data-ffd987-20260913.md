# Gate final pré-apply — ID8 suplemento `prova_data`

Data: 2026-09-13. Revisão read-only; approve/apply não executados.

## Decisão: LIBERA approve + apply exclusivo

A proposta `tpp-ffd987976e8d77b201715ea32de19073` está `proposed`, concurso 8, com baseline versão 87, `baseline_prova_data=null`, `proposed_prova_data=2026-12-06` e `eligible_fields=["prova_data"]`. O gate registra `proposed_cargos_present=false`; portanto não há cargos nem outro campo no payload corretivo.

O vínculo é o suplemento `tp-reviewed-ea4b278d48957c543fed74edd6b8222b`, cuja evidência SHA-bound usa o mesmo PDF ID8 (`fef17aa…116ab28a`, 1.048.994 bytes) e o trecho literal da p.68: `15 Realização das Provas Objetivas 06/12/2026`. O receipt confirmou exatamente um ReviewedField top-level, dry-run/import válidos e `_revalidate → create_proposal` isolado elegível somente para `prova_data`.

Contagens atuais: 92 propostas, 87 versões, 87 outbox, 86 notificações. Não há efeito de versão/outbox/notificação para esta proposta. Libera-se uma única sequência approve+apply, condicionada a CAS de estado, hash e baseline 87, seguida de revisão pós-apply. Não liberar/reaplicar a proposta antiga de `cargos`, nem qualquer outra proposta.

Evidências: `docs/execucao/evidencias/T010/gate-ID8-prova-data-import-proposta-20260913.json` e `docs/execucao/evidencias/T010/T010-id8-prova-data-supplement-receipt.json`.
