"""TenderProof review ledger; canonical contests remain in app.models."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PublicationProposal(Base):
    __tablename__ = "tenderproof_publication_proposals"
    __table_args__ = (UniqueConstraint("owner_user_id", "run_id", "concurso_id", "proposal_hash", name="uq_tp_proposal_review"),)

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    run_id: Mapped[str] = mapped_column(String(128), nullable=False)
    concurso_id: Mapped[int | None] = mapped_column(ForeignKey("concursos.id"), nullable=True)
    proposal_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    state: Mapped[str] = mapped_column(String(30), default="proposed", nullable=False)
    approved_fields: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    # One durable application per observation/target, including no-op applications.
    applied_observation: Mapped[str | None] = mapped_column(String(64), unique=True)
    version_id: Mapped[int | None] = mapped_column(ForeignKey("concurso_versions.id"))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime)
    result: Mapped[dict | None] = mapped_column(JSON)
    rollback_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    rollback_at: Mapped[datetime | None] = mapped_column(DateTime)
    rollback_reason: Mapped[str | None] = mapped_column(Text)
    rollback_version_id: Mapped[int | None] = mapped_column(ForeignKey("concurso_versions.id"))
    # Rejection is a terminal review decision, distinct from rollback of an
    # already-applied publication.  These fields are additive audit metadata.
    rejected_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class PublicationOutbox(Base):
    __tablename__ = "tenderproof_publication_outbox"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("concurso_versions.id"), unique=True, nullable=False)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("tenderproof_publication_proposals.id"), nullable=False)
    state: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


def ensure_publication_schema(engine):
    """Additive, repeatable migration; does not alter or delete canonical data."""
    from sqlalchemy import inspect
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    inspector = inspect(engine)
    if PublicationProposal.__tablename__ in inspector.get_table_names():
        existing_columns = {column["name"] for column in inspector.get_columns(PublicationProposal.__tablename__)}
        # PostgreSQL does not provide a DATETIME type; SQLite accepts both
        # names loosely. Keep the migration additive and portable across the
        # pilot's PostgreSQL volume and the local SQLite operational store.
        timestamp_type = "TIMESTAMP" if engine.dialect.name == "postgresql" else "DATETIME"
        additive = {
            "rejected_by": "INTEGER",
            "rejected_at": timestamp_type,
            "rejection_reason": "TEXT",
        }
        missing = {name: sql_type for name, sql_type in additive.items() if name not in existing_columns}
        if missing:
            with engine.begin() as connection:
                for name, sql_type in missing.items():
                    connection.exec_driver_sql(
                        f"ALTER TABLE {PublicationProposal.__tablename__} ADD COLUMN {name} {sql_type}"
                    )
        column = next(c for c in inspector.get_columns(PublicationProposal.__tablename__) if c["name"] == "concurso_id")
        if not column["nullable"]:
            # SQLite batch replacement requires temporarily disabling FK checks
            # on this maintenance connection, then checking the preserved ledger.
            with engine.connect() as connection:
                sqlite = engine.dialect.name == "sqlite"
                foreign_keys = connection.exec_driver_sql("PRAGMA foreign_keys").scalar() if sqlite else None
                connection.commit()
                if sqlite:
                    connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
                    connection.commit()
                try:
                    with connection.begin():
                        if sqlite:
                            connection.exec_driver_sql("BEGIN IMMEDIATE")
                        operations = Operations(MigrationContext.configure(connection))
                        with operations.batch_alter_table(PublicationProposal.__tablename__) as batch:
                            batch.alter_column("concurso_id", existing_type=Integer(), nullable=True)
                        if sqlite and connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall():
                            raise RuntimeError("TenderProof: migration would violate foreign keys")
                finally:
                    if sqlite:
                        connection.exec_driver_sql("PRAGMA foreign_keys=" + str(int(foreign_keys)))
                        connection.commit()
    Base.metadata.create_all(engine, tables=[PublicationProposal.__table__, PublicationOutbox.__table__, CanonicalIdentity.__table__])


class CanonicalIdentity(Base):
    """Unique reservations shared across reviewers/sources; never title similarity."""
    __tablename__ = "tenderproof_canonical_identities"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    concurso_id: Mapped[int] = mapped_column(ForeignKey("concursos.id"), nullable=False)
    reason: Mapped[str] = mapped_column(String(80), nullable=False)
    evidence: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
