from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import RefreshSession, User

security = HTTPBearer(auto_error=False)


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode('ascii')


def _b64url_decode(value: str) -> bytes:
    padding = '=' * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str) -> str:
    if len(password) < 6:
        raise ValueError('A senha deve ter pelo menos 6 caracteres')
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 210_000)
    return f'pbkdf2_sha256$210000${_b64url_encode(salt)}${_b64url_encode(digest)}'


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations_raw, salt_raw, digest_raw = password_hash.split('$', 3)
        if algorithm != 'pbkdf2_sha256':
            return False
        iterations = int(iterations_raw)
        salt = _b64url_decode(salt_raw)
        expected = _b64url_decode(digest_raw)
        actual = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def _jwt_secret() -> bytes:
    settings = get_settings()
    return settings.secret_key.encode('utf-8')


def create_access_token(subject: str | int, expires_delta: timedelta | None = None) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + (expires_delta or timedelta(minutes=get_settings().access_token_expire_minutes))
    header = {'alg': 'HS256', 'typ': 'JWT'}
    payload = {
        'sub': str(subject),
        'iat': int(now.timestamp()),
        'exp': int(expires_at.timestamp()),
    }
    signing_input = '.'.join([
        _b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8')),
        _b64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8')),
    ])
    signature = hmac.new(_jwt_secret(), signing_input.encode('ascii'), hashlib.sha256).digest()
    return f'{signing_input}.{_b64url_encode(signature)}'


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header_raw, payload_raw, signature_raw = token.split('.', 2)
        signing_input = f'{header_raw}.{payload_raw}'
        expected_signature = hmac.new(_jwt_secret(), signing_input.encode('ascii'), hashlib.sha256).digest()
        provided_signature = _b64url_decode(signature_raw)
        if not hmac.compare_digest(expected_signature, provided_signature):
            raise ValueError('Invalid signature')
        payload = json.loads(_b64url_decode(payload_raw).decode('utf-8'))
        if int(payload.get('exp', 0)) < int(time.time()):
            raise ValueError('Expired token')
        return payload
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token inválido ou expirado',
            headers={'WWW-Authenticate': 'Bearer'},
        ) from exc


def create_refresh_token(db: Session, user_id: int, *, days: int = 3650) -> str:
    raw = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw.encode('utf-8')).hexdigest()
    now = datetime.utcnow()
    session = RefreshSession(
        user_id=user_id,
        token_hash=token_hash,
        created_at=now,
        expires_at=now + timedelta(days=days),
    )
    db.add(session)
    db.commit()
    return raw


def exchange_refresh_token(db: Session, raw_token: str) -> tuple[str, User]:
    token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    session = db.execute(
        select(RefreshSession).where(RefreshSession.token_hash == token_hash)
    ).scalar_one_or_none()
    now = datetime.utcnow()
    if session is None or session.revoked_at is not None or session.expires_at <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Refresh token inválido ou expirado')

    # Keep a remembered device eligible for a long-lived session after a successful refresh.
    session.expires_at = now + timedelta(days=3650)
    db.commit()
    user = db.execute(select(User).where(User.id == session.user_id)).scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Usuário inválido ou inativo')
    return create_access_token(user.id), user


def revoke_refresh_token(db: Session, raw_token: str) -> None:
    token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    session = db.execute(
        select(RefreshSession).where(RefreshSession.token_hash == token_hash)
    ).scalar_one_or_none()
    if session is not None and session.revoked_at is None:
        session.revoked_at = datetime.utcnow()
        db.commit()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != 'bearer':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Autenticação necessária',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    payload = decode_access_token(credentials.credentials)
    user_id_raw = payload.get('sub')
    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token inválido') from exc

    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Usuário inválido ou inativo')
    return user
