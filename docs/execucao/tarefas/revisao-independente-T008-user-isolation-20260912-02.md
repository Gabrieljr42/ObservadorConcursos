# Revisão independente T008 — rechecagem de isolamento

Data: 2026-09-12. **ACEITO — gate de código/testes de isolamento local.**

`syncService` compara `item.owner_user_id` com `active_user_id` antes de cada item e aborta antes da API quando a sessão mudou. Leituras/gravações de `alerts` e `deleteOutboxItem`/`deleteOutboxForEntity` estão owner-scoped; a fila antiga não remove a fila de B. A criação offline preserva `active=false`, e a troca A→B limpa dados privados sem apagar o catálogo público.

Verificação independente: `npx tsc --noEmit` PASS; `node --test tests/alert-state.test.cjs tests/checkpoint-pending.test.cjs` PASS (8/8), incluindo o caso de worker com ID antigo. Não mutuei executor, build, piloto ou navegador.

**Gate operacional ainda pendente:** rebuild e corrida implantada offline→sync para confirmar servidor/UI e remoção/reabertura de favorito; este aceite não declara aceite real do piloto.
