"""Controlled signature rotations; official transport evidence is documented in helper."""
import copy
import hashlib
import json
import pytest
from test_tenderproof_publication import env
from test_tenderproof_document_review_gate import checkpoint
from app.tenderproof.continuous import ContinuousEngine
from app.tenderproof.contracts import ValidationResult,ValidationStatus
from app.tenderproof.document_identity import document_identity_url,signature_value,signature_manifest,observation_signature

CES='https://concursos.cesgranrio.org.br/media/gpoweb-prd-hibrido3/eventos/27/conteudos/9454893c-7962-4e4f-8be8-fb3c79821d8f.pdf'
CP='https://cpcon.uepb.edu.br/download/edital-processo-seletivo-simplificado-no-002-2026-uepb/'
PAIRS=[
    ('https://cdn.example.org/document.pdf?X-Amz-Signature=one&doc=9','https://cdn.example.org/document.pdf?doc=9&X-Amz-Signature=two'),
    (CES+'?sv=2024-11-04&se=2026-10-01&sr=c&sp=r&sig=one',CES+'?sv=2024-11-04&se=2026-10-02&sr=c&sp=r&sig=two'),
    (CP+'?wpdmdl=9836&refresh=6aa01ae49c5291788877540',CP+'?refresh=6aa01af25d4b21788877554&wpdmdl=9836'),
]


@pytest.mark.parametrize('first,second',PAIRS,ids=['existing-aws','observed-cesgranrio-sas','observed-cpcon-refresh'])
def test_signature_payload_and_manifest_are_copied_normalized_and_deduplicated(first,second):
    original={'url':first,'validation':{'checks':['duplicate '+first,{'nested_url':first}]}}
    other={'url':second,'validation':{'checks':['duplicate '+second,{'nested_url':second}]}}
    saved=copy.deepcopy(original)
    assert signature_value(original)==signature_value(other)
    assert original==saved
    docs=[{'url':u,'title':'Edital','kind':'edital'} for u in (first,second)]
    assert len(signature_manifest(docs))==1 and docs[0]['url']==first and docs[1]['url']==second


@pytest.mark.parametrize('url',[
    CES.replace('concursos.cesgranrio.org.br','example.org')+'?sv=x&se=y&sr=c&sp=r&sig=z',
    CES.replace('/media/','/other/')+'?sv=x&se=y&sr=c&sp=r&sig=z',
    CES+'?sv=x&se=y&sr=c&sp=rw&sig=z',
    CES+'?sv=x&se=y&sr=b&sp=r&sig=z',
    CES+'?sv=x&se=y&sr=c&sp=r&sig=z&id=9',
    CES+'?sv=x&se=y&sr=c&sp=r&sig=z&sig=q',
    CES+'?sv=x&se=y&sr=c&sp=r&sig=',
    CP.replace('cpcon.uepb.edu.br','example.org')+'?wpdmdl=9836&refresh=6aa01ae49c5291788877540',
    CP.replace('/download/','/other/')+'?wpdmdl=9836&refresh=6aa01ae49c5291788877540',
    CP+'?wpdmdl=9836&refresh=6aa01ae49c5291788877540&id=1',
    CP+'?wpdmdl=9836&refresh=6aa01ae49c5291788877540&wpdmdl=9999',
    CP+'?wpdmdl=other&refresh=6aa01ae49c5291788877540',
    CP+'?wpdmdl=9836&refresh=not-valid!',
])
def test_unobserved_hosts_routes_and_parameter_shapes_keep_full_url(url):
    assert document_identity_url(url)==url


def finish(env,monkeypatch,url,digest,now,*,legacy=False):
    run=env[4].model_copy(deep=True)
    doc={'title':run.document.title,'url':url,'kind':'edital'}
    queue,lease=checkpoint(env,[doc],now,finish=False)
    monkeypatch.setattr('app.tenderproof.continuous_store.time.time',lambda:now+3)
    run.run_id='controlled-rotation-'+str(now)
    run.artifact.sha256=digest
    run.document.url_requested=url
    run.validation=ValidationResult(status=ValidationStatus.VALID,checks=['acquired '+url,'nested duplicate '+url])
    env[5].put_run(run)
    engine=ContinuousEngine(queue=queue,run_store=env[5])
    if legacy:
        summary={'title':lease.payload.get('title_observed'),'validation_status':run.validation_status.value,
            'artifact_sha256':run.artifact.sha256,'semantic_hash':run.semantic_hash,'documents':[doc],
            'documents_truncated':False,'is_synthetic_sample':run.is_synthetic_sample,'truncated_pdf':run.truncated}
        extractors={(e.method,e.method_version) for field in run.fields for e in field.evidence}
        signature=observation_signature(summary,run.validation.model_dump(mode='json'),extractors,normalize=False)
        summary['selected_document']=doc
        observation=queue.complete_detail(lease,run.run_id,signature,summary)
    else:
        observation=engine._finish_detail(lease,run)
    return queue,lease,run,observation


