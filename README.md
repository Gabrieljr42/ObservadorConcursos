# Observador de Concursos

Agregador de concursos públicos brasileiros: o **backend** coleta editais nos portais das bancas, versiona mudanças e gera notificações; o **mobile** (Expo/React Native) funciona **offline-first** e sincroniza com o servidor quando há rede.

## Projeto at a glance

| Parte | Stack | Entrada principal |
|---|---|---|
| `backend/` | FastAPI + PostgreSQL 17 + Redis + Celery (worker/beat) + crawlers (httpx/Playwright) | `backend/app/main.py` |
| `mobile/` | Expo SDK 54 + React Native + TypeScript + expo-router + SQLite local | `mobile/app/_layout.tsx` |

- Catálogo de **99 fontes** (bancas e seleções institucionais) em `backend/app/connectors/registry.py`.
- Autenticação própria: JWT HS256 + refresh tokens persistidos (`backend/app/auth.py`).
- Mobile lê tudo do SQLite local (`observador.db`) e sincroniza via `GET /sync/checkpoint`.

## Quick start — backend

Pré-requisitos: Docker + Docker Compose.

```powershell
cd backend
copy .env.example .env   # ajuste SECRET_KEY
docker compose up --build
```

Confirmar que subiu:

```powershell
Invoke-RestMethod http://localhost:8000/health
# status: ok
```

Swagger: `http://localhost:8000/docs`

Popular o banco e rodar a primeira coleta (dentro do `backend/`):

```powershell
# Cadastra/atualiza as 99 fontes do catálogo
Invoke-RestMethod -Method POST http://localhost:8000/sources/presets/seed-all

# Coleta síncrona de uma fonte (troque 1 pelo id desejado)
Invoke-RestMethod -Method POST http://localhost:8000/crawl/1/sync

# Listar concursos
Invoke-RestMethod http://localhost:8000/concursos
```

Criar usuário e autenticar:

```powershell
$body = @{ name = "Seu Nome"; email = "voce@test.com"; password = "123456" } | ConvertTo-Json
$auth = Invoke-RestMethod -Method POST -Uri "http://localhost:8000/auth/register" -ContentType "application/json" -Body $body
$headers = @{ Authorization = "Bearer $($auth.access_token)" }
Invoke-RestMethod -Method GET -Uri "http://localhost:8000/auth/me" -Headers $headers
```

## Quick start — mobile

Pré-requisitos: Node.js LTS + app Expo Go no celular (ou emulador).

```powershell
cd mobile
npm install
npx expo start --tunnel
```

O app precisa alcançar a API. Defina em `mobile/.env`:

```text
EXPO_PUBLIC_API_BASE_URL=http://SEU_IP_LOCAL:8000
```

- Celular físico na mesma rede: use o IP LAN da máquina (ex.: `http://192.168.0.105:8000`).
- Emulador Android: `http://10.0.2.2:8000`.
- `localhost` só funciona no navegador (`npx expo start --web`).

> O `mobile/README.md` anterior era um template genérico e foi substituído. O fluxo oficial é o descrito aqui.

## Estrutura do repositório

```text
ObservadorDeCursos/
  README.md            # este arquivo
  docs/                # documentação por tema (arquitetura, API, banco, guias)
    ARCHITECTURE.md
    DATABASE.md
    API.md
    MOBILE.md
    CONFIGURATION.md
    DEVELOPMENT.md
    DEPLOYMENT_TROUBLESHOOTING.md
    ONBOARDING.md
    LIVE_*.md / SOURCES_STATUS.md   # auditoria das fontes (material existente, preservado)
  backend/             # API + workers + crawlers
    app/               # main.py, models.py, services.py, auth.py, connectors/, pdf/
    tests/             # pytest (SQLite em memória; testes live são opt-in)
    scripts/           # auditoria live e empacotamento
    docker-compose.yml # api, worker, scheduler, postgres, redis (+ pgadmin opcional)
  mobile/              # app Expo offline-first
    app/               # rotas expo-router (onboarding, login, (tabs)/, concurso/[id])
    src/api|db|sync|storage|providers/  # acesso local + sincronização + sessão
  scripts/             # utilitários na raiz (auditoria, empacotamento)
```

## Documentação

| Documento | Conteúdo |
|---|---|
| [docs/ONBOARDING.md](docs/ONBOARDING.md) | **Comece aqui.** Checklist da primeira execução, ordem de leitura e primeira alteração guiada |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Serviços, fluxos de coleta/sync/alertas e mapa do repositório |
| [docs/API.md](docs/API.md) | Rotas, auth, exemplos de request/response |
| [docs/DATABASE.md](docs/DATABASE.md) | Tabelas, relacionamentos, migrações e reset local |
| [docs/MOBILE.md](docs/MOBILE.md) | App offline-first: telas, SQLite, outbox e background sync |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Variáveis de ambiente e serviços externos |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Comandos, padrões de código, testes e como contribuir |
| [docs/DEPLOYMENT_TROUBLESHOOTING.md](docs/DEPLOYMENT_TROUBLESHOOTING.md) | O que existe de deploy/operação + falhas comuns |

Guias específicos já existentes e preservados: [backend/README.md](backend/README.md) (fluxo IBFC e extração de PDF), auditoria das fontes em [docs/SOURCES_STATUS.md](docs/SOURCES_STATUS.md) e `backend/docs/`.

## Status de verificação

Testado durante a escrita desta documentação:

- `pytest -q -m "not live"` no `backend/`: **145 passed, 2 deselected**.
- `docker compose config`: válido.
- `npx tsc --noEmit` no `mobile/`: 1 erro pré-existente em `components/ExternalLink.tsx` (tipo de `href` com `typedRoutes`) — ver [troubleshooting](docs/DEPLOYMENT_TROUBLESHOOTING.md).

Não testado (requer rede/containers ou decisão do mantenedor): `docker compose up`, `expo start`, scripts de auditoria live (`-m live`), URLs de produção (`https://api.observador.tech`).
