from concurrent.futures import ThreadPoolExecutor
import pytest
from app.tenderproof.solari_budget import SolariBudget, BudgetExceeded


def test_shared_concurrent_reservations_cannot_exceed_limit(tmp_path):
    path = tmp_path / 'budget.sqlite'
    budget = SolariBudget(path, limit_usd='0.05', authority='test authorization')
    def reserve(_):
        ledger = SolariBudget(path, limit_usd='0.05', authority='test authorization')
        try:
            return ledger.reserve('browser', maximum_seconds=60, hourly_usd='0.15', tariff='fixture')
        except BudgetExceeded:
            return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        ids = [r for r in pool.map(reserve, range(20)) if r]
    assert len(ids) == 5
    assert budget.snapshot()['reserved_usd'] == .05
    budget.created(ids[0], 'remote-1')
    budget.closed('remote-1')
    with pytest.raises(BudgetExceeded):
        reserve_id = budget.reserve('sandbox', maximum_seconds=60, hourly_usd='.086', tariff='fixture')
    assert budget.snapshot()['confirmed_billed_usd'] is None


def test_restart_retains_uncertain_creates_and_rejects_changed_authority(tmp_path):
    path = tmp_path / 'budget.sqlite'
    a = SolariBudget(path, limit_usd='20', authority='user:20')
    a.reserve('browser', maximum_seconds=3600, hourly_usd='.15', tariff='fixture')
    b = SolariBudget(path, limit_usd='20', authority='user:20')
    assert b.snapshot()['reserved_usd'] == .15
    with pytest.raises(ValueError):
        SolariBudget(path, limit_usd='25', authority='user:20')


@pytest.mark.parametrize('seconds,rate', [(0,'.15'),(-1,'.15'),('NaN','.15'),(60,'Infinity')])
def test_invalid_estimates_rejected(tmp_path, seconds, rate):
    b = SolariBudget(tmp_path/'budget.sqlite', limit_usd='20', authority='test')
    with pytest.raises(ValueError):
        b.reserve('browser', maximum_seconds=seconds, hourly_usd=rate, tariff='test')


def test_browser_reserves_before_create_and_requires_verified_lifetime(tmp_path, monkeypatch):
    import asyncio
    from app.tenderproof.solari_adapter import SolariBrowserAdapter, SolariConfig
    monkeypatch.setenv('TENDERPROOF_SOLARI_BUDGET_PATH', str(tmp_path/'shared.sqlite'))
    monkeypatch.setenv('TENDERPROOF_SOLARI_BUDGET_USD', '.15')
    monkeypatch.setenv('TENDERPROOF_SOLARI_BUDGET_AUTHORITY', 'fixture')
    monkeypatch.delenv('TENDERPROOF_SOLARI_BROWSER_MAX_LIFETIME_SECONDS', raising=False)
    a = SolariBrowserAdapter(config=SolariConfig(api_key='fake'))
    calls = []
    class Client:
        async def launch(self, **kwargs):
            calls.append(kwargs)
            raise RuntimeError('ambiguous create')
    with pytest.raises(ValueError, match='duração máxima'):
        asyncio.run(a._budgeted_launch(Client()))
    assert not calls
    monkeypatch.setenv('TENDERPROOF_SOLARI_BROWSER_MAX_LIFETIME_SECONDS', '3600')
    with pytest.raises(RuntimeError, match='ambiguous'):
        asyncio.run(a._budgeted_launch(Client()))
    with pytest.raises(BudgetExceeded):
        asyncio.run(a._budgeted_launch(Client()))
    assert len(calls) == 1
    assert a._budget.snapshot()['reserved_usd'] == .15


def test_sandbox_uses_same_reservations_before_http(tmp_path, monkeypatch):
    import httpx
    from app.tenderproof.processing import ProcessingLimits
    from app.tenderproof.processing_solari import SolariSandboxProcessor
    path = tmp_path/'shared.sqlite'
    monkeypatch.setenv('TENDERPROOF_SOLARI_BUDGET_PATH', str(path))
    monkeypatch.setenv('TENDERPROOF_SOLARI_BUDGET_USD', '.01')
    monkeypatch.setenv('TENDERPROOF_SOLARI_BUDGET_AUTHORITY', 'fixture')
    ledger = SolariBudget(path, limit_usd='.01', authority='fixture')
    ledger.reserve('browser', maximum_seconds=60, hourly_usd='.15', tariff='fixture')
    calls = []
    p = SolariSandboxProcessor('fake', live_authorized=True,
        http=httpx.Client(transport=httpx.MockTransport(lambda request: calls.append(request))))
    with pytest.raises(BudgetExceeded):
        p.create('test', ProcessingLimits())
    assert not calls
