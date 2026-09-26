# Revisão independente T008 — estado offline

Teste executado em `mobile`: `node --test tests/checkpoint-pending.test.cjs` — 4/4 passou. Os testes novos cobrem favorito pendente, rollback de escrita, alerta criado/editado e toggle pendente; não cobrem leitura vazia transitória versus exclusão legítima do servidor.

O toggle otimista está correto em `mobile/app/(tabs)/alertas.tsx:51-60,103-106`: atualiza `active` antes da API, reverte no erro e `aria-checked` acompanha o estado. A remoção em Salvos usa `removeFavorite` e atualiza a lista em `salvos.tsx:54-60`.

**Defeito concreto a devolver:** `alertas.tsx:33-37` preserva qualquer lista local quando uma leitura retorna vazia (`data.length===0 && current.length>0`), sem verificar operação pendente, identidade do alerta ou usuário. Assim, uma exclusão legítima no servidor pode deixar alerta fantasma indefinidamente; também pode preservar alerta de usuário anterior. O guard deve consultar apenas operações `alert_create/update` pendentes, por `local_id`/usuário, e permitir que snapshot vazio remova alertas confirmadamente ausentes. O teste deve incluir ambos os casos: alerta sem outbox é removido por snapshot vazio; alerta com outbox pendente permanece.

`database.ts:180-183` bloqueia todo checkpoint com qualquer outbox, preservando ordem e evitando perda, mas é uma barreira global; a correção específica deve manter a operação pendente identificada, sem transformar toda lista vazia em retenção.
