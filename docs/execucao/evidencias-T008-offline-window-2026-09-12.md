# Janela offline controlada T008 — 2026-09-12

- **Estado seguro confirmado:** 2026-09-12T18:25:22-03:00.
- **Comando:** `docker compose --env-file backend/.env.pilot -f backend/docker-compose.pilot.yml stop api`.
- **Mutação autorizada:** somente `observador-pilot-api-1` foi parado temporariamente. Web, worker, scheduler, PostgreSQL e Redis permaneceram ativos; volumes e configuração não foram alterados.
- **Health antes:** HTTP 200 em `http://127.0.0.1:18000/health`.
- **Health durante offline:** indisponível como esperado; conexão a `127.0.0.1:18000` recusada.
- **Próximo passo:** aguardar `ONLINE_AGORA`; então iniciar somente a mesma API, esperar health HTTP 200 e registrar o retorno.

## Retorno online

- Durante a API parada, validação real registrou `VAL-20260912-REAL-01-alert-182522`: alerta criado localmente ativo e imediatamente desligado (`Value:0`); Garibaldi ID 33 mudou localmente de SALVAR para SALVO.
- **Comando de retorno:** `docker compose --env-file backend/.env.pilot -f backend/docker-compose.pilot.yml up -d api`.
- **Início:** 2026-09-12T18:26:32-03:00; **ONLINE_READY:** 2026-09-12T18:26:38-03:00.
- Health HTTP 200: `{"status":"ok","app":"Observador de Concursos","env":"local-pilot"}`. Somente a API foi iniciada; não houve deploy, migração ou alteração nos demais serviços.

## Validação read-only pós-retorno

- Conta consultada: `operador@observador.local`; endpoints `GET /me/alerts` e `GET /me/favorites`.
- Janela de polling: 2026-09-12T18:28:00–18:28:55-03:00.
- Resultado: **FAIL** — alerta `VAL-20260912-REAL-01-alert-182522` não localizado no servidor (somente alerta existente id `1`, ativo); favorito `concurso_id=33` não localizado (lista vazia).
- Nenhuma sincronização manual, escrita ou alteração de serviço foi executada durante a consulta.

### Revalidação após reabertura de Salvos

- Polling read-only: 2026-09-12T18:29:15–18:30:15-03:00; API errors: none.
- Resultado: **FAIL** — `VAL-20260912-REAL-01-alert-182522` ainda não localizado; `concurso_id=33` ainda não localizado em `/me/favorites`. O servidor retornou somente alerta id `1` (`active=true`) e favoritos vazios.

### Revalidação após redeploy T008 r3

- Janela read-only: 2026-09-12T18:38:03–18:39:03-03:00; erros de API: nenhum.
- **PASS** — alerta id `6`, nome `VAL-20260912-REAL-01-alert-182522`, `active=false`; favorito id `8`, `concurso_id=33`, presente no servidor.
- Checkpoint: `alerts=2`, `favorites=1`. Logs API: `POST /me/alerts` 201, `PATCH /me/alerts/6` 200, `POST /me/favorites/33` 201, `GET /sync/checkpoint` 200 e consultas read-only 200.

### Checagem pós-bundle r3 — confirmação final

- Timestamp: 2026-09-12T18:41:42-03:00; polling read-only concluído sem erros.
- **PASS** — alerta id `6`, `VAL-20260912-REAL-01-alert-182522`, `active=false`; favorito id `8`, `concurso_id=33` presente.
- Checkpoint: `alerts=2`, `favorites=1`; outbox mobile não é exposto pelo contrato server-side. Logs recentes: GET `/me/alerts`, `/me/favorites` e `/sync/checkpoint` HTTP 200, sem erros/500.

### Remoção de favorito pós-aceite

- Timestamp read-only: 2026-09-12T18:48:34-03:00.
- **PASS** — favorito id `8`/concurso `33` ausente em `/me/favorites`; checkpoint `favorites=0`; vazio legítimo após reload.
- Logs API sem erro: `DELETE /me/favorites/33` 204, `GET /sync/checkpoint` 200 e `GET /me/favorites` 200.

### Exclusão do alerta de teste pós-reload

- Timestamp read-only: 2026-09-12T18:49:35-03:00.
- **PASS** — alerta id `6` ausente; alerta original id `1` (`Concursos revisados do piloto`) preservado e ativo; checkpoint `alerts=1`, `favorites=0`.
- Logs API sem erro: `DELETE /me/alerts/6` 204; `GET /sync/checkpoint` e `GET /me/alerts` 200.
