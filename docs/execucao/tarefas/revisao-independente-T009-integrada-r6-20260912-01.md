# Revisão independente integrada T009 — r6

Status: ACEITA para código; liberado o próximo gate operacional.

- `PUSH_SQL` agora cria `token` e `token_fingerprint` nullable, mantendo unicidade de fingerprint e `(user_id, device_id)`; `PUSH_UPGRADE_SQL` executa `ALTER COLUMN token DROP NOT NULL` e `ALTER COLUMN token_fingerprint DROP NOT NULL` antes do índice único. A sequência é repetível e cobre volume legado com fingerprint NOT NULL. `revoked_at`/`revoke_reason` permanecem nas tabelas e no modelo.
- Suíte dirigida (`test_t009_push.py`, `test_idempotency.py`, `test_offline_sync_auth.py`): 16 PASS, 1 skip (fixture PostgreSQL ausente). Os testes incluem asserções SQL da criação/upgrade e revogação nullable.

Gate de código: ACEITA. Libero o integrador para executar fixture PostgreSQL descartável, aplicar upgrade duas vezes, testar GET/POST/DELETE autenticado entre dois usuários e confirmar índices/ownership. Depois pode prosseguir para build/deploy e smoke autenticado.

Isto não é aceite do PostgreSQL real, deploy nem teste nativo externo: esses gates permanecem obrigatórios e separados.
