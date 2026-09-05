# API do backend

Base local: `http://localhost:8000`. Swagger: `http://localhost:8000/docs`. Todo o roteamento está em `backend/app/main.py`; contratos em `backend/app/schemas.py`.

## Autenticação

- Registro/login retornam `access_token` (JWT HS256 próprio, `backend/app/auth.py`, expiração default 7 dias via `ACCESS_TOKEN_EXPIRE_MINUTES=10080`) + `refresh_token` opaco (só o hash SHA-256 fica em `refresh_sessions`).
- Rotas `/me/*`, `/auth/me` e `/sync/checkpoint` exigem `Authorization: Bearer <access_token>`; sem token → `401 {"detail": "Autenticação necessária"}`.
- Senhas: PBKDF2-SHA256 (210k iterações), mínimo 6 caracteres.
- E-mail é normalizado (trim + minúsculas). Erros comuns: `422` e-mail inválido/senha curta, `401` credenciais inválidas, `403` usuário inativo, `409` e-mail já cadastrado.
- `POST /auth/refresh` renova o access token (e estende a sessão). Não há endpoint de logout/revogação — revogar exige acesso ao banco (`revoke_refresh_token`).

Exemplo:

```powershell
$body = @{ name = "João"; email = "joao@test.com"; password = "123456" } | ConvertTo-Json
$auth = Invoke-RestMethod -Method POST -Uri "http://localhost:8000/auth/register" -ContentType "application/json" -Body $body
$auth.access_token   # usar como "Bearer ..." ; $auth.refresh_token para renovar
```

```powershell
# Renovar
$rb = @{ refresh_token = $auth.refresh_token } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/auth/refresh" -ContentType "application/json" -Body $rb
```

## Rotas públicas (coleta e leitura)

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | `{status: ok, app, env}` |
| `GET` | `/sources` | Lista fontes (id desc) |
| `POST` | `/sources` | Cria fonte (`name`, `base_url`, `list_url?`, `source_type`, `active`, `frequency_minutes`) |
| `POST` | `/sources/presets/ibfc-open\|ibgp-open\|ibgp-ongoing\|imeso-open\|fundep-open\|aocp-open\|idecan-open\|consulplan-open\|fumarc-open` | Presets individuais (idempotentes por `source_type`+`list_url`) |
| `POST` | `/sources/presets/next-bancas` | Cria AOCP+IDECAN+CONSULPLAN+FUMARC de uma vez |
| `POST` | `/sources/presets/mg-priority` | Cria IBGP+IMESO+FUNDEP (foco MG) |
| `POST` | `/sources/presets/seed-all` | Sincroniza as **99** fontes do catálogo → `{total_master_sources, created, updated, unchanged}` |
| `GET` | `/sources/{id}/runs?limit=` | Últimas execuções da fonte (1–100, default 30) |
| `GET` | `/runs/recent?limit=&status=` | Execuções recentes globais (1–200, default 50) |
| `GET` | `/concursos?source_id=&banca=&status=&uf=&limit=` | Lista (banca/status substring case-insensitive; uf exata upper; limit 1–200 default 50) |
| `GET` | `/concursos/{id}` | Detalhe (`404` se inexistente) |
| `GET` | `/concursos/versions/recent?limit=&change_type=` | Versões recentes |
| `GET` | `/concursos/{id}/versions?limit=` | Histórico do concurso |
| `GET` | `/concursos/{id}/publications?limit=` | Publicações (data desc) |
| `GET` | `/updates/recent?limit=&change_type=` | Visão resumida (`UpdateOut`: id, concurso_id, change_type/summary, titulo, banca, orgao, cidade, uf, area, status) |
| `DELETE` | `/sources/{id}/concursos` | Apaga concursos da fonte (cascade) → `{deleted}` |
| `POST` | `/crawl/{id}` | Enfileira coleta no Celery → `{task_id}` |
| `POST` | `/crawl/{id}/sync` | Coleta **síncrona** (resposta é o resultado; `400` fonte inativa, `404` inexistente) |
| `POST` | `/crawl/all` ou `/crawl-all` | Enfileira todas as ativas (com lock Redis; `already_running` se ocupado) |
| `POST` | `/crawl/all/sync` ou `/crawl-all/sync` | Coleta síncrona de todas as ativas → `{status: success\|partial_failure, processed_sources, inserted, updated, ..., results, success, failed}` |

Exemplo — filtrar e inspecionar:

```powershell
Invoke-RestMethod "http://localhost:8000/concursos?uf=MG&status=abertas&limit=10"
Invoke-RestMethod "http://localhost:8000/concursos/1/versions"
Invoke-RestMethod "http://localhost:8000/sources/1/runs?limit=5"
```

Exemplo — resposta de `/crawl/1/sync` (sucesso):

```json
{
  "source_id": 1,
  "source_name": "IBFC - Inscrições Abertas",
  "source_type": "ibfc_open",
  "status": "success",
  "processed": 3, "inserted": 1, "updated": 1, "unchanged": 1,
  "versions_created": 2, "notifications_created": 1,
  "candidates_found": 3, "candidates_rejected": 0,
  "browser_used": false, "duration_ms": 8421
}
```

