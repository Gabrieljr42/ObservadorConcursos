from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.auth import create_access_token, create_refresh_token, exchange_refresh_token, revoke_refresh_token
from app.database import Base, get_db
from app.main import app, get_sync_checkpoint
from app.models import (
    Alert,
    Concurso,
    ConcursoPublication,
    ConcursoVersion,
    FavoriteConcurso,
    Notification,
    RefreshSession,
    Source,
    User,
    UserPreference,
)
from app.schemas import SyncCheckpointOut


def make_db():
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def make_concurso(db, source_id: int) -> Concurso:
    concurso = Concurso(
        source_id=source_id,
        banca='Banca Teste',
        orgao='Órgão Teste',
        titulo='Concurso de Teste',
        cargo='Analista',
        area='Administrativa',
        cidade='Belo Horizonte',
        uf='MG',
        status='Inscrições abertas',
        link_pagina='https://example.com/concurso/1',
        content_hash='concurso-hash',
        raw_data={},
    )
    db.add(concurso)
    db.flush()
    return concurso


def test_checkpoint_is_complete_and_user_scoped():
    db = make_db()
    try:
        source = Source(name='Teste', base_url='https://example.com', list_url='https://example.com/list')
        user = User(name='Usuário 1', email='one@example.com', password_hash='unused')
        other_user = User(name='Usuário 2', email='two@example.com', password_hash='unused')
        db.add_all([source, user, other_user])
        db.flush()
        concurso = make_concurso(db, source.id)
        version = ConcursoVersion(
            concurso_id=concurso.id,
            content_hash='version-hash',
            change_type='created',
            change_summary='Criado',
        )
        publication = ConcursoPublication(
            concurso_id=concurso.id,
            title='Edital',
            publication_type='edital',
            content_hash='publication-hash',
        )
        favorite = FavoriteConcurso(user_id=user.id, concurso_id=concurso.id)
        alert = Alert(user_id=user.id, name='Alerta 1', uf='MG')
        other_alert = Alert(user_id=other_user.id, name='Alerta 2', uf='SP')
        notification = Notification(
            user_id=user.id,
            alert=alert,
            concurso_id=concurso.id,
            title='Atualização',
            message='Nova publicação',
        )
        other_notification = Notification(
            user_id=other_user.id,
            concurso_id=concurso.id,
            title='Privada',
            message='Não vazar',
        )
        preference = UserPreference(user_id=user.id, ufs=['MG'])
        db.add_all([
            version,
            publication,
            favorite,
            alert,
            other_alert,
            notification,
            other_notification,
            preference,
        ])
        db.commit()
        db.refresh(user)

        checkpoint = get_sync_checkpoint(user, db)
        validated = SyncCheckpointOut.model_validate(checkpoint)

        assert len(validated.concursos) == 1
        assert len(validated.publications) == 1
        assert len(validated.versions) == 1
        assert len(validated.recent_updates) == 1
        assert len(validated.my_updates) == 1
        assert [item.user_id for item in validated.favorites] == [user.id]
        assert [item.user_id for item in validated.alerts] == [user.id]
        assert [item.user_id for item in validated.notifications] == [user.id]
        assert validated.preferences is not None
    finally:
        db.close()


def test_checkpoint_route_requires_authentication():
    db = make_db()
    try:
        user = User(name='API User', email='api@example.com', password_hash='unused')
        db.add(user)
        db.commit()
        db.refresh(user)

        def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        assert client.get('/sync/checkpoint').status_code == 401

        response = client.get(
            '/sync/checkpoint',
            headers={'Authorization': f'Bearer {create_access_token(user.id)}'},
        )
        assert response.status_code == 200
        assert response.json()['user']['id'] == user.id
        assert response.json()['favorites'] == []
    finally:
        app.dependency_overrides.pop(get_db, None)
        db.close()


def test_refresh_token_can_be_revoked():
    db = make_db()
    try:
        user = User(name='Refresh User', email='refresh@example.com', password_hash='unused')
        db.add(user)
        db.commit()
        db.refresh(user)
        raw = create_refresh_token(db, user.id, days=1)
        revoke_refresh_token(db, raw)

        with pytest.raises(HTTPException) as exc_info:
            exchange_refresh_token(db, raw)
        assert exc_info.value.status_code == 401
    finally:
        db.close()


def test_refresh_token_slides_expiry_and_is_not_stored_raw():
    db = make_db()
    try:
        user = User(name='Refresh User', email='refresh2@example.com', password_hash='unused')
        db.add(user)
        db.commit()
        db.refresh(user)
        raw = create_refresh_token(db, user.id, days=1)
        session = db.execute(select(RefreshSession)).scalar_one()
        old_expiry = session.expires_at
        access_token, refreshed_user = exchange_refresh_token(db, raw)

        assert access_token.count('.') == 2
        assert refreshed_user.id == user.id
        db.refresh(session)
        assert session.expires_at > old_expiry
        assert session.token_hash != raw
        assert session.expires_at > datetime.utcnow() + timedelta(days=3000)
    finally:
        db.close()
