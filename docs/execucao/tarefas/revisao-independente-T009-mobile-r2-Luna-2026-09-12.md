# Parecer independente T009 mobile r2 — Luna — 2026-09-12

**Decisão: DEVOLVE r2.** A maior parte da devolução anterior foi corrigida: o POST autenticado exige `userId`/token, valida e armazena `response.data.id` por chave `observador_push_registration_{userId}`; o DELETE usa rota relativa com ID numérico e credencial capturada; logout dispara revogação best-effort com `.catch` antes de limpar sessão, sem bloquear; listeners nativos e cleanup existem; payload de resposta é validado para `/concurso/{id}`; Expo Go retorna `expo_go`; endpoint não é mais configurável; token não é logado. `expo-notifications` instalado: `0.32.17`; plugin Expo 54 e projectId EAS conferidos.

## Pendência que mantém devolução

Se já existe registro local do mesmo usuário e a revogação anterior falha, `registerPushNotifications` chama `revokePushNotifications` mas ignora o resultado e prossegue com novo POST; depois sobrescreve a chave com o novo `id`. O ID antigo fica no servidor sem possibilidade de retry, contrariando “storage/retry same user only”. Deve bloquear o novo registro quando a revogação falhar, ou preservar uma fila/coleção de IDs antigos por usuário para retry autenticado posterior; nunca apagar/ocultar a pendência.

O backend aceita tanto `/me/push/devices/{id}` quanto o alias `/me/push-tokens/{id}`; o mobile usa a rota pública canônica documentada (`/me/push/devices/{id}`), portanto o contrato numérico está correto, mas o recibo deve registrar explicitamente essa equivalência.

## Verificação

`npx tsc --noEmit` PASS. `node --test tests/*.test.cjs` PASS **36/36**. Cobertura inclui ID/DELETE, ownership de user, retry direto, listeners/cleanup, rota malformada, Expo Go e ausência de token. Não houve build, dispositivo/emulador, rede Expo ou piloto.
