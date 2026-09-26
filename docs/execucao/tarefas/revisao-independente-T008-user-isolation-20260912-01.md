# Revisão independente T008 — isolamento de usuário

Data: 2026-09-12. Escopo: diff de `mobile/`, evidência de isolamento, filas, migração local e filtros de alerta/favorito.

## Resultado

**DEVOLVIDO — gate de sincronização concorrente/escopo de proprietário.**

Os campos `owner_user_id`, `active_user_id`, limpeza A→B e adoção de linhas legadas estão implementados; o teste A→B passa. `npx tsc --noEmit` passou e `node --test tests/alert-state.test.cjs tests/checkpoint-pending.test.cjs` passou 7/7.

Falha específica: `syncService.ts` obtém a fila filtrada, mas relê e grava `alerts` por `local_id` sem restringir `owner_user_id` (linhas 79–93 e 99–102). `deleteOutboxItem` e `deleteOutboxForEntity` também não verificam proprietário. Se a fila de A já estiver carregada e ocorrer logout/login de B durante a corrida, o item de A pode ser enviado com o token de B e atualizar/remover dados fora do escopo. Cobrir/cancelar essa corrida e filtrar todas as operações por usuário ativo antes do aceite. Build/piloto não foram executados.
