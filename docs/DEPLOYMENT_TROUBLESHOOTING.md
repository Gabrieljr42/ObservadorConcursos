# Deploy, operação e troubleshooting

## O que existe (evidência no repo) vs. o que falta

| Tema | Existe | Falta / a confirmar |
|---|---|---|
| Ambiente local | `backend/docker-compose.yml` (api/worker/scheduler/postgres/redis, healthchecks, volumes) — `config` validado | Compose de produção, `restart:` policies, limites de recurso |
| App mobile | `eas.json` (`preview` APK interno, `production` AAB, ambos `EXPO_PUBLIC_API_BASE_URL=https://api.observador.tech`) | Conta EAS, credenciais Android, processo de release; conectividade com `api.observador.tech` **não verificada** |
| Banco admin | pgAdmin via `--profile tools` (:5050) | Backups, restore testado, retenção |
| CI/CD | — | Sem `.github/`, pipeline ou checagem automatizada |
| Logs | stdout dos containers (`docker compose logs -f <svc>`); `CrawlRun.diagnostics_payload` no banco | Agregação, alerta, retenção |
| Monitoramento/health | `GET /health`; beat `heartbeat` (só indica scheduler vivo); `GET /runs/recent?status=failed` como painel operacional | Uptime checks, métricas, SLOs |
| Rollback | Reversível por imagem/volume em tese; `DELETE /sources/{id}/concursos` + recrawl reconstrói coletas | Procedimento escrito/testado: **não há** |

Recomendação (não procedimento existente): antes de qualquer produção, definir `SECRET_KEY` forte, backup do volume `postgres_data`, `restart: unless-stopped`, e um check externo no `/health` + `/runs/recent?status=failed`.

## Operação do dia a dia

```powershell
cd backend
docker compose up --build -d
docker compose logs -f api worker scheduler
docker compose ps
```

- Ver coletas com falha: `GET /runs/recent?status=failed` (ou `?status=degraded|blocked`) e abrir `diagnostics_payload` (motivos de rejeição, `empty_evidence`, `sanity_rejections`).
- Recoletar tudo: `POST /crawl/all/sync` (resposta inclui `success`/`failed` por fonte). Concorrente recebe `already_running`.
- Auditoria portal×crawler: `python scripts/run_full_live_audit.py` (rede nos 99 portais; gera `audit_live_99.json`/`live_evidence.json`) e `python scripts/generate_live_audit_docs.py` (regenera `backend/docs/LIVE_*`). **Não rodado neste trabalho.**

## Falhas comuns e diagnóstico

| Sintoma | Causa provável | Como confirmar / resolver |
|---|---|---|
| `503` em `POST /crawl/all` | Redis fora (lock indisponível) | `docker compose ps redis`; `docker compose logs redis`. Sem Redis não há crawl-all seguro — suba o serviço, não contorne o lock |
| `already_running` persistente | Lock órfão (TTL 12h) após queda | Inspecione `GET /runs/recent`; se nenhum crawl ativo, apague a chave `observador:crawl_all_lock` no Redis e investigue a queda |
| Runs `blocked` (Cloudflare/403/429) | Proteção do portal | Esperado: conector tenta Playwright; se persistir, fonte fica `blocked` com evidência — não é bug do backend. Re-testar depois |
| Runs `degraded` / `UnconfirmedEmpty` | Seletor mudou ou página JS-only | Abrir o `list_url` no navegador; ajustar `SourceDefinition`/conector dedicado; nunca marcar vazio sem evidência |
| `empty_valid` inesperado | `empty_state_patterns` genérico demais | Checar `diagnostics_payload.empty_evidence` e restringir o padrão à fonte |
| API não cria tabelas novas | Volume antigo + coluna nova sem migration | Registrar `ADD COLUMN IF NOT EXISTS` em `schema_migrations.py` (o `create_all` não altera tabelas) |
| `401` no app mesmo logado | Access token expirado e refresh ausente/inválido | `POST /auth/refresh`; se falhar, login online novamente. Offline só funciona se a conta já foi validada no aparelho |
| App não alcança API no celular | `localhost` no `EXPO_PUBLIC_API_BASE_URL` | Usar IP LAN (`192.168.x.x:8000`) ou `10.0.2.2:8000` no emulador Android |
| Sync retorna `ok:false` | Rede/auth | Ler motivo em Perfil → status de sync (`last_sync_error` no SQLite via `getSyncStatus`) |
| `tsc --noEmit` falha em `ExternalLink.tsx` | `href: string` vs rotas tipadas (`typedRoutes`) | Pré-existente (verificado). Correção sugerida: tipar como `React.ComponentProps<typeof Link>['href']` ou desabilitar `typedRoutes` conscientemente |
| Warnings `datetime.utcnow() is deprecated` nos testes | Legado em `auth.py`/`models.py`/teste | Cosmético; não introduzir novos `utcnow()` (usar `datetime.now(timezone.utc)`) |
| `docker compose down -v` | Apaga volumes | **Destrutivo**: só para reset local consciente (ver [DATABASE.md](DATABASE.md)) |

## Troubleshooting da primeira subida

1. `docker compose up --build` falha no build → confira Docker Desktop em execução e espaço em disco (imagem Playwright é pesada).
2. API sobe mas `/health` não responde → `docker compose logs -f api` (o `lifespan` pode estar criando schema/migrations na primeira vez — aguarde) e `docker compose ps` (postgres/redis `healthy`?).
3. `seed-all` retorna `created: 0, unchanged: 99` → normal em banco já semeado; `created: 99` só na primeira vez.
4. Mobile trava no login → confirme a URL da API a partir do aparelho (`EXPO_PUBLIC_API_BASE_URL` alcançável) antes de mexer em auth.
