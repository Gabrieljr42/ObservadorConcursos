# Revisão independente T008 — OPFS/SQLite web r4

Data: 2026-09-12

## Gate código — ACEITA

`mobile/src/db/transaction.ts` usa somente o `db` recebido, serializa `BEGIN IMMEDIATE`/`COMMIT` por fila e tenta rollback sem mascarar o erro primário; a fila é liberada também em falha. `database.ts` mantém um único `dbPromise`; não há `useNewConnection` nem `closeAsync` no caminho de produção. Native continua em `withExclusiveTransactionAsync`. Testes dirigidos T008+push: 24/24; suíte mobile: 41/41; `npx tsc --noEmit`: PASS; `npm run build`: PASS. Ownership/outbox e isolamento T008 permanecem cobertos.

## Gate operacional/deploy — DEVOLVIDO

Não libero deploy para declarar a correção OPFS concluída: nesta sessão não há navegador disponível para reproduzir um lock de AccessHandle realmente externo na origem `127.0.0.1`, observar falha acessível sem limpar OPFS, liberar a outra aba/worker e confirmar retry bem-sucedido. Os testes simulam `database is locked` e provam retry, mas não substituem essa prova pós-correção. Executar smoke em duas abas da mesma origem, fechar a titular, clicar “Tentar novamente”, verificar dados intactos e registrar HTTP/UI/reload; então reavaliar somente este gate.
