"""Celery deliveries are hints; the SQLite queue survives lost broker messages."""
from celery import shared_task

from app.tenderproof.continuous import ContinuousEngine, continuous_enabled
from app.tenderproof.processing import get_processing_service


@shared_task(name="app.tenderproof.continuous.tick", ignore_result=True)
def continuous_tick():
    if not continuous_enabled():
        return {"status":"disabled"}
    recovered_processing = get_processing_service().recover_local()
    engine=ContinuousEngine()
    cycles=engine.schedule_due()
    dispatched=0
    failures=0
    # Acquisition has a deployment-wide capacity of one. Dispatching one per
    # source concurrently only creates busy retries and delays useful work.
    for job_id in engine.ready_jobs(limit=1):
        try:
            # No "sent" flag: a lost delivery is eligible on the next tick.
            continuous_job.apply_async(args=[job_id],queue="tenderproof")
            dispatched+=1
        except Exception:
            failures+=1
    return {"cycles":len(cycles),"dispatched":dispatched,"dispatch_failures":failures,
            "recovered_processing":recovered_processing}


@shared_task(name="app.tenderproof.continuous.job", acks_late=True, reject_on_worker_lost=True,
             ignore_result=True, soft_time_limit=700, time_limit=730)
def continuous_job(job_id):
    engine=ContinuousEngine()
    result=engine.process_job(job_id)
    if result.get('status') in ('succeeded','failed','retry_or_failed'):
        # The completed process_job has released its acquisition lease. Let
        # another ready source proceed without waiting for the periodic tick.
        # Duplicates/busy/paused deliveries never multiply the dispatch chain.
        for next_job in engine.ready_jobs(limit=1):
            try:
                continuous_job.apply_async(args=[next_job],queue='tenderproof',countdown=1)
            except Exception:
                # Durable eligibility is unchanged; the next tick recovers it.
                pass
    return result