`status` também pode ser `degraded` (vazio sem evidência), `empty_valid`, `blocked` ou `failed` (+ `error`). Ver diagnósticos em `diagnostics_payload` via `/sources/{id}/runs`.

## Rotas do usuário (`Bearer` obrigatório)

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/auth/register` → `201` | `{name, email, password}` → `{access_token, refresh_token, token_type, user}` |
| `POST` | `/auth/login` | `{email, password}` → mesmo envelope |
| `POST` | `/auth/refresh` | `{refresh_token}` → novo `access_token` (reusa o refresh) |
| `GET` | `/auth/me` | Usuário atual |
| `GET` | `/sync/checkpoint` | Snapshot completo p/ clientes offline (concursos, publications, versions, recent/my updates, favorites, alerts, notifications, preferences) |
| `GET` / `PUT` | `/me/preferences` | Lê (pode ser `null`) / cria-atualiza (`areas, ufs, cidades, bancas, cargo_keywords, only_open, notification_channels`; UFs normalizadas p/ maiúsculas) |
| `GET` | `/me/favorites` | Favoritos (idempotente no POST; DELETE inexistente → `204` mesmo assim) |
| `POST` | `/me/favorites/{concurso_id}` → `201` | Favorita (`404` se concurso inexistente) |
| `DELETE` | `/me/favorites/{concurso_id}` → `204` | Desfavorita |
| `GET` / `POST` | `/me/alerts` | Lista / cria (`name` obrigatório; `uf` normalizada p/ 2 letras; `only_open` default true) |
| `PATCH` / `DELETE` | `/me/alerts/{id}` | Atualiza parcial / remove (`404` se não for do usuário) |
| `GET` | `/me/notifications?unread_only=` | Lista (criadas desc) |
| `GET` | `/me/updates?limit=&change_type=` | Updates filtrados pelos alertas ativos (ou preferências, se sem alertas) |
| `POST` | `/me/notifications/{id}/read` | Marca lida |
| `POST` | `/me/notifications/read-all` | Marca todas → `{updated}` |
| `POST` | `/me/alerts/run/sync` | Roda alertas ativos sobre os 500 concursos mais recentes → `{processed_alerts, created_notifications}` |

Exemplo — preferências e alerta:

```powershell
$pref = @{ ufs = @("MG","SP"); bancas = @("IBFC"); only_open = $true } | ConvertTo-Json
Invoke-RestMethod -Method PUT -Uri "http://localhost:8000/me/preferences" -Headers $headers -ContentType "application/json" -Body $pref

$alert = @{ name = "Saúde MG"; uf = "MG"; area = "saude" } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/me/alerts" -Headers $headers -ContentType "application/json" -Body $alert
```

## Fluxos de negócio principais (onde vivem)

1. **Descoberta de concursos**: presets/seed-all (`main.py` + `registry.seed_master_sources`) → crawl (sync ou Celery) → `CrawlService` (`services.py`) → linhas em `concursos`.
2. **Acompanhamento de mudanças**: diff por coleta (`versioning.py`) → `concurso_versions` → leitura em `/concursos/{id}/versions`, `/updates/recent`, `/me/updates`.
3. **Documentos do edital**: `publications.py` + `CrawlService._sync_publications` → `concurso_publications` → `/concursos/{id}/publications`; PDF resumido nos campos `edital_pdf_*` de `concursos`.
4. **Personalização**: preferências + favoritos + alertas → notificações internas geradas no crawl (`create_notifications_for_version`) ou sob demanda (`POST /me/alerts/run/sync`) → `/me/notifications`.
5. **Offline-first mobile**: `GET /sync/checkpoint` entrega tudo de uma vez; o app aplica no SQLite e drena a outbox (ver [MOBILE.md](MOBILE.md)).

## Erros, validação e limites

- Formato padrão FastAPI: `{"detail": "..."}` (mensagens em pt-BR). Validação Pydantic → `422`.
- `404`: fonte/concurso/alerta/notificação inexistente (ou de outro usuário, no caso de alertas/notificações — propositalmente indistinguível).
- `POST /crawl/all*` com crawl em andamento → `{"status": "already_running"}`; Redis fora → `503`.
- `POST /crawl/{id}/sync` de fonte inativa → `400`; exceção inesperada vira payload `status: failed` (com `CrawlRun` registrado), não `500`.
- Paginação por `limit` com teto (100/200 conforme a rota); sem cursor — `limit` alto + ordenação por `updated_at/id desc`.
- Sem rate limiting, sem versionamento de API (`/v1`), sem paginação por offset/cursor, sem endpoint de logout.

## Eventos, filas e agendamentos

- Filas Celery (Redis broker DB 0, results DB 1): `app.tasks.heartbeat`, `app.tasks.crawl_source(source_id)`, `app.tasks.crawl_active_sources(lock_token)`.
- Beat (`app/worker.py`): `heartbeat` a cada 15 min; `crawl_active_sources` toda hora cheia.
- Webhooks (entrada ou saída): **não há**. Push externo: **não há**.
