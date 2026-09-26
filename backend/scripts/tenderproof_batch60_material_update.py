"""Real IBAM PDF -> material update of an explicitly synthetic baseline.

No portal requests, production writes or observation mutation. Optional PostgreSQL
uses only the existing explicitly disposable local acceptance database.
"""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import HTTPException
from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema
from app.database import Base
from app.models import Concurso, ConcursoVersion, Notification, Source, User
from app.tenderproof import publication as pub
from app.tenderproof.contracts import TenderProofRun
from app.tenderproof.publication_models import PublicationOutbox


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preserved-root',default='.tenderproof/r60replay')
    parser.add_argument('--output',default='../docs/tenderproof-batch60-material-update.json')
    parser.add_argument('--source',default='ibam_open')
    parser.add_argument('--source-name',default='IBAM')
    parser.add_argument('--postgres',action='store_true',help='Also use TENDERPROOF_TEST_POSTGRES_URL, restricted to disposable local fixture')
    args=parser.parse_args()
    root=Path(args.preserved_root).resolve()
    with closing(sqlite3.connect((root/'operational.sqlite3').as_uri()+'?mode=ro',uri=True)) as connection:
        runs=[TenderProofRun.model_validate_json(r[0]) for r in connection.execute('SELECT payload FROM runs ORDER BY saved_at,run_id')]
    run=next(r for r in runs if r.source==args.source and r.execution_status.value=='completed' and r.validation_status.value=='valid' and not r.is_synthetic_sample and r.mode=='real')
    original_run_hash=hashlib.sha256(run.model_dump_json().encode()).hexdigest()
    fields=run.field_map()
    assert fields['titulo'].state.value=='supported' and fields['inscricao_fim'].state.value=='unknown'
    candidate=next(c for c in run.candidates if c.candidate_id==run.selected_candidate_id)
    filename=Path(run.artifact.storage_path.replace('\\','/')).name
    pdf=(root/'artifacts'/filename).read_bytes()
    assert hashlib.sha256(pdf).hexdigest()==run.artifact.sha256

    class PreservedBytes:
        def load_artifact_bytes(self, artifact):
            assert artifact.sha256==run.artifact.sha256
            return pdf

    pg_url=os.getenv('TENDERPROOF_TEST_POSTGRES_URL') if args.postgres else None
    if args.postgres:
        if not pg_url:
            parser.error('TENDERPROOF_TEST_POSTGRES_URL required for --postgres')
        parsed=make_url(pg_url)
        if parsed.host!='127.0.0.1' or parsed.database!='tenderproof_acceptance' or parsed.username!='fixture':
            parser.error('PostgreSQL must be the explicitly disposable loopback acceptance fixture')
    report={'validated_at':datetime.now(timezone.utc).isoformat(),'scope':'real preserved '+args.source+' observation; synthetic canonical baseline only',
        'command':'python scripts/tenderproof_batch60_material_update.py'+(' --postgres' if args.postgres else ''),
        'command_argv':[sys.executable,*sys.argv],
        'source':run.source,'candidate':candidate.external_id,'run_id':run.run_id,'document_sha256':run.artifact.sha256,
        'original_run_payload_sha256':original_run_hash,
        'preserved_root':str(root),'network_requests':0,'production_writes':0,'observation_modified':False,
        'baseline_synthetic':True,'executions':[],
        'limitations':['The prior canonical title, dates and salary are controlled test values, not historical source data.',
            'Unknown dates are observed in the real PDF extraction; no conflicting field was fabricated.',
            'This proves title update, not a real change between two editions of the source.',
            'Outbox is recorded but no notifications are delivered.']}
    previous=dict(os.environ)
    try:
        with tempfile.TemporaryDirectory(prefix='tp-batch60-material-') as temporary:
            temp=Path(temporary)
            os.environ.update(TENDERPROOF_ARTIFACT_DIR=str(temp/'artifacts'),TENDERPROOF_PROCESSING_DIR=str(temp/'processing'),
                TENDERPROOF_PUBLICATION_ENABLED='true',TENDERPROOF_PUBLICATION_ALLOW_SYNTHETIC='false',
                TENDERPROOF_PUBLISHER_USER_IDS=str(run.owner_user_id),TENDERPROOF_MAX_PAGES='60')
            if (root/'continuous.sqlite3').exists():
                with closing(sqlite3.connect((root/'continuous.sqlite3').as_uri()+'?mode=ro',uri=True)) as src, closing(sqlite3.connect(temp/'continuous.sqlite3')) as dst:
                    src.backup(dst)
            for dialect in ['sqlite']+(['postgresql'] if args.postgres else []):
                admin=None; schema=None; engine=None
                try:
                    if dialect=='postgresql':
                        schema='tp_material_'+uuid.uuid4().hex
                        admin=create_engine(pg_url)
                        with admin.begin() as conn: conn.execute(CreateSchema(schema))
                        engine=create_engine(pg_url,connect_args={'options':f'-csearch_path={schema}'})
                    else:
                        engine=create_engine('sqlite:///'+str(temp/'canonical.sqlite3'))
                    Base.metadata.create_all(engine)
                    with sessionmaker(engine,expire_on_commit=False)() as db:
                        user=User(id=run.owner_user_id,name='Isolated material update reviewer',email='material-review@example.test',password_hash='unused',is_active=True)
                        from urllib.parse import urlsplit
                        origin=urlsplit(candidate.detail_url_observed)
                        source=Source(name=args.source_name,source_type=run.source,base_url=origin.scheme+'://'+origin.netloc,active=False)
                        db.add_all([user,source]);db.flush()
                        baseline_title='Título anterior controlado para prova de atualização'
                        contest=Concurso(source_id=source.id,external_id=candidate.external_id,banca=args.source_name,titulo=baseline_title,
                            orgao=fields['orgao'].value,edital_numero=fields['edital_numero'].value,link_pagina=candidate.detail_url_observed,
                            link_edital=run.artifact.url_final,inscricao_inicio=datetime(2026,4,1),inscricao_fim=datetime(2026,4,19),
                            salario_min=3500,salario_max=4000,content_hash='a'*64,raw_data={'fixture':'controlled canonical baseline'})
                        db.add(contest);db.commit()
                        proposal=pub.create_proposal(db,run=run,concurso_id=contest.id,user=user,store=PreservedBytes())
                        repeated=pub.create_proposal(db,run=run,concurso_id=contest.id,user=user,store=PreservedBytes())
                        assert repeated['id']==proposal['id'] and proposal['action']=='update'
                        assert 'inscricao_fim' in proposal['blocked_fields']
                        try:
                            pub.approve_proposal(db,proposal_id=proposal['id'],proposal_hash=proposal['proposal_hash'],fields=['inscricao_fim'],user=user,store=PreservedBytes())
                        except HTTPException as exc:
                            assert exc.status_code==422
                        else: raise AssertionError('Unknown date must not be approved')
                        reviewed=pub.approve_proposal(db,proposal_id=proposal['id'],proposal_hash=proposal['proposal_hash'],fields=['titulo'],user=user,store=PreservedBytes())
                        result=pub.apply_proposal(db,proposal_id=reviewed['id'],proposal_hash=reviewed['proposal_hash'],user=user,store=PreservedBytes())
                        repeat=pub.apply_proposal(db,proposal_id=reviewed['id'],proposal_hash=reviewed['proposal_hash'],user=user,store=PreservedBytes())
                        db.refresh(contest)
                        assert contest.titulo==fields['titulo'].value and contest.titulo!=baseline_title
                        assert contest.inscricao_fim.day==19 and contest.inscricao_inicio.day==1
                        assert float(contest.salario_min)==3500 and float(contest.salario_max)==4000
                        assert result['version_id']==repeat['version_id'] and set(result['result']['diff'])=={'titulo'}
                        def counts():
                            return {name:db.scalar(select(func.count()).select_from(model)) for name,model in [('contests',Concurso),('versions',ConcursoVersion),('outbox',PublicationOutbox),('notifications',Notification)]}
                        after=counts();assert after==dict(contests=1,versions=1,outbox=1,notifications=0)
                        rolled=pub.rollback_proposal(db,proposal_id=proposal['id'],reason='Reverter exclusivamente a baseline sintética deste ensaio.',user=user)
                        again=pub.rollback_proposal(db,proposal_id=proposal['id'],reason='Repetição controlada de rollback.',user=user)
                        db.refresh(contest)
                        assert contest.titulo==baseline_title and rolled['rollback_version_id']==again['rollback_version_id']
                        rollback_counts=counts();assert rollback_counts==dict(contests=1,versions=2,outbox=2,notifications=0)
                        report['executions'].append({'database':dialect,'passed':True,'proposal_id':proposal['id'],
                            'real_supported_update':result['result']['diff'],'evidence':proposal['evidences']['titulo'],
                            'unknown_field':{'name':'inscricao_fim','state':fields['inscricao_fim'].state.value,'value':fields['inscricao_fim'].value,'reason':fields['inscricao_fim'].reason},'unknown_approval_rejected':True,'preserved_controlled_values':{'inscricao_inicio':'2026-04-01','inscricao_fim':'2026-04-19','salario_min':3500,'salario_max':4000},
                            'proposal_creation_request_idempotent':True,'application_idempotent':True,'after_apply':after,
                            'rollback_restores_baseline':True,'rollback_idempotent':True,'after_rollback':rollback_counts})
                finally:
                    if engine: engine.dispose()
                    if admin:
                        with admin.begin() as conn: conn.execute(DropSchema(schema,cascade=True))
                        admin.dispose()
            assert hashlib.sha256(run.model_dump_json().encode()).hexdigest()==original_run_hash
        report['temporary_volume_removed']=not Path(temporary).exists()
        report['passed']=all(e['passed'] for e in report['executions']) and report['temporary_volume_removed']
    finally:
        os.environ.clear();os.environ.update(previous)
    Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps({'passed':report['passed'],'databases':[e['database'] for e in report['executions']],'temporary_volume_removed':report['temporary_volume_removed']}))


if __name__=='__main__': main()
