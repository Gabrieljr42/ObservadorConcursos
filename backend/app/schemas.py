from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, HttpUrl


class SourceCreate(BaseModel):
    name: str
    base_url: HttpUrl
    list_url: HttpUrl | None = None
    source_type: str = 'html_list'
    active: bool = True
    frequency_minutes: int = 360


class SourceOut(BaseModel):
    id: int
    name: str
    base_url: str
    list_url: str | None
    source_type: str
    active: bool
    frequency_minutes: int
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class ConcursoOut(BaseModel):
    id: int
    source_id: int
    external_id: str | None
    banca: str
    orgao: str | None
    titulo: str
    modalidade: str | None
    cargo: str | None
    area: str | None
    cidade: str | None
    uf: str | None
    status: str | None
    vagas: int | None
    salario_min: Decimal | None
    salario_max: Decimal | None
    escolaridade: str | None
    taxa: Decimal | None
    prova_data: datetime | None
    edital_numero: str | None
    edital_data: datetime | None
    inscricao_inicio: datetime | None
    inscricao_fim: datetime | None
    link_pagina: str
    link_edital: str | None
    link_inscricao: str | None
    resumo: str | None
    raw_data: dict[str, Any] | None
    edital_pdf_text_hash: str | None
    edital_pdf_pages: int | None
    edital_pdf_excerpt: str | None
    pdf_extracted_at: datetime | None
    content_hash: str
    fetched_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class ConcursoVersionOut(BaseModel):
    id: int
    concurso_id: int
    content_hash: str
    change_type: str
    changed_fields: dict[str, Any] | None
    change_summary: str | None
    raw_data_snapshot: dict[str, Any] | None
    captured_at: datetime

    model_config = {'from_attributes': True}


class ConcursoPublicationOut(BaseModel):
    id: int
    concurso_id: int
    title: str
    publication_type: str | None
    publication_date: datetime | None
    link: str | None
    content_hash: str
    raw_data: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class UpdateOut(BaseModel):
    id: int
    concurso_id: int
    change_type: str
    change_summary: str | None
    captured_at: datetime
    titulo: str
    banca: str
    orgao: str | None
    cidade: str | None
    uf: str | None
    area: str | None
    status: str | None


class UserRegister(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class AuthToken(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = 'bearer'
    user: UserOut


class RefreshTokenIn(BaseModel):
    refresh_token: str


class UserPreferenceIn(BaseModel):
    areas: list[str] | None = None
    ufs: list[str] | None = None
    cidades: list[str] | None = None
    bancas: list[str] | None = None
    cargo_keywords: list[str] | None = None
    only_open: bool = True
    notification_channels: list[str] | None = None


class UserPreferenceOut(UserPreferenceIn):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class FavoriteOut(BaseModel):
    id: int
    user_id: int
    concurso_id: int
    created_at: datetime
    concurso: ConcursoOut

    model_config = {'from_attributes': True}


class AlertCreate(BaseModel):
    name: str
    uf: str | None = None
    cidade: str | None = None
    banca: str | None = None
    area: str | None = None
    cargo_keyword: str | None = None
    status: str | None = None
    only_open: bool = True
    active: bool = True


class AlertUpdate(BaseModel):
    name: str | None = None
    uf: str | None = None
    cidade: str | None = None
    banca: str | None = None
    area: str | None = None
    cargo_keyword: str | None = None
    status: str | None = None
    only_open: bool | None = None
    active: bool | None = None


class AlertOut(BaseModel):
    id: int
    user_id: int
    name: str
    active: bool
    uf: str | None
    cidade: str | None
    banca: str | None
    area: str | None
    cargo_keyword: str | None
    status: str | None
    only_open: bool
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class NotificationOut(BaseModel):
    id: int
    user_id: int
    alert_id: int | None
    concurso_id: int | None
    notification_type: str
    title: str
    message: str
    read_at: datetime | None
    created_at: datetime
    concurso: ConcursoOut | None = None

    model_config = {'from_attributes': True}


class AlertRunResult(BaseModel):
    processed_alerts: int
    created_notifications: int


class CrawlRunOut(BaseModel):
    id: int
    source_id: int
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None
    status: str
    http_status: int | None
    browser_used: bool
    candidates_found: int
    candidates_rejected: int
    processed: int
    inserted: int
    updated: int
    unchanged: int
    versions_created: int
    notifications_created: int
    error_type: str | None
    error_message: str | None
    diagnostics_payload: dict[str, Any] | None

    model_config = {'from_attributes': True}


class SourceMasterSeedOut(BaseModel):
    total_master_sources: int
    created: int
    updated: int
    unchanged: int


class SyncCheckpointOut(BaseModel):
    generated_at: datetime
    user: UserOut
    preferences: UserPreferenceOut | None
    concursos: list[ConcursoOut]
    publications: list[ConcursoPublicationOut]
    versions: list[ConcursoVersionOut]
    recent_updates: list[UpdateOut]
    my_updates: list[UpdateOut]
    favorites: list[FavoriteOut]
    alerts: list[AlertOut]
    notifications: list[NotificationOut]
