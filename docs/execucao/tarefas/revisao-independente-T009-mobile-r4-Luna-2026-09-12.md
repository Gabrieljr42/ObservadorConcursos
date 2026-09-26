# Parecer independente T009 mobile r4 — Luna — 2026-09-12

**Decisão: ACEITA r4 (escopo mobile interno).**

Verificações:

- Revogação usa exatamente `DELETE /me/push-tokens/{numericId}`; registro usa `POST /me/push-tokens` e guarda `{id,userId}` por conta.
- Fila persistente mantém somente `{id,userId}`, deduplica por par, preserva IDs remanescentes em falha parcial, reinício e relogin, e drena apenas a conta autenticada. Novo POST é bloqueado enquanto qualquer DELETE same-user não for terminal.
- Apenas HTTP 204 e 404 removem itens; outros status/erro permanecem na fila. Logout enfileira antes do fire-and-forget, captura token/usuário antes de limpar sessão e trata rejeição.
- `getLastNotificationResponseAsync` reutiliza a validação estrita da rota; listener e cold-start compartilham chave de deduplicação sem suprimir payloads distintos. Cleanup remove ambos os listeners.
- Casos válido, inválido, duplicado, cleanup, Expo Go, ownership, restart/relogin e falha parcial estão nos testes; nenhum token é logado.

`node_modules/expo-notifications` é 0.32.17 e o plugin Expo 54/projectId estão configurados. `npx tsc --noEmit` PASS; `node --test tests/*.test.cjs` PASS **39/39**. Não houve build, dispositivo/emulador, rede Expo ou piloto. Aceite final de uso real ainda requer development build/dispositivo, fora deste gate de código.
