# Evidência T008 — isolamento local por usuário (2026-09-12)

## Reprodução corrigida

Antes da correção, `outbox` e `alerts` não tinham proprietário: uma fila criada offline por A podia ser lida/enviada após logout e login offline de B, e uma leitura vazia podia preservar a linha de A.

Agora o SQLite mantém `metadata.active_user_id` e colunas `owner_user_id` em `alerts`, `favorites` e `outbox`. `setActiveUser` detecta troca de conta, remove somente os dados privados/fila da sessão anterior e vincula as linhas legadas à primeira conta autenticada. Leituras, criação/edição/remoção e `getOutbox` filtram o usuário ativo; o catálogo público permanece.

## Testes

Comandos executados em `mobile/`:

```text
npx tsc --noEmit                         PASS
node --test tests/alert-state.test.cjs tests/checkpoint-pending.test.cjs  PASS (8/8)
```

Os testes criam alerta e fila para A, alternam para B e comprovam que ambos desaparecem; B cria uma linha independente. O teste concorrente simula worker com ID antigo e comprova que `deleteOutboxItem` não remove fila de B. A suíte também cobre leitura vazia legítima, retenção apenas com `alert_create/update`, remoção de favorito, rollback de escrita e estado `active=false` pendente.

`syncService` agora revalida `active_user_id` antes de cada item da fila; se a sessão mudou, aborta sem chamada de API. Leituras/gravações de alertas e exclusões da fila exigem o mesmo owner.

## Reabertura após indisponibilidade da API

A reprodução real mostrou a fila local preservada, mas sem drenagem após a API voltar: a tentativa falha gravava `last_sync_attempt_at`, e `syncIfDue(false)` bloqueava novas tentativas por `SYNC_INTERVAL_MS` (1 hora). Como `navigator.onLine` permaneceu verdadeiro, não houve evento de reconexão.

Correção: inicialização de sessão e retorno ao foreground chamam `syncIfDue(true)`; quando há outbox, tentativas não forçadas usam janela de retry de 60 s. O startup agora é o sinal de transporte recuperado, sem apagar itens locais.

Teste de inicialização (`tests/auth-initialization.test.cjs`) confirma que uma sessão reaberta dispara sync forçado (`true`) e continua recuperável após falha de armazenamento. Resultado: PASS; a suíte owner-scoped permanece 8/8.

## Gate pendente

Não foi reiniciado serviço nem usada sessão compartilhada. O aceite real ainda exige rebuild web/app e nova corrida offline→sync pelo integrador, incluindo servidor/UI e remoção de favorito.