@pytest.mark.parametrize('first,second',PAIRS,ids=['aws','cesgranrio','cpcon'])
def test_two_rotations_same_bytes_dedup_but_changed_bytes_hold_survives_rotation(env,monkeypatch,first,second):
    digest=env[4].artifact.sha256
    queue,lease,run,obs1=finish(env,monkeypatch,first,digest,100)
    queue,lease,run,obs2=finish(env,monkeypatch,second,digest,4000)
    assert obs1==obs2 and len(queue.observations(1))==1
    assert queue.snapshot(lease.job_id,1)['metadata']['documents'][0]['url']==second
    assert queue.observations(1)[0]['summary']['documents'][0]['url']==first
    assert not queue.review_for_run(run)['pending']
    changed=hashlib.sha256(b'controlled new PDF bytes').hexdigest()
    queue,_,run,obs3=finish(env,monkeypatch,first,changed,8000)
    assert obs3!=obs1 and queue.review_for_run(run)['pending']
    before=queue.review_for_run(run)
    queue,_,run,obs4=finish(env,monkeypatch,second,changed,12000)
    assert obs4==obs3 and len(queue.observations(1))==2
    assert queue.review_for_run(run)==before
    assert before['documents'][0]['change']=='bytes_changed'
    with queue._db() as db:
        assert db.execute('SELECT COUNT(*) FROM acquired_document_state').fetchone()[0]==1


def test_cpcon_document_id_changes_never_collide(env,monkeypatch):
    first,second=PAIRS[2]
    digest=env[4].artifact.sha256
    finish(env,monkeypatch,first,digest,100)
    queue,_,run,_=finish(env,monkeypatch,second.replace('wpdmdl=9836','wpdmdl=9830'),digest,4000)
    assert len(queue.observations(1))==2 and queue.review_for_run(run)['pending']
    with queue._db() as db:
        assert db.execute('SELECT COUNT(*) FROM acquired_document_state').fetchone()[0]==2


@pytest.mark.parametrize('first,second',PAIRS,ids=['legacy-aws','legacy-sas','legacy-refresh'])
def test_legacy_raw_signature_is_reused_in_place_with_snapshot_audit(env,monkeypatch,first,second):
    digest=env[4].artifact.sha256
    queue,_,original,old_id=finish(env,monkeypatch,first,digest,100,legacy=True)
    with queue._db() as db:
        old_row=dict(db.execute('SELECT * FROM observations WHERE observation_id=?',(old_id,)).fetchone())
    old_payload=env[5].get_run(original.run_id).model_dump_json()
    queue,lease,current,new_id=finish(env,monkeypatch,second,digest,4000)
    assert new_id==old_id and len(queue.observations(1))==1
    assert env[5].get_run(original.run_id).model_dump_json()==old_payload
    with queue._db() as db:
        new_row=dict(db.execute('SELECT * FROM observations WHERE observation_id=?',(old_id,)).fetchone())
        assert db.execute('SELECT last_valid_run_id FROM known_candidates').fetchone()[0]==current.run_id
    assert new_row['last_seen']>old_row['last_seen']
    assert {k:v for k,v in new_row.items() if k!='last_seen'}=={k:v for k,v in old_row.items() if k!='last_seen'}
    metadata=queue.snapshot(lease.job_id,1)['metadata']
    assert metadata['documents'][0]['url']==second
    assert metadata['document_signature_match']['observation_id']==old_id
    assert metadata['document_signature_match']['preserved_signature']==old_row['signature']
    assert not queue.review_for_run(current)['pending']
    changed=hashlib.sha256(b'changed despite legacy signature rotation').hexdigest()
    queue,lease,current,changed_id=finish(env,monkeypatch,first,changed,8000)
    assert changed_id!=old_id and len(queue.observations(1))==2
    assert queue.review_for_run(current)['pending']
    assert 'document_signature_match' not in queue.snapshot(lease.job_id,1)['metadata']


def test_unverifiable_legacy_signature_is_not_silently_merged(env,monkeypatch):
    first,second=PAIRS[1]
    digest=env[4].artifact.sha256
    queue,_,_,old_id=finish(env,monkeypatch,first,digest,100,legacy=True)
    with queue._db(write=True) as db:
        db.execute('UPDATE observations SET signature=? WHERE observation_id=?',('unverifiable-historical-signature',old_id))
    queue,_,_,new_id=finish(env,monkeypatch,second,digest,4000)
    assert new_id!=old_id and len(queue.observations(1))==2
