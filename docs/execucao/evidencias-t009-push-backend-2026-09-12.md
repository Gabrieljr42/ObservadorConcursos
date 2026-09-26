# Evidência T009 — backend de push (2026-09-12)

Implementação restrita ao backend interno:

- `PushDevice` é vinculado ao usuário, com unicidade de `(user_id, device_id)` e do token; registro/upsert e remoção exigem autenticação.
- Listagem retorna apenas metadados (`id`, plataforma, device id, estado e timestamps); token nunca aparece no schema de saída.
- Token Expo, plataforma (`android`/`ios`) e identificador do dispositivo possuem validação estrita.
- `PushDelivery` e `PushDeliveryAttempt` formam outbox durável, deduplicada por notificação/dispositivo, com retry exponencial, limite de tentativas e falha permanente auditável.
- `ExpoPushTransport` é injetável; envia lote como array no endpoint HTTPS oficial fixo, fecha cliente próprio, e aplica timeout/batching/limite. `push_dispatch_enabled=False` por padrão e o drain é tarefa explícita, sem scheduler automático.
- Claim/lease com ownership por worker impede dois drains concorrentes na mesma linha; lease expirado é recuperável. Em crash após envio externo e antes do commit, a semântica é explicitamente at-least-once.
- Enqueue usa savepoint + unicidade para absorver corrida sem abortar a transação da notificação. Revogação é soft, cancela pendentes e preserva entregas/tentativas; `DeviceNotRegistered` desativa somente o token afetado.
- Finalização usa CAS (`processing` + `lease_owner` + lease vigente), e tentativas têm unicidade `(delivery_id, attempt_number)`; worker antigo não consegue auditar ou revogar após perder o lease.
- O drain não muta ORM tracked antes do CAS: attempts/status/metadados e contadores só são aplicados após ownership confirmado; dispositivo revogado/sem token é cancelado antes de qualquer chamada ao provider.
- Redaction recursiva cobre exceções, mensagens, detalhes e metadados controlados pelo provider. Payload inclui apenas dados tipados de deep-link (`notification_id`, `concurso_id`, `notification_type`). Fingerprints legados permanecem nulos, sem hash incompatível.
- Criação de notificações apenas enfileira registros na mesma transação; nenhuma chamada de rede é feita na transação canônica.

Validação: `backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_t009_push.py backend/tests/test_idempotency.py` → **9 passed, 1 skipped** (+ PostgreSQL descartável opcional via `TEST_POSTGRES_URL`); `compileall` concluído. Nenhum serviço externo foi instalado ou acionado.
