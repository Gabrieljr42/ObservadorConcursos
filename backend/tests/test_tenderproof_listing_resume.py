from app.tenderproof.continuous_store import ContinuousStore
from app.tenderproof.source_adapter_base import ListingPage
from test_tenderproof_continuous import setup_queue, policy, SOURCE, URL, URL2


def test_next_cycle_resumes_observed_page_deferred_at_deadline(tmp_path):
    queue=setup_queue(tmp_path,cycle_timeout_s=60)
    first=queue.enqueue(1,SOURCE,[URL],now=1000)
    lease=queue.claim(queue.ready_jobs(now=1000)[0],now=1000)
    queue.complete_listing(lease,'official page one',ListingPage(next_urls=[URL2]),now=1001)
    queue.ready_jobs(now=1061)
    assert queue.cycle(first,1)['status']=='partial'
    old_snapshot=queue.snapshot(lease.job_id,1)
    reopened=ContinuousStore(queue.path)
    second=reopened.enqueue(1,SOURCE,[URL],force=True,now=1062)
    with reopened._db() as db:
        rows=db.execute("SELECT resource_key,payload FROM jobs WHERE cycle_id=? AND kind='listing'",(second,)).fetchall()
    assert {r['resource_key'] for r in rows}=={URL,URL2}
    assert reopened.snapshot(lease.job_id,1)==old_snapshot
    assert reopened.cycle(first,1)['status']=='partial'


def test_successful_new_attempt_prevents_resurrecting_old_deferral(tmp_path):
    queue=setup_queue(tmp_path,cycle_timeout_s=60)
    first=queue.enqueue(1,SOURCE,[URL2],now=1000)
    queue.ready_jobs(now=1061)
    second=queue.enqueue(1,SOURCE,[URL],force=True,now=1062)
    for now in (1063,1064):
        lease=queue.claim(queue.ready_jobs(now=now)[0],now=now)
        queue.complete_listing(lease,'terminal',ListingPage(terminal_evidence='explicit terminal'),now=now)
    assert queue.cycle(second,1)['status']=='completed'
    third=queue.enqueue(1,SOURCE,[URL],force=True,now=1065)
    jobs=queue.cycle(third,1)['jobs']
    assert len(jobs)==1
    assert queue.claim(jobs[0]['job_id'],now=1065).payload=={'url':URL}
    assert queue.cycle(first,1)['status']=='partial'


def test_continuation_is_owner_scoped_and_keeps_current_page_budget(tmp_path):
    queue=setup_queue(tmp_path,cycle_timeout_s=60)
    queue.configure(2,SOURCE,policy(cycle_timeout_s=60),now=1000)
    own=queue.enqueue(1,SOURCE,[URL2],now=1000)
    queue.enqueue(2,SOURCE,[URL+'?page=99'],now=1000)
    queue.ready_jobs(now=1061)
    queue.configure(1,SOURCE,policy(cycle_timeout_s=60,max_listing_pages=1),now=1062)
    second=queue.enqueue(1,SOURCE,[URL],force=True,now=1062)
    state=queue.cycle(second,1)
    assert len(state['jobs'])==1 and 'listing_page_limit' in state['reasons']
    lease=queue.claim(state['jobs'][0]['job_id'],now=1062)
    assert lease.payload=={'url':URL2,'continued_from_cycle':own}


def test_small_page_budget_advances_through_unqueued_published_links(tmp_path):
    queue=setup_queue(tmp_path,max_listing_pages=1)
    page3=URL+'?page=3'
    for now,expected,next_url in [(1000,URL,URL2),(1002,URL2,page3),(1004,page3,None)]:
        cycle=queue.enqueue(1,SOURCE,[URL],force=True,now=now)
        jobs=queue.cycle(cycle,1)['jobs']
        assert len(jobs)==1
        lease=queue.claim(jobs[0]['job_id'],now=now)
        assert lease.payload['url']==expected
        page=ListingPage(next_urls=[next_url]) if next_url else ListingPage(terminal_evidence='explicit end')
        queue.complete_listing(lease,'observed page '+expected,page,now=now+1)
        assert queue.cycle(cycle,1)['status']=='partial'
    # Once the backlog was actually read, periodic discovery returns to seeds.
    final=queue.enqueue(1,SOURCE,[URL],force=True,now=1006)
    job=queue.cycle(final,1)['jobs'][0]
    assert queue.claim(job['job_id'],now=1006).payload=={'url':URL}


def test_never_queued_links_from_another_owner_are_not_imported(tmp_path):
    queue=setup_queue(tmp_path,max_listing_pages=1)
    queue.configure(2,SOURCE,policy(max_listing_pages=1),now=1000)
    other=queue.enqueue(2,SOURCE,[URL],now=1000)
    job=queue.cycle(other,2)['jobs'][0]
    lease=queue.claim(job['job_id'],now=1000)
    queue.complete_listing(lease,'other owner evidence',ListingPage(next_urls=[URL2]),now=1001)
    own=queue.enqueue(1,SOURCE,[URL],now=1002)
    own_job=queue.cycle(own,1)['jobs'][0]
    assert queue.claim(own_job['job_id'],now=1002).payload=={'url':URL}
