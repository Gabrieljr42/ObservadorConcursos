from __future__ import annotations

import uuid

import redis

from app.config import get_settings


CRAWL_ALL_LOCK_KEY = 'observador:crawl_all_lock'
CRAWL_ALL_LOCK_TIMEOUT_SECONDS = 12 * 60 * 60

_RELEASE_LOCK_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
end
return 0
"""

_REFRESH_LOCK_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('expire', KEYS[1], ARGV[2])
end
return 0
"""


class CrawlLockUnavailable(RuntimeError):
    """Redis could not be reached, so a safe distributed lock is unavailable."""


def get_redis_client() -> redis.Redis:
    settings = get_settings()
    return redis.Redis.from_url(
        settings.celery_broker_url,
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=1,
    )


def acquire_crawl_all_lock(existing_token: str | None = None) -> str | None:
    """Acquire the global crawl lock, or return None when another crawl owns it.

    ``existing_token`` is used by the enqueue endpoint to transfer its
    reservation to the Celery task without releasing the lock in between.
    """
    client = get_redis_client()
    token = existing_token or uuid.uuid4().hex
    try:
        if existing_token:
            refreshed = client.eval(
                _REFRESH_LOCK_SCRIPT,
                1,
                CRAWL_ALL_LOCK_KEY,
                existing_token,
                CRAWL_ALL_LOCK_TIMEOUT_SECONDS,
            )
            if refreshed:
                return existing_token

        acquired = client.set(
            CRAWL_ALL_LOCK_KEY,
            token,
            nx=True,
            ex=CRAWL_ALL_LOCK_TIMEOUT_SECONDS,
        )
        return token if acquired else None
    except redis.RedisError as exc:
        raise CrawlLockUnavailable('Não foi possível acessar o lock distribuído do crawl-all') from exc


def refresh_crawl_all_lock(token: str) -> bool:
    client = get_redis_client()
    try:
        return bool(client.eval(
            _REFRESH_LOCK_SCRIPT,
            1,
            CRAWL_ALL_LOCK_KEY,
            token,
            CRAWL_ALL_LOCK_TIMEOUT_SECONDS,
        ))
    except redis.RedisError as exc:
        raise CrawlLockUnavailable('Não foi possível renovar o lock distribuído do crawl-all') from exc


def release_crawl_all_lock(token: str) -> None:
    client = get_redis_client()
    try:
        client.eval(_RELEASE_LOCK_SCRIPT, 1, CRAWL_ALL_LOCK_KEY, token)
    except redis.RedisError as exc:
        raise CrawlLockUnavailable('Não foi possível liberar o lock distribuído do crawl-all') from exc
