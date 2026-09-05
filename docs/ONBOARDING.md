# Onboarding — guia do novo desenvolvedor

> Documento de entrada. Tempo estimado até o primeiro run verde: ~30 min (backend) + ~20 min (mobile), excluindo download de imagens Docker.

## Checklist da primeira execução

- [ ] Clonou o repo e está na branch `main`.
- [ ] Backend: copiou `backend/.env.example` → `backend/.env` e trocou `SECRET_KEY`.
- [ ] Backend: `docker compose up --build` sobe 5 serviços (`api`, `worker`, `scheduler`, `postgres`, `redis`) sem erro.
- [ ] `GET http://localhost:8000/health` retorna `status: ok`.
- [ ] `POST /sources/presets/seed-all` retorna `total_master_sources: 99`.
- [ ] `POST /crawl/1/sync` retorna um resultado (qualquer `status` documentado) e `GET /sources/1/runs` mostra a execução.
- [ ] Registro + login + `/auth/me` funcionam (comandos no [README](../README.md)).
- [ ] Suite backend verde: `python -m pytest -q -m "not live"` (esperado: 145 passed, 2 deselected).
- [ ] Mobile: `npm install` + `npx expo start --tunnel`, app abre no Expo Go; `EXPO_PUBLIC_API_BASE_URL` aponta para a API alcançável pelo aparelho.
- [ ] Login no app + sync inicial preenche a lista de concursos (ou registra erro legível em Perfil).

## Ordem de leitura sugerida

1. [README](../README.md) (este contexto) + [ARCHITECTURE.md](ARCHITECTURE.md) — o que o sistema faz e como as peças se falam.
2. [API.md](API.md) — rotas que você vai chamar todo dia; deixe o Swagger (`/docs`) aberto ao lado.
3. [DATABASE.md](DATABASE.md) — tabelas e ciclo de vida (leia antes de mexer em `models.py`).
4. [MOBILE.md](MOBILE.md) — só se for trabalhar no app (offline-first tem armadilhas próprias).
5. [CONFIGURATION.md](CONFIGURATION.md) + [DEVELOPMENT.md](DEVELOPMENT.md) — quando for codar.
6. [DEPLOYMENT_TROUBLESHOOTING.md](DEPLOYMENT_TROUBLESHOOTING.md) — quando algo quebrar.
7. Auditoria de fontes (`SOURCES_STATUS.md`, `backend/docs/`, runbook na raiz) — só quando for mexer em conectores.

## Onde olhar para tarefas comuns

| Quero… | Olhar |
|---|---|
| Entender por que um concurso (não) apareceu | `GET /sources/{id}/runs` → `diagnostics_payload`; `backend/app/connectors/` |
| Mudar regra de alerta/notificação | `backend/app/notifications.py` (`AREA_KEYWORDS`, `SIGNIFICANT_CHANGE_TYPES`) |
| Mudar o que gera versão | `backend/app/versioning.py` (`VERSIONED_FIELDS`, `classify_change`) |
| Adicionar rota autenticada | `backend/app/main.py` + `get_current_user` (`auth.py`) |
| Entender o que o app mostra | `mobile/src/db/repositories.ts` (fonte de verdade da UI) |
| Debugar sync do app | `mobile/src/sync/syncService.ts` + `getSyncStatus()` |
| Problema de login offline | `mobile/src/storage/auth.ts` + `AuthProvider.tsx` |

## Primeira alteração guiada (30 min, segura)

**Adicionar o filtro `orgao` ao `GET /concursos`** — segue padrão existente (`banca`/`status`), sem migração, com teste.

1. Abra `backend/app/main.py`, função `list_concursos`. Adicione o parâmetro e o filtro, espelhando `banca`:
   ```python
   orgao: str | None = Query(default=None),
   ...
   if orgao:
       query = query.where(Concurso.orgao.ilike(f'%{orgao}%'))
   ```
2. Rode a API (`docker compose up --build`) e teste:
   ```powershell
   Invoke-RestMethod "http://localhost:8000/concursos?orgao=prefeitura&limit=5"
   ```
3. Adicione um teste em `backend/tests/` espelhando `test_checkpoint_route_requires_authentication` (TestClient + SQLite em memória): cria source + concurso com `orgao`, chama a rota com e sem o filtro, asserta.
4. Rode `python -m pytest -q -m "not live"` e atualize a linha do `GET /concursos` em `docs/API.md`.
5. Abra o PR conforme [DEVELOPMENT.md](DEVELOPMENT.md).

## Armadilhas e limitações (leia antes de sofrer)

- `Base.metadata.create_all()` não migra: coluna nova sem entrada em `schema_migrations.py` “funciona” em banco zerado e quebra em volume antigo. Sempre adicione o `ADD COLUMN IF NOT EXISTS`.
- `POST /sources/presets/*` e `seed-all` são idempotentes — rode sem medo; já `DELETE /sources/{id}/concursos` e `docker compose down -v` destroem dados.
- Crawl-all tem lock de 12h no Redis: dois cliques geram `already_running`, não duplicata. Não apague a chave sem checar `/runs/recent`.
- `degraded` ≠ vazio: portal sem evidência explícita de vazio é falha de extração a investigar, não “sem concursos”.
- Tipos mobile defasados: `src/types/concurso.ts` não tem os campos novos do backend (`vagas`, salários, `edital_pdf_*`) — estenda antes de exibi-los.
- `applyCheckpoint` no app faz replace total do SQLite — nunca edite o banco local esperando persistência sem passar pela outbox.
- `tsc --noEmit` já falha (ExternalLink) — não assuma “estava verde”.

## Perguntas em aberto para o mantenedor

1. `https://api.observador.tech` está no ar? Quem opera DNS/TLS e onde roda a API de produção (sem compose/manifest de prod no repo)?
2. Qual `origin` web vale: `APP_URL` do `.env.example` ou o default `*.run.app` em `mobile/app.config.js`?
3. Fluxo de contribuição oficial (branches, revisão, CI desejado) — hoje só há `main` + 3 commits.
4. Política de crawling (frequência por banca, robots, user-agent dedicado) e owner da revisão quando um portal muda de layout.
5. Estratégia de push notifications (provedor, opt-in) — hoje só existem notificações internas.
6. Retenção de `crawl_runs`/`diagnostics_payload` e backups do Postgres — hoje sem rotina.
7. Versão mínima de Python suportada (não pinada no repo; Docker usa a imagem Playwright).
