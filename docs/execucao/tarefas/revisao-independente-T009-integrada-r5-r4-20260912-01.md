# Revisão independente integrada T009 — backend r5 + mobile r4

Status: DEVOLVIDA para correção de migração PostgreSQL (código SQLite/mobile aprovado condicionalmente).

## Evidência

- Backend: `pytest -q tests/test_t009_push.py tests/test_idempotency.py tests/test_offline_sync_auth.py` → 15 PASS, 1 skip (PostgreSQL). Outbox tem claim/lease/CAS, retry, redaction, DeviceNotRegistered, payload tipado (`notification_id`, `concurso_id`, `notification_type`) e dispatch desligado por padrão. Não há tarefa push no `beat_schedule`; drain é explícito.
- Mobile: `node --test tests/push-registration.test.cjs tests/auth-initialization.test.cjs` → 11/11 PASS; `npx tsc --noEmit` PASS. Registro/revogação por usuário, ID numérico, cold-start/deep-link validado sem URL absoluta, Expo Go/web/simulador bloqueados.
- API `/me/push-tokens` retorna apenas metadata (`id`, device/platform/estado), filtra owner e DELETE cancela fila; token não é schema/log. Modelos possuem índices/uniques adequados.

## P1 — PostgreSQL

`PushDevice.token_fingerprint` é `nullable=True` no modelo, e DELETE/revogação grava `token_fingerprint=None`; porém `PUSH_SQL` cria `token_fingerprint VARCHAR(64) NOT NULL UNIQUE`. `PUSH_UPGRADE_SQL` adiciona a coluna mas nunca remove `NOT NULL`. Em PostgreSQL novo ou legado atualizado, logout/DELETE soft falha por constraint, quebrando o contrato de revogação. SQLite não detecta isso.

Correção obrigatória: tornar `token_fingerprint` nullable na criação e em upgrade (`ALTER COLUMN ... DROP NOT NULL`), repetir teste PostgreSQL descartável e endpoint API autenticado de GET/POST/DELETE entre dois usuários. Gate operacional/deploy e teste nativo continuam pendentes.
