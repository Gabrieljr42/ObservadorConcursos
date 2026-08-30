from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine


CONCURSO_COLUMNS_SQL = [
    "ALTER TABLE concursos ADD COLUMN IF NOT EXISTS vagas INTEGER",
    "ALTER TABLE concursos ADD COLUMN IF NOT EXISTS salario_min NUMERIC(12, 2)",
    "ALTER TABLE concursos ADD COLUMN IF NOT EXISTS salario_max NUMERIC(12, 2)",
    "ALTER TABLE concursos ADD COLUMN IF NOT EXISTS escolaridade VARCHAR(120)",
    "ALTER TABLE concursos ADD COLUMN IF NOT EXISTS taxa NUMERIC(10, 2)",
    "ALTER TABLE concursos ADD COLUMN IF NOT EXISTS prova_data TIMESTAMP WITH TIME ZONE",
    "ALTER TABLE concursos ADD COLUMN IF NOT EXISTS edital_pdf_text_hash VARCHAR(64)",
    "ALTER TABLE concursos ADD COLUMN IF NOT EXISTS edital_pdf_pages INTEGER",
    "ALTER TABLE concursos ADD COLUMN IF NOT EXISTS edital_pdf_excerpt TEXT",
    "ALTER TABLE concursos ADD COLUMN IF NOT EXISTS pdf_extracted_at TIMESTAMP WITH TIME ZONE",
    "CREATE INDEX IF NOT EXISTS ix_concursos_prova_data ON concursos (prova_data)",
    "CREATE INDEX IF NOT EXISTS ix_concursos_edital_pdf_text_hash ON concursos (edital_pdf_text_hash)",
]


CONCURSO_VERSION_SQL = [
    "CREATE TABLE IF NOT EXISTS concurso_versions (id BIGSERIAL PRIMARY KEY, concurso_id BIGINT NOT NULL REFERENCES concursos(id) ON DELETE CASCADE, content_hash VARCHAR(64) NOT NULL, change_type VARCHAR(50) NOT NULL DEFAULT 'updated', changed_fields JSON, change_summary TEXT, raw_data_snapshot JSON, captured_at TIMESTAMP DEFAULT now() NOT NULL)",
    "CREATE INDEX IF NOT EXISTS ix_concurso_versions_concurso_id ON concurso_versions (concurso_id)",
    "CREATE INDEX IF NOT EXISTS ix_concurso_versions_content_hash ON concurso_versions (content_hash)",
    "CREATE INDEX IF NOT EXISTS ix_concurso_versions_change_type ON concurso_versions (change_type)",
    "CREATE INDEX IF NOT EXISTS ix_concurso_versions_captured_at ON concurso_versions (captured_at)",
]

CONCURSO_PUBLICATION_SQL = [
    "CREATE TABLE IF NOT EXISTS concurso_publications (id BIGSERIAL PRIMARY KEY, concurso_id BIGINT NOT NULL REFERENCES concursos(id) ON DELETE CASCADE, title TEXT NOT NULL, publication_type VARCHAR(50), publication_date TIMESTAMP WITH TIME ZONE, link TEXT, content_hash VARCHAR(64) NOT NULL, raw_data JSON, created_at TIMESTAMP DEFAULT now() NOT NULL, updated_at TIMESTAMP DEFAULT now() NOT NULL)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_concurso_publication_hash ON concurso_publications (concurso_id, content_hash)",
    "CREATE INDEX IF NOT EXISTS ix_concurso_publications_concurso_id ON concurso_publications (concurso_id)",
    "CREATE INDEX IF NOT EXISTS ix_concurso_publications_publication_type ON concurso_publications (publication_type)",
    "CREATE INDEX IF NOT EXISTS ix_concurso_publications_publication_date ON concurso_publications (publication_date)",
    "CREATE INDEX IF NOT EXISTS ix_concurso_publications_content_hash ON concurso_publications (content_hash)",
]

CRAWL_RUNS_SQL = [
    "CREATE TABLE IF NOT EXISTS crawl_runs (id BIGSERIAL PRIMARY KEY, source_id BIGINT NOT NULL REFERENCES sources(id) ON DELETE CASCADE, started_at TIMESTAMP DEFAULT now() NOT NULL, finished_at TIMESTAMP, duration_ms INTEGER, status VARCHAR(30) NOT NULL DEFAULT 'success', http_status INTEGER, browser_used BOOLEAN NOT NULL DEFAULT FALSE, candidates_found INTEGER NOT NULL DEFAULT 0, candidates_rejected INTEGER NOT NULL DEFAULT 0, processed INTEGER NOT NULL DEFAULT 0, inserted INTEGER NOT NULL DEFAULT 0, updated INTEGER NOT NULL DEFAULT 0, unchanged INTEGER NOT NULL DEFAULT 0, versions_created INTEGER NOT NULL DEFAULT 0, notifications_created INTEGER NOT NULL DEFAULT 0, error_type VARCHAR(100), error_message TEXT, diagnostics_payload JSON)",
    "CREATE INDEX IF NOT EXISTS ix_crawl_runs_source_id ON crawl_runs (source_id)",
    "CREATE INDEX IF NOT EXISTS ix_crawl_runs_started_at ON crawl_runs (started_at)",
    "CREATE INDEX IF NOT EXISTS ix_crawl_runs_status ON crawl_runs (status)",
]

REFRESH_SESSIONS_SQL = [
    "CREATE TABLE IF NOT EXISTS refresh_sessions (id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE, token_hash VARCHAR(64) NOT NULL UNIQUE, created_at TIMESTAMP DEFAULT now() NOT NULL, expires_at TIMESTAMP NOT NULL, revoked_at TIMESTAMP)",
    "CREATE INDEX IF NOT EXISTS ix_refresh_sessions_user_id ON refresh_sessions (user_id)",
    "CREATE INDEX IF NOT EXISTS ix_refresh_sessions_token_hash ON refresh_sessions (token_hash)",
    "CREATE INDEX IF NOT EXISTS ix_refresh_sessions_expires_at ON refresh_sessions (expires_at)",
]


def ensure_runtime_schema(engine: Engine) -> None:
    """Small development migration layer.

    The project still uses Base.metadata.create_all for MVP speed. create_all does
    not alter existing tables, so new nullable columns need lightweight ALTERs to
    keep old local volumes working without asking the developer to wipe Postgres.
    """
    with engine.begin() as connection:
        for statement in CONCURSO_COLUMNS_SQL:
            connection.execute(text(statement))
        for statement in CONCURSO_VERSION_SQL:
            connection.execute(text(statement))
        for statement in CONCURSO_PUBLICATION_SQL:
            connection.execute(text(statement))
        for statement in CRAWL_RUNS_SQL:
            connection.execute(text(statement))
        for statement in REFRESH_SESSIONS_SQL:
            connection.execute(text(statement))
