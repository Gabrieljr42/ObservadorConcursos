# Configuração e integrações

Use placeholders nos seus arquivos locais. Nunca commite `.env` (já está no `.gitignore` raiz e no `.dockerignore` do backend).

## Backend (`backend/.env`)

Copie o exemplo e ajuste o segredo:

```powershell
cd backend
copy .env.example .env
```

| Variável | Obrigatória | Default (`config.py` / `.env.example`) | Uso |
|---|---|---|---|
| `APP_NAME` | não | `Observador de Concursos` | Título do FastAPI e resposta do `/health` |
| `APP_ENV` | não | `development` | Exposto no `/health`; sem comportamento condicional hoje |
| `APP_DEBUG` | não | `true` | Declarado; sem uso condicional verificado no código |
| `API_PORT` | não | `8000` | Documental (o compose publica `8000:8000`; o comando do uvicorn fixa `--port 8000`) |
| `DATABASE_URL` | sim (fora do compose) | `postgresql+psycopg://postgres:postgres@postgres:5432/observador` | Engine SQLAlchemy (`database.py`). **No compose, o bloco `environment:` sobrescreve o `.env`** com o mesmo valor apontando p/ o serviço `postgres` |
| `CELERY_BROKER_URL` | sim (fora do compose) | `redis://redis:6379/0` | Broker Celery + base do lock distribuído (`crawl_lock.py` usa `celery_broker_url` p/ o Redis). Sobrescrito pelo compose |
| `CELERY_RESULT_BACKEND` | sim (fora do compose) | `redis://redis:6379/1` | Backend de resultados Celery. Sobrescrito pelo compose |
| `SECRET_KEY` | **sim em produção** | `change-me-in-production` | Assinatura HMAC dos JWTs. **Trocar em qualquer ambiente real**: vazar/invadir permite forjar tokens |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | não | `10080` (7 dias) | Expiração do access token |

`get_settings()` (`pydantic-settings`, `env_file=".env"`, `extra="ignore"`) é cacheado; o `lifespan` lê essas settings no boot.

Rodar fora do Docker (não é o fluxo documentado, mas suportado pelo código): exporte `DATABASE_URL` apontando para um Postgres acessível e `CELERY_BROKER_URL` para um Redis, instale `requirements.txt` e rode `uvicorn app.main:app`. O `lifespan` cria o schema sozinho.

## Mobile (`mobile/.env`)

```powershell
cd mobile
copy .env.example .env
```

| Variável | Obrigatória | Exemplo | Uso |
|---|---|---|---|
| `EXPO_PUBLIC_API_BASE_URL` | sim (fora dos builds EAS) | `http://192.168.0.105:8000` | `baseURL` do axios (`src/api/client.ts` e `src/api/auth.ts`). Fallback no código: `https://api.observador.tech` |
| `APP_URL` | não | `https://api.observador.tech` | `origin` do Expo Router web (`app.config.js`); o default no código é uma URL `*.run.app` legada — prefira definir explicitamente |

Tabela rápida aparelho × URL: navegador `http://localhost:8000`; físico `http://<IP-LAN>:8000`; emulador Android `http://10.0.2.2:8000`. Detalhes em [MOBILE.md](MOBILE.md).

## Serviços externos e dependências de rede

| Serviço | Ambiente local | Produção (a confirmar) |
|---|---|---|
| PostgreSQL 17 | container `postgres` (volume `postgres_data`, porta 5432) | não configurado no repo |
| Redis 7 | container `redis` (volume `redis_data`, porta 6379; DB 0 broker/lock, DB 1 resultados) | não configurado no repo |
| pgAdmin | container `pgadmin` só com `--profile tools` (porta 5050) | n/a |
| Portais das 99 bancas | leitura pública via crawlers (respeitar robots/termos de cada portal; alguns exigem Playwright/Cloudflare bypass) | mesmo |
| `https://api.observador.tech` | túnel Cloudflare para o computador local do mantenedor | Referenciada no `mobile/.env.example`, `eas.json` e fallback do `client.ts`. Depende do computador, API e túnel ativos; não representa hospedagem permanente. Em 25/10/2026 retornou HTTP 530 com o túnel indisponível. Para desenvolvimento, defina a URL local adequada ao dispositivo |
| EAS (`eas.json`, `projectId` em `app.json`) | builds `preview` (APK) e `production` (AAB) | requer conta Expo + credenciais; nunca executado neste trabalho |

Nada no código envia e-mail, SMS ou push: “notificações” são registros internos. Quaisquer segredos futuros (Sentry, provedores de push) devem entrar via `.env` + `.env.example` com placeholder, nunca com valor real.
