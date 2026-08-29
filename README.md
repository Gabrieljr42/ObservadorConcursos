# Observador de Concursos

Projeto organizado em duas partes:

```text
ObservadorDeCursos/
  backend/  # FastAPI + PostgreSQL + Redis + Celery + crawlers
  mobile/   # Expo + React Native + TypeScript
```

## Backend

Entrar na pasta:

```powershell
cd backend
```

Subir API, Postgres, Redis, worker e scheduler:

```powershell
docker compose up --build
```

Subir em segundo plano:

```powershell
docker compose up --build -d
```

Parar:

```powershell
docker compose down
```

Ver logs da API:

```powershell
docker compose logs -f api
```

Documentação Swagger:

```text
http://localhost:8000/docs
```

Healthcheck:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Rotas esperadas:

```text
GET  /health
GET  /sources
POST /sources
POST /sources/presets/ibfc-open
GET  /concursos
GET  /concursos/{id}
POST /crawl/{source_id}/sync
POST /auth/register
POST /auth/login
GET  /auth/me
GET  /me/preferences
PUT  /me/preferences
GET  /me/favorites
POST /me/favorites/{concurso_id}
DELETE /me/favorites/{concurso_id}
GET  /me/alerts
POST /me/alerts
PATCH /me/alerts/{alert_id}
DELETE /me/alerts/{alert_id}
GET  /me/notifications
POST /me/notifications/{notification_id}/read
POST /me/notifications/read-all
POST /me/alerts/run/sync
```

### Teste rápido de usuário

```powershell
$body = @{
  name = "João Gabriel"
  email = "joao@test.com"
  password = "123456"
} | ConvertTo-Json

$auth = Invoke-RestMethod `
  -Method POST `
  -Uri "http://localhost:8000/auth/register" `
  -ContentType "application/json" `
  -Body $body

$headers = @{ Authorization = "Bearer $($auth.access_token)" }

Invoke-RestMethod `
  -Method GET `
  -Uri "http://localhost:8000/auth/me" `
  -Headers $headers
```

## Mobile

Entrar na pasta:

```powershell
cd mobile
```

Instalar dependências:

```powershell
npm install
```

Garantir pacotes nativos do Expo:

```powershell
npx expo install @react-native-async-storage/async-storage react-native-safe-area-context
```

Rodar no celular via Expo Go:

```powershell
npx expo start --tunnel
```

Para celular físico, a API não deve usar `localhost`. Use o IP da máquina na rede, por exemplo:

```text
http://192.168.0.105:8000
```

Para emulador Android, use:

```text
http://10.0.2.2:8000
```

## O que foi limpo

Foram removidos da estrutura organizada:

```text
observador-concursos-auth-module/ aninhado
__pycache__/
*.pyc
celerybeat-schedule.db
mobile/node_modules/
mobile/.expo/
mobile/.git/
```
