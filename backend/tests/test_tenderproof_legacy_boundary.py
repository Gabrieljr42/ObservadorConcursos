"""Disabled legacy collection must not reach a database, queue or connector."""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app import main, services, tasks


@pytest.fixture(autouse=True)
def disabled(monkeypatch):
    for module in (main, services, tasks):
        monkeypatch.setattr(module, 'get_settings', lambda: SimpleNamespace(legacy_crawler_enabled=False))


class NoDatabase:
    def __getattr__(self, name):
        raise AssertionError(f'database touched: {name}')


@pytest.mark.parametrize('endpoint,args', [
    (main.enqueue_crawl_all, ()), (main.run_crawl_all_sync, ()),
    (main.enqueue_crawl_all_alias, ()), (main.run_crawl_all_sync_alias, ()),
    (main.enqueue_crawl, (1,)), (main.run_crawl_sync, (1,)),
])
def test_manual_routes_reject_before_any_work(endpoint, args, monkeypatch):
    monkeypatch.setattr(main, 'acquire_crawl_all_lock', lambda: pytest.fail('lock acquired'))
    with pytest.raises(HTTPException) as error:
        endpoint(*args, db=NoDatabase())
    assert error.value.status_code == 409


@pytest.mark.parametrize('task,args', [(tasks.crawl_source, (1,)), (tasks.crawl_active_sources, ()), (tasks.scheduled_crawl_active_sources, ())])
def test_queued_legacy_tasks_are_disabled(task, args, monkeypatch):
    monkeypatch.setattr(tasks, 'SessionLocal', lambda: pytest.fail('database opened'))
    monkeypatch.setattr(tasks, 'acquire_crawl_all_lock', lambda *a: pytest.fail('lock acquired'))
    assert task.run(*args)['status'] == 'disabled'


def test_direct_service_cannot_bypass_guard():
    with pytest.raises(ValueError, match='Coletor antigo desativado'):
        services.CrawlService(NoDatabase()).crawl_source(1)


def test_explicit_legacy_installation_can_pass_route_guard(monkeypatch):
    monkeypatch.setattr(main, 'get_settings', lambda: SimpleNamespace(legacy_crawler_enabled=True))
    main.require_legacy_crawler()
