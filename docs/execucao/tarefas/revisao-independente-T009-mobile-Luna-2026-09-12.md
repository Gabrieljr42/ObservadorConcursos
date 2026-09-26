# Parecer independente T009 mobile — Luna — 2026-09-12

**Decisão: DEVOLVE.** A dependência está instalada de fato: `node_modules/expo-notifications/package.json` é `0.32.17`, compatível com Expo SDK 54; `package.json`/lock e `app.config.js` declaram o plugin. O fluxo de registro é opt-in na tela Notificações, exige sessão autenticada via `apiClient`, verifica Android/iOS físico, permissão, `projectId` (EAS `a175e274-ccca-4052-a33f-3f653887dc67`), usa `Crypto.randomUUID`, não registra token em log e cobre web/simulador/denied/missing-config.

## Bloqueios de contrato/aceite

1. **Revogação incompatível:** o backend real retorna metadata com `id` numérico no `POST /me/push-tokens` e exige `DELETE /me/push-tokens/{device_id}` (esse parâmetro é o ID numérico da entidade). `pushRegistration.ts` descarta `response.data.id`, armazena só o UUID local e chama `DELETE /me/push-tokens` com body `{device_id}`. Logout portanto recebe 404/405 e não revoga o dispositivo.
2. **Logout bloqueante:** `AuthProvider.logout` faz `await revokePushNotifications()` antes de fechar sessão/token; a API tem timeout de 10 s. “Best effort sem bloquear” não está satisfeito. O `finally` apaga o registro local mesmo em falha, portanto não há retry autenticado posterior.
3. **Resposta/deep link ausentes:** não há `addNotificationReceivedListener`/`addNotificationResponseReceivedListener`, tratamento de payload ou roteamento para `/concurso/{id}`. Push recebido/tocado não atualiza a tela nem navega.
4. `endpoint` permanece livremente configurável, inclusive URL absoluta, e não há teste de ownership/relogin contra resposta `{id}`. O registro sem token em log e o isolamento do POST via autenticação estão adequados.

## Verificação

`npx tsc --noEmit` passou. `node --test tests/*.test.cjs` passou **33/33**, mas os testes atuais modelam o DELETE antigo e não detectam o ID numérico, logout não bloqueante ou listeners/deep-link. Não houve build, rede Expo, dispositivo/emulador ou piloto nesta revisão.

**Retorno exigido:** armazenar `response.data.id`, revogar na rota numérica com ownership, tornar logout best-effort não bloqueante (preservando retry), implementar/testar listeners e deep-link, restringir endpoint a caminho relativo/allowlist e atualizar recibo/testes.
