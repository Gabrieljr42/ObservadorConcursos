# T008 — OPFS web: conexão única e retry

## Reprodução mínima (antes)

- Em `http://127.0.0.1:13000/notificacoes`, a primeira carga após fechar/reabrir e a abertura concorrente em duas abas puderam exibir `Dados salvos indisponíveis`.
- O diagnóstico do build aceito registrou falha de `AccessHandle` OPFS em `127.0.0.1`, enquanto `http://localhost:13000/notificacoes` abriu os mesmos dados; são origens diferentes e o storage não deve ser limpo.
- O caminho web de `withLocalTransaction` abria `observador.db` com `useNewConnection: true`, deixando a conexão principal e a auxiliar disputarem o handle por origem.

## Correção limitada

- `mobile/src/db/transaction.ts` não abre nem fecha conexão auxiliar no web: reutiliza o `db` singleton de `database.ts`.
- Transações web explícitas são serializadas por uma fila por módulo; `BEGIN IMMEDIATE`, `COMMIT` e rollback preservam o erro original quando o handle externo ainda está ocupado.
- Native continua usando `withExclusiveTransactionAsync`; nenhuma migração, dado OPFS/IndexedDB ou API foi removida.
- O retry de UI permanece seguro: a inicialização falha de forma acessível quando o lock é externo e `Tentar novamente` recarrega/reabre a origem; após liberar o handle, a nova conexão singleton pode prosseguir.

## Evidência automatizada

- `mobile/tests/local-transaction.test.cjs`: conexão única, rollback sem `close`, concorrência serializada, erro real de lock seguido de retry, e regressão native.
- `node --test tests/*.test.cjs`: 41/41 passando (inclui T008 ownership/outbox e T009 push).
- `npx tsc --noEmit`: passou.
- `npm run build`: export web passou; bundles gerados em `mobile/dist`.

## Depois / revisão

O cenário de duas abas agora não cria conexão interna concorrente. Um lock realmente externo continua aparecendo como erro recuperável, sem exclusão de dados; fechar a outra aba/worker da mesma origem e usar `Tentar novamente` é o passo de recuperação. Solicita-se revisão independente antes de qualquer publicação.
