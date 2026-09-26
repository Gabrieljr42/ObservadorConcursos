from types import SimpleNamespace
import pytest
from app.tenderproof import service

def test_wait_obtains_available_lease_without_closing_driver(monkeypatch):
    tokens=iter([None,None,'owned'])
    released=[];closed=[]
    store=SimpleNamespace(acquire_execution_lease=lambda **kw:next(tokens),
        release_execution_lease=lambda token:released.append(token))
    driver=SimpleNamespace(close=lambda:closed.append(True))
    monkeypatch.setattr(service.time,'sleep',lambda _:None)
    lease=service._ExecutionLease(store,driver,wait_s=1)
    lease.check();lease.release()
    assert released==['owned'] and not closed

def test_wait_deadline_never_releases_someone_elses_lease(monkeypatch):
    clock=[0.0];closed=[];released=[]
    monkeypatch.setattr(service.time,'monotonic',lambda:clock[0])
    monkeypatch.setattr(service.time,'sleep',lambda delay:clock.__setitem__(0,clock[0]+delay))
    store=SimpleNamespace(acquire_execution_lease=lambda **kw:None,
        release_execution_lease=lambda token:released.append(token))
    with pytest.raises(service.TenderProofBusy):
        service._ExecutionLease(store,SimpleNamespace(close=lambda:closed.append(True)),wait_s=1)
    assert clock[0]==1 and closed==[True] and not released
