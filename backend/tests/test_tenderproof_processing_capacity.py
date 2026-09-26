import pytest
from app.tenderproof import processing as p

class FakeService:
    def __init__(self): self.enqueues=0; self.calls=[]; self.cancelled=[]; self.busy=1
    def enqueue(self,owner,content,limits):
        self.enqueues+=1
        return {'id':'same-job'}
    def execute(self,job,owner):
        self.calls.append((job,owner))
        if self.busy:
            self.busy-=1
            raise p.ProcessingError('concurrency_limit')
        return {'state':'succeeded'}
    def result(self,job,owner):return {'pages':[{'page_number':1,'text':'Edital'}],'total_pages':1}
    def cancel(self,job,owner):self.cancelled.append((job,owner))

def test_capacity_wait_resumes_same_job_without_duplicate_enqueue(monkeypatch):
    service=FakeService()
    monkeypatch.setattr(p,'get_processing_service',lambda:service)
    monkeypatch.setattr(p.time,'sleep',lambda _:None)
    result=p.extract_pages_isolated(b'%PDF-1.4',artifact_id='art',owner_id='7',capacity_wait_s=1)
    assert service.enqueues==1 and service.calls==[('same-job','7')]*2
    assert not service.cancelled and result[1:4]==(1,1,False)

def test_exhausted_capacity_cancels_only_own_unstarted_job(monkeypatch):
    service=FakeService()
    monkeypatch.setattr(p,'get_processing_service',lambda:service)
    with pytest.raises(p.ProcessingError,match='concurrency_limit'):
        p.extract_pages_isolated(b'%PDF-1.4',artifact_id='art',owner_id='7')
    assert service.enqueues==1 and service.cancelled==[('same-job','7')]
