from __future__ import annotations

import copy
import hashlib
import json
import logging
import re
import time
from datetime import date, datetime, timezone
from typing import Any
from urllib.parse import urlsplit

from sqlalchemy import insert, select, update
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.connectors.base import BaseConnector, CrawlResult, CrawlRunData
from app.connectors.registry import get_connector
from app.concurso_identity import identity_is_blank
from app.config import get_settings
from app.models import Concurso, ConcursoPublication, ConcursoVersion, CrawlRun, Source
from app.notifications import create_notifications_for_version
from app.publications import build_publication_hash
from app.versioning import (build_change_summary, classify_change, diff_concurso,
                            jsonable, normalize_for_compare)

logger = logging.getLogger(__name__)

_AMENDMENT_DATE_FIELDS = frozenset({'prova_data', 'inscricao_inicio', 'inscricao_fim'})


def _same_amendment_value(left: Any, right: Any, field: str) -> bool:
    """Compare amendment dates across SQLite's naive and PostgreSQL's aware round trips."""
    if field not in _AMENDMENT_DATE_FIELDS:
        return normalize_for_compare(left, field=field) == normalize_for_compare(right, field=field)
    def key(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.replace(tzinfo=None).isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return value.strip()
            return parsed.replace(tzinfo=None).isoformat()
        return normalize_for_compare(value, field=field)
    return key(left) == key(right)


class AmbiguousContestIdentity(ValueError):
    """A catalogue URL or fallback identifies multiple possible contests."""


class CrawlService:
    def __init__(self, db: Session):
        self.db = db

    def crawl_source(self, source_id: int) -> dict[str, Any]:
        if not get_settings().legacy_crawler_enabled:
            raise ValueError('Coletor antigo desativado; use a coleta e revisão TenderProof')
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
                if existing is not None and existing.external_id and identity_is_blank(item.get('external_id')):
                    # A URL-only legacy observation must not erase a reviewed ID.
                    item = {**item, 'external_id': existing.external_id}

                if existing is None:
                    concurso = Concurso(source_id=source_id, **item)
                    self.db.add(concurso)
                    self.db.flush()  # get concurso.id for initial version

                    new_publications = self._sync_publications(concurso, item)
                    created_fields = {}
                    if new_publications:
                        created_fields['publications_added'] = {
                            'label': 'publicações adicionadas',
                            'old': [],
                            'new': jsonable(new_publications),
                        }
                    version = self._create_version(
                        concurso=concurso,
                        item=item,
                        change_type='created',
                        changed_fields=created_fields,
                        change_summary=build_change_summary(created_fields, is_created=True),
                    )
                    self.db.flush()
                    notifications_created += create_notifications_for_version(self.db, concurso=concurso, version=version)
                    inserted += 1
                    versions_created += 1
                    continue

                self._claim_external_identity(existing, item)
                item, amendment_guarded = self._guard_amended_observation(existing, item)
                # Legacy connectors cannot erase reviewed structured job data.
                item['cargos'] = existing.cargos
                new_publications = self._sync_publications(existing, item)
                changed_fields = diff_concurso(existing, item)
                if not identity_is_blank(item.get('external_id')) and existing.external_id != item['external_id']:
                    changed_fields['external_id'] = {
                        'label': 'identificador externo', 'old': existing.external_id, 'new': item['external_id'],
                    }
                if new_publications:
                    changed_fields['publications_added'] = {
                        'label': 'publicações adicionadas',
                        'old': [],
                        'new': jsonable(new_publications),
                    }

                if not changed_fields:
                    if 'fetched_at' in item:
                        existing.fetched_at = item['fetched_at']
                    # Raw source metadata is useful even when no catalog
                    # field changed.  The amendment guard has already
                    # retained the app-owned ledger and history keys.
                    if amendment_guarded and item.get('raw_data') != existing.raw_data:
                        existing.raw_data = copy.deepcopy(item.get('raw_data'))
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

    def _claim_external_identity(self, existing: Concurso, item: dict[str, Any]) -> None:
        """Compare-and-swap before any dependent writes, retaining ORM audit state."""
        expected = existing.external_id
        requested = item.get('external_id')
        target = expected if identity_is_blank(requested) else requested
        if not identity_is_blank(expected) and target != expected:
            raise AmbiguousContestIdentity('identificador existente não pode ser substituído')
        with self.db.no_autoflush:
            result = self.db.execute(update(Concurso).where(
                Concurso.id == existing.id, Concurso.external_id == expected
            ).values(external_id=target, updated_at=Concurso.updated_at).execution_options(synchronize_session=False))
        if result.rowcount != 1:
            raise AmbiguousContestIdentity('identidade alterada concorrentemente; repetir resolução em nova transação')

    def _guard_amended_observation(self, existing: Concurso, item: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        """Keep an applied amendment from being reverted by the old crawler.

        A legacy observation can still carry useful source metadata and
        changes to unrelated fields.  Only fields covered by an amendment
        whose ``new`` value is still canonical are held back.  A conflicting
        old value is retained as a deterministic diagnostic in the
        TenderProof ledger so it can be reviewed through the normal flow.
        """
        protected: dict[str, dict[str, Any]] = {}
        versions = self.db.scalars(
            select(ConcursoVersion)
            .where(ConcursoVersion.concurso_id == existing.id,
                   ConcursoVersion.change_type == 'amendment')
            .order_by(ConcursoVersion.id.desc())
        ).all()
        for version in versions:
            for field, change in (version.changed_fields or {}).items():
                if field in protected or not isinstance(change, dict):
                    continue
                current = getattr(existing, field, None)
                if _same_amendment_value(current, change.get('new'), field):
                    protected[field] = change
        if not protected:
            return item, False

        guarded = dict(item)
        conflicts: dict[str, dict[str, Any]] = {}
        for field, change in protected.items():
            current = getattr(existing, field, None)
            observed = item.get(field)
            if not _same_amendment_value(observed, current, field):
                conflicts[field] = {
                    'observed': jsonable(observed),
                    'kept': jsonable(current),
                    'amendment_new': jsonable(change.get('new')),
                }
            guarded[field] = current

        guarded['raw_data'] = self._merge_amendment_raw_data(
            existing.raw_data, item.get('raw_data'), conflicts,
            content_hash=item.get('content_hash'), fetched_at=item.get('fetched_at'),
        )
        return guarded, True

    @staticmethod
    def _merge_amendment_raw_data(existing_raw: Any, observed_raw: Any, conflicts: dict[str, dict[str, Any]], *,
                                  content_hash: Any = None, fetched_at: Any = None) -> dict[str, Any]:
        """Merge a legacy payload without letting it replace app-owned history."""
        previous = copy.deepcopy(existing_raw) if isinstance(existing_raw, dict) else {}
        observed = copy.deepcopy(observed_raw) if isinstance(observed_raw, dict) else {}
        merged = observed
        for key in ('tenderproof', 'history'):
            if key not in previous:
                continue
            old_value = previous[key]
            new_value = merged.get(key)
            if isinstance(old_value, dict) and isinstance(new_value, dict):
                # Existing ledger entries win on collisions; source-specific
                # additions remain available for later review.
                merged[key] = {**new_value, **copy.deepcopy(old_value)}
            elif isinstance(old_value, list) and isinstance(new_value, list):
                merged[key] = copy.deepcopy(old_value)
                for entry in new_value:
                    if entry not in merged[key]:
                        merged[key].append(entry)
            else:
                merged[key] = copy.deepcopy(old_value)

        if conflicts:
            fingerprint = hashlib.sha256(json.dumps(
                {'content_hash': content_hash, 'fields': conflicts},
                sort_keys=True, ensure_ascii=False, default=str,
                separators=(',', ':')).encode('utf-8')).hexdigest()
            tenderproof = merged.get('tenderproof')
            # Keep a malformed/non-dict legacy value byte-for-byte and put
            # the diagnostic beside it.  A collector must never make the
            # app-owned ``tenderproof`` field disappear while preserving it.
            diagnostic_owner = tenderproof if isinstance(tenderproof, dict) else merged
            observations = diagnostic_owner.setdefault('legacy_observations', [])
            if not isinstance(observations, list):
                observations = []
                diagnostic_owner['legacy_observations'] = observations
            if not any(isinstance(entry, dict) and entry.get('observation_key') == fingerprint for entry in observations):
                observations.append({
                    'observation_key': fingerprint,
                    'source': 'legacy_crawler',
                    'content_hash': content_hash,
                    'observed_at': jsonable(fetched_at) or datetime.now(timezone.utc).isoformat(),
                    'protected_fields': conflicts,
                    'review_required': True,
                })
        return merged

    def _find_existing_concurso(self, source_id: int, item: dict[str, Any]) -> Concurso | None:
        """Multi-level deduplication hierarchy (within-source first, then cross-source canonical)."""
        external_id = item.get('external_id')
        link_pagina = item.get('link_pagina')
        orgao = item.get('orgao')
        edital_numero = item.get('edital_numero')
        banca = item.get('banca')
        external_id = None if identity_is_blank(external_id) else external_id

        def one(statement, *, compatible_external=False):
            rows = list(self.db.scalars(statement))
            if compatible_external and external_id:
                rows = [row for row in rows if identity_is_blank(row.external_id) or row.external_id == external_id]
            if len(rows) > 1:
                raise AmbiguousContestIdentity('identidade de concurso ambígua; URL compartilhada exige identificador explícito')
            return rows[0] if rows else None

        # 1. Match by (source_id, external_id)
        if external_id:
            concurso = one(
                select(Concurso).where(
                    Concurso.source_id == source_id,
                    Concurso.external_id == external_id,
                )
            )
            if concurso:
                return concurso

        # 2. Match by (source_id, link_pagina)
        if link_pagina:
            concurso = one(
                select(Concurso).where(
                    Concurso.source_id == source_id,
                    Concurso.link_pagina == link_pagina,
                )
            , compatible_external=True)
            if concurso:
                return concurso

        # 3. Match by (source_id, orgao, edital_numero) if available
        if orgao and edital_numero:
            concurso = one(
                select(Concurso).where(
                    Concurso.source_id == source_id,
                    Concurso.orgao == orgao,
                    Concurso.edital_numero == edital_numero,
                )
            , compatible_external=True)
            if concurso:
                return concurso

        # 4. Cross-source match by canonical link_pagina
        if link_pagina:
            concurso = one(
                select(Concurso).where(
                    Concurso.link_pagina == link_pagina,
                )
            , compatible_external=True)
            if concurso:
                return concurso

        # 5. Cross-source match by (banca, external_id) for known alias sources
        if banca and external_id:
            concurso = one(
                select(Concurso).where(
                    Concurso.banca == banca,
                    Concurso.external_id == external_id,
                )
            )
            if concurso:
                return concurso

        # 6. Cross-source match by (banca, orgao, edital_numero)
        if banca and orgao and edital_numero:
            concurso = one(
                select(Concurso).where(
                    Concurso.banca == banca,
                    Concurso.orgao == orgao,
                    Concurso.edital_numero == edital_numero,
                )
            , compatible_external=True)
            if concurso:
                return concurso

        return None

    def _sync_publications(self, concurso: Concurso, item: dict) -> list[dict]:
        raw_data = item.get('raw_data') or {}
        publications = raw_data.get('publications') or []
        if not isinstance(publications, list):
            publications = []

        # Some reviewed observations contain a verified edital link in the
        # normalized field but no connector publication rows.  Keep that
        # evidence available to detail/checkpoint consumers through the same
        # publication ledger, without inventing a document when the link is
        # absent or malformed.  The hash is derived from stable observation
        # fields so repeated syncs remain idempotent and revised links create
        # a new historical publication.
        if not publications:
            edital_link = item.get('link_edital')
            parsed_link = urlsplit(edital_link.strip()) if isinstance(edital_link, str) else None
            if (parsed_link and parsed_link.scheme.lower() in {'http', 'https'}
                    and bool(parsed_link.netloc)):
                edital_number = item.get('edital_numero')
                contest_title = item.get('titulo')
                normalized_link = edital_link.strip()
                # Keep the label sourced from the observation.  The fallback
                # is a reference record and does not claim that the file was
                # downloaded, parsed, or independently certified.
                title = str(edital_number or contest_title or '').strip()
                if not title:
                    return []
                publication_date = item.get('edital_data')
                if isinstance(publication_date, datetime):
                    publication_date = publication_date.isoformat()
                elif isinstance(publication_date, date):
                    publication_date = publication_date.isoformat()
                publication_type = 'edital' if re.search(r'\.pdf(?:$|[?#])', normalized_link, re.IGNORECASE) else 'outro'
                publications = [{
                    'title': title[:500],
                    'publication_type': publication_type,
                    'publication_date': publication_date,
                    'link': normalized_link,
                    'content_hash': build_publication_hash(
                        title, publication_date, normalized_link, publication_type,
                    ),
                    'source': 'concurso.link_edital',
                    'provenance': {
                        'kind': 'normalized_link_fallback',
                        'field': 'link_edital',
                        'reference_only': True,
                    },
                }]

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
        existing_link_rows = {
            link.rstrip('/').casefold(): row
            for row in self.db.scalars(select(ConcursoPublication).where(
                ConcursoPublication.concurso_id == concurso_id,
                ConcursoPublication.link.is_not(None),
            )).all()
            for link in [row.link]
            if isinstance(link, str) and link.strip()
        }

        created: list[dict] = []
        for publication, content_hash, publication_date in candidates:
            title = publication.get('title')
            if content_hash in existing_hashes:
                continue
            link = publication.get('link')
            normalized_link = link.rstrip('/').casefold() if isinstance(link, str) and link.strip() else None
            existing_link = existing_link_rows.get(normalized_link) if normalized_link else None
            incoming_fallback = (publication.get('provenance') or {}).get('kind') == 'normalized_link_fallback'
            existing_fallback = isinstance(existing_link, ConcursoPublication) and (
                (existing_link.raw_data or {}).get('provenance', {}).get('kind') == 'normalized_link_fallback'
            )
            if incoming_fallback and existing_link:
                continue
            if existing_fallback and not incoming_fallback:
                # Converge a reference-only row into the later real extractor
                # observation while retaining the stable row identity.
                existing_link.title = str(title)[:500]
                existing_link.publication_type = publication.get('publication_type')
                existing_link.publication_date = publication_date
                existing_link.content_hash = content_hash
                existing_link.raw_data = jsonable(publication)
                created.append({
                    'title': publication.get('title'), 'publication_type': publication.get('publication_type'),
                    'publication_date': publication.get('publication_date'), 'link': link,
                    'content_hash': content_hash,
                })
                existing_link_rows[normalized_link] = existing_link
                existing_hashes.add(content_hash)
                continue

            values = {
                'concurso_id': concurso_id,
                'title': str(title)[:500],
                'publication_type': publication.get('publication_type'),
                'publication_date': publication_date,
                'link': link,
                'content_hash': content_hash,
                'raw_data': jsonable(publication),
            }

            # The conflict target is explicit.  This makes the operation
            # idempotent under concurrent PostgreSQL workers while allowing
            # unrelated integrity errors (for example a missing title) to
            # propagate and fail the source transaction.
            result = self.db.execute(self._publication_insert_statement(values))
            # Do not infer insertion from rowcount: PostgreSQL drivers may
            # report an indeterminate/zero rowcount for INSERT statements even
            # when the row was committed.  RETURNING gives an atomic signal;
            # no returned id means the unique content hash won a concurrent
            # conflict and the caller must remain idempotent.
            inserted_id = result.scalar_one_or_none()
            if inserted_id is None:
                continue

            created.append({
                'title': publication.get('title'),
                'publication_type': publication.get('publication_type'),
                'publication_date': publication.get('publication_date'),
                'link': publication.get('link'),
                'content_hash': content_hash,
            })
            if normalized_link:
                existing_link_rows[normalized_link] = True
        return created

    def _publication_insert_statement(self, values: dict[str, Any]):
        table = ConcursoPublication.__table__
        bind = self.db.get_bind()
        if bind.dialect.name == 'postgresql':
            return postgresql_insert(table).values(values).on_conflict_do_nothing(
                index_elements=[table.c.concurso_id, table.c.content_hash],
            ).returning(table.c.id)
        if bind.dialect.name == 'sqlite':
            return sqlite_insert(table).values(values).on_conflict_do_nothing(
                index_elements=[table.c.concurso_id, table.c.content_hash],
            ).returning(table.c.id)
        return insert(table).values(values).returning(table.c.id)

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
