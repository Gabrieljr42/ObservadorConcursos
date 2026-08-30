from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Source(Base):
    __tablename__ = 'sources'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    base_url: Mapped[str] = mapped_column(Text, nullable=False)
    list_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default='html_list')
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    frequency_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=360)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    concursos: Mapped[list['Concurso']] = relationship(
        back_populates='source',
        cascade='all, delete-orphan',
    )
    runs: Mapped[list['CrawlRun']] = relationship(
        back_populates='source',
        cascade='all, delete-orphan',
        order_by='desc(CrawlRun.started_at)',
    )


class Concurso(Base):
    __tablename__ = 'concursos'
    __table_args__ = (
        UniqueConstraint('source_id', 'link_pagina', name='uq_concursos_source_link_pagina'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey('sources.id', ondelete='CASCADE'), nullable=False, index=True)

    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    banca: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    orgao: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    modalidade: Mapped[str | None] = mapped_column(String(150), nullable=True)
    cargo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    area: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    cidade: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    uf: Mapped[str | None] = mapped_column(String(2), nullable=True, index=True)
    status: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)

    vagas: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salario_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    salario_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    escolaridade: Mapped[str | None] = mapped_column(String(120), nullable=True)
    taxa: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    prova_data: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    edital_numero: Mapped[str | None] = mapped_column(String(80), nullable=True)
    edital_data: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    inscricao_inicio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    inscricao_fim: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    link_pagina: Mapped[str] = mapped_column(Text, nullable=False)
    link_edital: Mapped[str | None] = mapped_column(Text, nullable=True)
    link_inscricao: Mapped[str | None] = mapped_column(Text, nullable=True)

    resumo: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    edital_pdf_text_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    edital_pdf_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    edital_pdf_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_extracted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    source: Mapped[Source] = relationship(back_populates='concursos')
    versions: Mapped[list['ConcursoVersion']] = relationship(
        back_populates='concurso',
        cascade='all, delete-orphan',
        order_by='desc(ConcursoVersion.captured_at)',
    )
    publications: Mapped[list['ConcursoPublication']] = relationship(
        back_populates='concurso',
        cascade='all, delete-orphan',
        order_by='desc(ConcursoPublication.publication_date)',
    )


class ConcursoVersion(Base):
    __tablename__ = 'concurso_versions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    concurso_id: Mapped[int] = mapped_column(ForeignKey('concursos.id', ondelete='CASCADE'), nullable=False, index=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    change_type: Mapped[str] = mapped_column(String(50), nullable=False, default='updated', index=True)
    changed_fields: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_data_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    concurso: Mapped[Concurso] = relationship(back_populates='versions')




class ConcursoPublication(Base):
    __tablename__ = 'concurso_publications'
    __table_args__ = (
        UniqueConstraint('concurso_id', 'content_hash', name='uq_concurso_publication_hash'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    concurso_id: Mapped[int] = mapped_column(ForeignKey('concursos.id', ondelete='CASCADE'), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    publication_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    publication_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    link: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    concurso: Mapped[Concurso] = relationship(back_populates='publications')


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    preferences: Mapped['UserPreference | None'] = relationship(
        back_populates='user',
        cascade='all, delete-orphan',
        uselist=False,
    )
    favorites: Mapped[list['FavoriteConcurso']] = relationship(
        back_populates='user',
        cascade='all, delete-orphan',
    )
    alerts: Mapped[list['Alert']] = relationship(
        back_populates='user',
        cascade='all, delete-orphan',
    )
    notifications: Mapped[list['Notification']] = relationship(
        back_populates='user',
        cascade='all, delete-orphan',
    )
    refresh_sessions: Mapped[list['RefreshSession']] = relationship(
        back_populates='user',
        cascade='all, delete-orphan',
    )


class UserPreference(Base):
    __tablename__ = 'user_preferences'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    areas: Mapped[list | None] = mapped_column(JSON, nullable=True)
    ufs: Mapped[list | None] = mapped_column(JSON, nullable=True)
    cidades: Mapped[list | None] = mapped_column(JSON, nullable=True)
    bancas: Mapped[list | None] = mapped_column(JSON, nullable=True)
    cargo_keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)
    only_open: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notification_channels: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates='preferences')


class FavoriteConcurso(Base):
    __tablename__ = 'favorite_concursos'
    __table_args__ = (
        UniqueConstraint('user_id', 'concurso_id', name='uq_favorite_user_concurso'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    concurso_id: Mapped[int] = mapped_column(ForeignKey('concursos.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates='favorites')
    concurso: Mapped[Concurso] = relationship()


class Alert(Base):
    __tablename__ = 'alerts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    uf: Mapped[str | None] = mapped_column(String(2), nullable=True, index=True)
    cidade: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    banca: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    area: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    cargo_keyword: Mapped[str | None] = mapped_column(String(150), nullable=True)
    status: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    only_open: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates='alerts')
    notifications: Mapped[list['Notification']] = relationship(back_populates='alert')


class Notification(Base):
    __tablename__ = 'notifications'
    __table_args__ = (
        UniqueConstraint('user_id', 'alert_id', 'concurso_id', 'notification_type', name='uq_notification_user_alert_concurso_type'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    alert_id: Mapped[int | None] = mapped_column(ForeignKey('alerts.id', ondelete='SET NULL'), nullable=True, index=True)
    concurso_id: Mapped[int | None] = mapped_column(ForeignKey('concursos.id', ondelete='CASCADE'), nullable=True, index=True)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False, default='alert_match')
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user: Mapped[User] = relationship(back_populates='notifications')
    alert: Mapped[Alert | None] = relationship(back_populates='notifications')
    concurso: Mapped[Concurso | None] = relationship()


class RefreshSession(Base):
    __tablename__ = 'refresh_sessions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship(back_populates='refresh_sessions')


class CrawlRun(Base):
    __tablename__ = 'crawl_runs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey('sources.id', ondelete='CASCADE'), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default='success', index=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    browser_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    candidates_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    candidates_rejected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    inserted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unchanged: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    versions_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notifications_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    error_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnostics_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    source: Mapped[Source] = relationship(back_populates='runs')
