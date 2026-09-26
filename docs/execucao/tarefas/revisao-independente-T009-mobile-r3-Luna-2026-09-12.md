# Parecer independente T009 mobile r3 — Luna — 2026-09-12

**Decisão: DEVOLVE r3.** A r3 atende quase todo o gate: fila persistente contém somente `{id,userId}`, `queuePushRevocation` ocorre antes do fire-and-forget no logout, IDs de outros usuários não são drenados, falhas parciais/restart preservam remanescentes, novo POST fica bloqueado enquanto DELETE same-user não drena, apenas 204/404 são terminais, credencial é capturada antes da limpeza da sessão e o `.catch` evita unhandled rejection. Expo Go, web/simulador, projectId, token sem log, listeners/cleanup e deep-link validado estão cobertos. `expo-notifications` instalado é 0.32.17; `tsc` e suíte completa passaram.

## Achado acionável

O contrato solicitado para remoção é exatamente `DELETE /me/push-tokens/{numeric id}`. O mobile usa `/me/push/devices/{id}`. O backend atualmente mantém esse caminho como alias funcional, mas ele não é o endpoint pedido/canônico do recibo e a suíte valida o alias, ocultando a divergência. Trocar a rota para `/me/push-tokens/${item.id}` e testar o caminho exato; manter ownership via token capturado.

Também não há recuperação de resposta de notificação em cold start (`getLastNotificationResponseAsync`); o listener cobre respostas após montagem do layout. Se deep-link em app encerrado fizer parte do aceite, adicionar esse caso/teste antes de aceitar.

## Verificação

`npx tsc --noEmit` PASS; `node --test tests/*.test.cjs` PASS **38/38**. Sem build, dispositivo/emulador, rede Expo ou piloto.
