# Desenvolvimento

## Comandos

Backend (dentro de `backend/`):

```powershell
docker compose up --build        # api + worker + scheduler + postgres + redis
docker compose up --build -d     # segundo plano
docker compose logs -f api       # logs da API (troque por worker|scheduler|postgres|redis)
docker compose down              # para (mantém dados)
docker compose down -v           # APAGA os volumes (destrutivo)
docker compose config --quiet    # valida o compose (verificado: OK)
```

Testes (dentro de `backend/`, sem Docker — usa SQLite em memória):

```powershell
python -m pytest -q -m "not live"   # suite padrão (verificado: 145 passed, 2 deselected)
python -m pytest -q -m live          # testes que acessam portais reais (opt-in, rede; não executado aqui)
python -m pytest --collect-only -q   # só lista
```

Mobile (dentro de `mobile/`):

```powershell
npm install
npx expo start --tunnel   # aparelho físico via Expo Go
npm run dev               # web em :3000
npm run build             # expo export -p web
npx tsc --noEmit          # checagem de tipos (hoje: 1 erro pré-existente, ver troubleshooting)
```

Não há no repo: linter, formatador, `mypy/ruff/eslint`, scripts de `test`/`lint` no `mobile/package.json`, `Makefile`, CI. Recomendações (não procedimentos existentes): adicionar `ruff + pytest` no backend e `eslint + tsc` no mobile antes de endurecer o fluxo.

## Convenções observadas (siga-as)

- Mensagens de API e logs voltados ao usuário em **pt-BR** (`'Fonte não encontrada'`, `'E-mail já cadastrado'`).
- Rotas em `main.py` finas: regra de negócio em `services.py` / `notifications.py` / `versioning.py`; parsing de portal em `connectors/common.py` + `publications.py`.
- Datas com timezone (`DateTime(timezone=True)` nos campos novos; `datetime.now(timezone.utc)`/`UTC` no código novo). Há `datetime.utcnow()` legado em `auth.py`/`models.py` (gera `DeprecationWarning` nos testes) — não introduza novos; prefira `datetime.now(timezone.utc)`.
- Campos JSON (`raw_data`, `changed_fields`) sempre passam por `jsonable()` antes de persistir (Decimal/datetime → string).
- Comparação de valores para diff usa `normalize_for_compare` (evita falsos positivos `Decimal('0.00')` vs `'0'`, datas com/sem microssegundos).
- Conectores nunca deixam exceção de PDF/parse quebrar a fonte: erro vira `diagnostics_payload`/`raw_data.pdf.error` + contadores.
- Vazio de portal exige evidência explícita (`mark_empty_evidence`); sem ela, `degraded` — nunca invente “vazio válido”.
- Mobile: telas leem SQLite via `repositories.ts`; rede só em `api/auth.ts` e `sync/syncService.ts`. Novas telas seguem esse padrão.

## Tarefas comuns

### Adicionar um endpoint (ex.: filtro `orgao` no `GET /concursos`)

1. Em `backend/app/main.py`, estenda `list_concursos` com `orgao: str | None = Query(default=None)` e `query.where(Concurso.orgao.ilike(...))` — mesmo padrão de `banca`/`status`.
2. Nada muda em `schemas.py` se o campo já existe no `ConcursoOut` (verifique).
3. Teste com `TestClient` + SQLite em memória (padrão de `tests/test_offline_sync_auth.py::test_checkpoint_route_requires_authentication`).
4. Confira no Swagger (`/docs`) e documente em `docs/API.md`.

### Adicionar campo a `concursos`

1. `models.py`: nova coluna nullable + índice se for filtro (`index=True`).
2. `schema_migrations.py`: `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` (+ índice) para volumes antigos.
3. `schemas.py`: expor no `ConcursoOut` (e no tipo mobile `src/types/concurso.ts` se a UI usar).
4. `versioning.py`: incluir em `VERSIONED_FIELDS` somente se mudança deve gerar versão/notificação.
5. Teste de diff/idempotência (espelhe `test_idempotency.py`).

### Adicionar uma fonte (banca nova)

1. Acrescente `SourceDefinition` em `MASTER_SOURCES` (`registry.py`) com `source_type` único, `base_url`, `list_urls`, `banca`, frequência.
2. Se o portal for padrão, `ConfigurableHTMLConnector`/`InstitutionalSelectionConnector` resolve; se peculiar, crie classe em `dedicated/` e registre em `DEDICATED_CLASSES`.
3. Rode `POST /sources/presets/seed-all` e `POST /crawl/{id}/sync`; inspecione `diagnostics_payload` em `/sources/{id}/runs`.
4. Adicione teste de fixture (padrão `test_connectors_fixtures.py`) + cobertura no `test_registry.py` (a contagem 99 é assertiva — **atualize-a**).
5. Regenerar docs de auditoria se aplicável (`scripts/generate_live_audit_docs.py`).

### Adicionar recurso mobile backed pelo servidor

1. Endpoint no backend + teste (acima).
2. Persistir no checkpoint (`SyncCheckpointOut` em `schemas.py` + `get_sync_checkpoint` em `main.py`) **ou** drenar via outbox (`syncService.ts` + `repositories.ts`) se for escrita.
3. Estender schema SQLite em `database.ts` e repositório em `repositories.ts`; tela lê do repositório, nunca do axios direto.
4. Rodar `npx tsc --noEmit` (após corrigir o erro atual) e testar sync com/sem rede.

## Estratégia de testes e lacunas

- Backend: 18 arquivos cobrindo registry/seed (99 fontes), dedup/idempotência, versionamento, quality gate, sanity, resiliência de crawl, plataformas dedicadas, fixtures HTML, métricas/coerência de auditoria, sync offline + auth/refresh. Marcador `live` separa testes de rede (2 testes; default `-m "not live"`).
- Lacunas honestas: sem e2e API↔banco real (só SQLite), sem testes de concorrência do lock Redis, sem testes do mobile, sem teste de carga, sem CI executando nada. Cobertura de conectores depende de fixtures — portais mudam; `CrawlRun diagnostics` + auditoria live (`scripts/run_full_live_audit.py`) são a rede de segurança operacional, não os testes unitários.

## Contribuição / PRs

Não há `CONTRIBUTING.md`, templates de PR/issue nem CI no repo (verificado: sem `.github/`, sem `Makefile`). Prática atual inferida do histórico (`main`, 3 commits, remote GitHub): trabalho direto na `main`. Sugestão mínima até o mantenedor definir o fluxo:

1. Branch curta a partir de `main` (`feat/...`, `fix/...`).
2. `pytest -q -m "not live"` verde + `docker compose config` OK (+ `tsc --noEmit` se mexeu no mobile).
3. Descreva rota/tabela nova e como verificar (curl + resposta esperada); marque comandos destrutivos (`down -v`, `DELETE .../concursos`).
4. Não commite `.env`, `*.db`, `node_modules/`, `.expo/` (já ignorados).
