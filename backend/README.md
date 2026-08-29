# Observador de Concursos - Backend

Backend FastAPI do MVP do Observador de Concursos.

## Serviços

- FastAPI (`api`)
- PostgreSQL (`postgres`)
- Redis (`redis`)
- Celery worker (`worker`)
- Celery beat (`scheduler`)

## Rodar

```powershell
cd backend
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

Rotas disponíveis:

```text
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

## Desenvolvimento

O projeto ainda usa `Base.metadata.create_all()` para velocidade de MVP. Como `create_all()` não altera tabelas existentes, existe uma camada leve em `app/schema_migrations.py` que adiciona colunas novas nullable em ambiente de desenvolvimento sem precisar apagar o volume do Postgres.
