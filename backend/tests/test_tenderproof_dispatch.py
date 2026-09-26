import pytest
from app.tenderproof import continuous_tasks as tasks


class Engine:
    def __init__(self,status='succeeded'):
        self.status=status;self.limits=[]
    def schedule_due(self):return ['cycle']
    def ready_jobs(self,*,limit):
        self.limits.append(limit);return ['next'][:limit]
    def process_job(self,job):return {'status':self.status}


def configure(monkeypatch,status='succeeded'):
    engine=Engine(status);sent=[]
    monkeypatch.setattr(tasks,'ContinuousEngine',lambda:engine)
    monkeypatch.setattr(tasks,'continuous_enabled',lambda:True)
    monkeypatch.setattr(tasks.continuous_job,'apply_async',lambda **kw:sent.append(kw))
    return engine,sent


def test_tick_respects_single_acquisition_capacity(monkeypatch):
    engine,sent=configure(monkeypatch)
    assert tasks.continuous_tick.run()['dispatched']==1
    assert engine.limits==[1] and len(sent)==1


@pytest.mark.parametrize('status',['succeeded','failed','retry_or_failed'])
def test_finished_attempt_dispatches_next_ready_work(monkeypatch,status):
    engine,sent=configure(monkeypatch,status)
    assert tasks.continuous_job.run('current')=={'status':status}
    assert sent==[{'args':['next'],'queue':'tenderproof','countdown':1}]


@pytest.mark.parametrize('status',['acquisition_busy','not_claimed','lease_lost','paused','operator_revoked'])
def test_duplicate_or_busy_delivery_cannot_amplify_dispatch(monkeypatch,status):
    _,sent=configure(monkeypatch,status)
    tasks.continuous_job.run('current');assert sent==[]


def test_broker_failure_preserves_completed_result(monkeypatch):
    configure(monkeypatch)
    def fail(**kw):raise ConnectionError('broker unavailable')
    monkeypatch.setattr(tasks.continuous_job,'apply_async',fail)
    assert tasks.continuous_job.run('current')=={'status':'succeeded'}
