from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.connectors.base import BaseConnector, CrawlResult, CrawlRunData
from app.connectors.registry import get_connector
from app.models import Concurso, ConcursoPublication, ConcursoVersion, CrawlRun, Source
from app.notifications import create_notifications_for_version
from app.versioning import build_change_summary, classify_change, diff_concurso, jsonable

logger = logging.getLogger(__name__)


class CrawlService:
    def __init__(self, db: Session):
        self.db = db

    def crawl_source(self, source_id: int) -> dict[str, Any]:
        source = self.db.get(Source, source_id)
        if not source:
            raise ValueError('Fonte não encontrada')

        # Capture all source metadata before any operation that can invalidate
        # the Session.  A failed transaction expires ORM state and accessing
        # ``source`` afterwards can raise PendingRollbackError.
        source_id = source.id
        source_name = source.name
        source_type = source.source_type
        source_base_url = source.base_url
        source_list_url = source.list_url
        if not source.active:
            raise ValueError('Fonte inativa')

        started_at = datetime.now(timezone.utc)
        start_mono = time.monotonic()

        inserted = 0
        updated = 0
        unchanged = 0
        versions_created = 0
        notifications_created = 0

        try:
            connector = get_connector(source_type, base_url=source_base_url, list_url=source_list_url)
            if hasattr(connector, 'crawl_with_diagnostics'):
                crawl_res: CrawlResult = connector.crawl_with_diagnostics()
                items = list(crawl_res.items)
                run_data = crawl_res.run_data
            else:
                items = list(connector.crawl())
                run_data = CrawlRunData(
                    candidates_found=len(items),
                    status='success' if items else 'degraded',
                    error_type=None if items else 'UnconfirmedEmpty',
                    error_message=None if items else 'No items returned without explicit empty-state evidence',
                )
            # Process each discovered concurso.  All writes belong to this
            # source transaction; an exception below rolls them all back.
            for item in items:
                existing = self._find_existing_concurso(source_id, item)

                if existing is None:
                    concurso = Concurso(source_id=source_id, **item)
                    self.db.add(concurso)
                    self.db.flush()  # get concurso.id for initial version

                    version = self._create_version(
                        concurso=concurso,
                        item=item,
                        change_type='created',
                        changed_fields={},
                        change_summary=build_change_summary({}, is_created=True),
                    )
                    self._sync_publications(concurso, item)
                    self.db.flush()
                    notifications_created += create_notifications_for_version(self.db, concurso=concurso, version=version)
                    inserted += 1
                    versions_created += 1
                    continue

                new_publications = self._sync_publications(existing, item)
                changed_fields = diff_concurso(existing, item)
                if new_publications:
                    changed_fields['publications_added'] = {
                        'label': 'publicações adicionadas',
                        'old': [],
                        'new': jsonable(new_publications),
                    }

                if not changed_fields:
                    if 'fetched_at' in item:
                        existing.fetched_at = item['fetched_at']
                    unchanged += 1
                    continue

                for key, value in item.items():
                    setattr(existing, key, value)

                change_type = classify_change(changed_fields)
                change_summary = build_change_summary(changed_fields)
                version = self._create_version(
                    concurso=existing,
                    item=item,
                    change_type=change_type,
                    changed_fields=changed_fields,
                    change_summary=change_summary,
                )
                self.db.flush()
                notifications_created += create_notifications_for_version(self.db, concurso=existing, version=version)
                updated += 1
                versions_created += 1

            finished_at = datetime.now(timezone.utc)
            duration_ms = int((time.monotonic() - start_mono) * 1000)

            # Determine run status
            final_status = run_data.status
            if final_status == 'success' and not items:
                final_status = 'degraded'
                if not run_data.error_type:
                    run_data.error_type = 'UnconfirmedEmpty'
                if not run_data.error_message:
                    run_data.error_message = 'No items returned without explicit empty-state evidence'

            run_record = CrawlRun(
                source_id=source_id,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                status=final_status,
                http_status=run_data.http_status,
                browser_used=run_data.browser_used,
                candidates_found=run_data.candidates_found,
                candidates_rejected=run_data.candidates_rejected,
                processed=len(items),
                inserted=inserted,
                updated=updated,
                unchanged=unchanged,
                versions_created=versions_created,
                notifications_created=notifications_created,
                error_type=run_data.error_type,
                error_message=run_data.error_message,
                diagnostics_payload=run_data.diagnostics_payload or {},
            )
            self.db.add(run_record)
            self.db.commit()

            return {
                'source_id': source_id,
                'source_name': source_name,
                'source_type': source_type,
                'status': final_status,
                'processed': len(items),
                'candidates_found': run_data.candidates_found,
                'candidates_rejected': run_data.candidates_rejected,
                'inserted': inserted,
                'updated': updated,
                'unchanged': unchanged,
                'versions_created': versions_created,
                'notifications_created': notifications_created,
                'browser_used': run_data.browser_used,
                'duration_ms': duration_ms,
            }
        except Exception as exc:
            # This rollback must happen before recording or returning the
            # failure.  The failure record is written in a fresh transaction.
            self.db.rollback()
            duration_ms = int((time.monotonic() - start_mono) * 1000)
            logger.exception('Crawl failed for source_id=%s', source_id)
            self._record_failed_run(
                source_id=source_id,
                started_at=started_at,
                duration_ms=duration_ms,
                error_type=exc.__class__.__name__,
                error_message=str(exc)[:1000],
            )
            return {
                'source_id': source_id,
                'source_name': source_name,
                'source_type': source_type,
                'status': 'failed',
                'error': f'{exc.__class__.__name__}: {str(exc)}',
                'processed': 0,
                'inserted': 0,
                'updated': 0,
                'unchanged': 0,
                'versions_created': 0,
                'notifications_created': 0,
                'duration_ms': duration_ms,
            }

    def _record_failed_run(
        self,
        *,
        source_id: int,
        started_at: datetime,
        duration_ms: int,
        error_type: str,
        error_message: str,
    ) -> None:
        """Persist failure diagnostics after the source transaction rolled back."""
        try:
            self.db.add(CrawlRun(
                source_id=source_id,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                duration_ms=duration_ms,
                status='failed',
                error_type=error_type,
                error_message=error_message,
            ))
            self.db.commit()
        except Exception:
            self.db.rollback()
            logger.exception('Could not record failed crawl for source_id=%s', source_id)

    def _find_existing_concurso(self, source_id: int, item: dict[str, Any]) -> Concurso | None:
        """Multi-level deduplication hierarchy (within-source first, then cross-source canonical)."""
        external_id = item.get('external_id')
        link_pagina = item.get('link_pagina')
        orgao = item.get('orgao')
        edital_numero = item.get('edital_numero')
        banca = item.get('banca')

        # 1. Match by (source_id, external_id)
        if external_id:
            concurso = self.db.execute(
                select(Concurso).where(
                    Concurso.source_id == source_id,
                    Concurso.external_id == external_id,
                )
            ).scalar_one_or_none()
            if concurso:
                return concurso

        # 2. Match by (source_id, link_pagina)
        if link_pagina:
            concurso = self.db.execute(
                select(Concurso).where(
                    Concurso.source_id == source_id,
                    Concurso.link_pagina == link_pagina,
                )
            ).scalar_one_or_none()
            if concurso:
                return concurso

        # 3. Match by (source_id, orgao, edital_numero) if available
        if orgao and edital_numero:
            concurso = self.db.execute(
                select(Concurso).where(
                    Concurso.source_id == source_id,
                    Concurso.orgao == orgao,
                    Concurso.edital_numero == edital_numero,
                )
            ).scalar_one_or_none()
            if concurso:
                return concurso

        # 4. Cross-source match by canonical link_pagina
        if link_pagina:
            concurso = self.db.execute(
                select(Concurso).where(
                    Concurso.link_pagina == link_pagina,
                )
            ).scalar_one_or_none()
            if concurso:
                return concurso

        # 5. Cross-source match by (banca, external_id) for known alias sources
        if banca and external_id:
            concurso = self.db.execute(
                select(Concurso).where(
                    Concurso.banca == banca,
                    Concurso.external_id == external_id,
                )
            ).scalar_one_or_none()
            if concurso:
                return concurso

        # 6. Cross-source match by (banca, orgao, edital_numero)
        if banca and orgao and edital_numero:
            concurso = self.db.execute(
                select(Concurso).where(
                    Concurso.banca == banca,
                    Concurso.orgao == orgao,
                    Concurso.edital_numero == edital_numero,
                )
            ).scalar_one_or_none()
            if concurso:
                return concurso

        return None

    def _sync_publications(self, concurso: Concurso, item: dict) -> list[dict]:
        raw_data = item.get('raw_data') or {}
        publications = raw_data.get('publications') or []
        if not isinstance(publications, list):
            return []

        concurso_id = concurso.id
        pending_keys = {
            (pending.concurso_id, str(pending.content_hash))
            for pending in self.db.new
            if isinstance(pending, ConcursoPublication)
            and pending.concurso_id is not None
            and pending.content_hash
        }

        # Build a unique payload first.  The connector is allowed to return
        # repeated DOM rows, so a database lookup alone is insufficient.
        candidates: list[tuple[dict, str, datetime | None]] = []
        seen_keys: set[tuple[int, str]] = set()
        for publication in publications:
            if not isinstance(publication, dict):
                continue
            title = publication.get('title')
            content_hash = publication.get('content_hash')
            if not title or not content_hash:
                continue

            content_hash = str(content_hash)
            key = (concurso_id, content_hash)
            if key in seen_keys or key in pending_keys:
                continue
            seen_keys.add(key)

            publication_date = publication.get('publication_date')
            if isinstance(publication_date, str) and publication_date:
                try:
                    publication_date = datetime.fromisoformat(publication_date.replace('Z', '+00:00'))
                except ValueError:
                    publication_date = None
            candidates.append((publication, content_hash, publication_date))

        if not candidates:
            return []

        existing_hashes = set(self.db.execute(
            select(ConcursoPublication.content_hash).where(
                ConcursoPublication.concurso_id == concurso_id,
                ConcursoPublication.content_hash.in_([content_hash for _, content_hash, _ in candidates]),
            )
        ).scalars())

        created: list[dict] = []
        for publication, content_hash, publication_date in candidates:
            title = publication.get('title')
            if content_hash in existing_hashes:
                continue

            values = {
                'concurso_id': concurso_id,
                'title': str(title)[:500],
                'publication_type': publication.get('publication_type'),
                'publication_date': publication_date,
                'link': publication.get('link'),
                'content_hash': content_hash,
                'raw_data': jsonable(publication),
            }

            # The conflict target is explicit.  This makes the operation
            # idempotent under concurrent PostgreSQL workers while allowing
            # unrelated integrity errors (for example a missing title) to
            # propagate and fail the source transaction.
            result = self.db.execute(self._publication_insert_statement(values))
            if result.rowcount != 1:
                continue

            created.append({
                'title': publication.get('title'),
                'publication_type': publication.get('publication_type'),
                'publication_date': publication.get('publication_date'),
                'link': publication.get('link'),
                'content_hash': content_hash,
            })
        return created

    def _publication_insert_statement(self, values: dict[str, Any]):
        table = ConcursoPublication.__table__
        bind = self.db.get_bind()
        if bind.dialect.name == 'postgresql':
            return postgresql_insert(table).values(values).on_conflict_do_nothing(
                index_elements=[table.c.concurso_id, table.c.content_hash],
            )
        if bind.dialect.name == 'sqlite':
            return sqlite_insert(table).values(values).on_conflict_do_nothing(
                index_elements=[table.c.concurso_id, table.c.content_hash],
            )
        return insert(table).values(values)

    def _create_version(
        self,
        *,
        concurso: Concurso,
        item: dict,
        change_type: str,
        changed_fields: dict,
        change_summary: str,
    ) -> ConcursoVersion:
        version = ConcursoVersion(
            concurso_id=concurso.id,
            content_hash=item.get('content_hash') or concurso.content_hash,
            change_type=change_type,
            changed_fields=jsonable(changed_fields),
            change_summary=change_summary,
            raw_data_snapshot=jsonable(item.get('raw_data') or {}),
        )
        self.db.add(version)
        return version
