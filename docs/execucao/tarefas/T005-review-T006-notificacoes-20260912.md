# Revisão independente T006 — notificações push

Resultado: a afirmação de que não há push nativo é correta e indica trabalho interno pendente, não bloqueio de ambiente.

- `mobile/package.json` não possui `expo-notifications`; `mobile/app.json`/`mobile/app.config.js` não declaram plugin, ícones/canais ou configuração de notificações; `mobile/eas.json` só configura distribuição/API.
- `mobile/src/api/notifications.ts:1-4` acessa apenas `localNotifications` (SQLite). `mobile/src/db/database.ts:79-83,262-272` cria/preenche a tabela local; `mobile/src/db/repositories.ts:139-171` lê e marca localmente, enfileirando sync.
- `mobile/src/sync/syncService.ts:68-72` usa somente `/me/notifications/{id}/read` e `/me/notifications/read-all`. Não há registro de token ou dispositivo.
- Backend `main.py:1017-1094` expõe leitura/marcação de notificações internas e `main.py:1097-1104` roda alertas; `models.py:259-277` tem `Notification`, sem Device/PushToken. `notification_tasks.py:1-48` entrega notificações internas e `publication.py:690-710` declara que não faz email/push/network.

Já funciona/testável: alertas e notificações internas persistem no backend, sincronizam para SQLite e a tela `mobile/app/notificacoes.tsx` lista/marca itens. Exigir push real requer implementação interna de dependência (`expo-notifications`, token/device model e endpoints de registro/envio), além de credenciais/configuração EAS/APNs/FCM por ambiente. Não há evidência de que credenciais externas ausentes sejam a causa atual; nenhum acesso foi feito.
