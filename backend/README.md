# Observador de Concursos - Backend

Backend FastAPI do MVP do Observador de Concursos.

Documentação completa: [../README.md](../README.md) (quick start), [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [../docs/API.md](../docs/API.md), [../docs/DATABASE.md](../docs/DATABASE.md).

## Serviços

- FastAPI (`api`, :8000)
- PostgreSQL 17 (`postgres`)
- Redis 7 (`redis`)
- Celery worker (`worker`)
- Celery beat (`scheduler`: `heartbeat` a cada 15 min, `crawl_active_sources` toda hora cheia)
- pgAdmin opcional (`pgadmin`, perfil `tools`, :5050)

## Rodar

```powershell
cd backend
copy .env.example .env   # ajuste SECRET_KEY
docker compose up --build
```

API:

```text
http://localhost:8000
http://localhost:8000/docs
```

## Fluxo inicial de coleta IBFC

Criar fonte preset:

```powershell
Invoke-RestMethod -Method POST http://localhost:8000/sources/presets/ibfc-open
```

Ou semear as 99 fontes do catálogo de uma vez:

```powershell
Invoke-RestMethod -Method POST http://localhost:8000/sources/presets/seed-all
```

Rodar coleta sincronamente:

```powershell
Invoke-RestMethod -Method POST http://localhost:8000/crawl/1/sync
```

Listar concursos:

```powershell
Invoke-RestMethod http://localhost:8000/concursos
```

## O que o conector IBFC faz agora

O conector `ibfc_open` agora coleta a página oficial de inscrições abertas e, para cada concurso encontrado:

1. acessa a página de detalhes;
2. extrai dados do HTML, como situação, edital, data do edital, inscrições e links;
3. baixa o PDF do edital quando `link_edital` existe;
4. extrai texto do PDF com `pypdf`, sem OCR;
5. tenta inferir campos estruturados do edital:
   - cargo;
   - área;
   - vagas;
   - salário mínimo/máximo;
   - escolaridade;
   - taxa;
   - data da prova;
6. salva metadados da extração em `raw_data.pdf` e `raw_data.pdf_fields`.

Campos adicionados em `concursos`:

```text
vagas
salario_min
salario_max
escolaridade
taxa
prova_data
edital_pdf_text_hash
edital_pdf_pages
edital_pdf_excerpt
pdf_extracted_at
```

## Observação sobre PDFs

A extração usa texto embutido no PDF. Se o edital for escaneado/imagem, o sistema registra o erro em `raw_data.pdf.error` e segue sem quebrar a coleta. OCR fica para uma etapa futura.

## Auth / Usuário

Rotas disponíveis (lista completa e exemplos em [../docs/API.md](../docs/API.md)):

```text
POST /auth/register
POST /auth/login
POST /auth/refresh
GET  /auth/me
GET  /sync/checkpoint
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
GET  /me/updates
POST /me/notifications/{notification_id}/read
POST /me/notifications/read-all
POST /me/alerts/run/sync
```

## Desenvolvimento

O projeto ainda usa `Base.metadata.create_all()` para velocidade de MVP. Como `create_all()` não altera tabelas existentes, existe uma camada leve em `app/schema_migrations.py` que adiciona colunas novas nullable em ambiente de desenvolvimento sem precisar apagar o volume do Postgres. Não há diretório de migrações Alembic (o pacote consta no `requirements.txt`, mas sem scripts no repo).

Testes (SQLite em memória; `live` = portais reais, opt-in):

```powershell
python -m pytest -q -m "not live"
python -m pytest -q -m live
```
