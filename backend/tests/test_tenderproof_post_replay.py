import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import pytest
from test_tenderproof_document_post import observed,FIX
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from tenderproof_pilot_continuous_replay import PreservedDriver

@pytest.fixture
def replay(observed):
    a,c,d,html=observed
    row=json.loads((FIX/'pdf-retry-manifest.json').read_text(encoding='utf-8'))['documents'][0]
    raw=(FIX/row['file']).read_bytes()
    run=SimpleNamespace(document=d.model_copy(deep=True),artifact=SimpleNamespace(url_final=d.url_requested,sha256=row['sha256']))
    fixture={'candidate':c,'run':run,'pdf':raw,'replay_document_url':d.url_requested}
    return PreservedDriver(fixture),c,d

def test_exact_post_replay_preserves_bytes(replay):
    driver,c,d=replay
    result=driver.download_document(d,c,max_bytes=30*1024*1024)
    assert hashlib.sha256(result.content).hexdigest()==driver.fixture['run'].artifact.sha256
    assert result.url_requested==d.url_requested
    driver.close();assert driver.closed

@pytest.mark.parametrize('change',['body','doc_id','candidate','bytes','redirect','limit','get','missing'])
def test_post_replay_rejects_different_identity_and_no_get_fallback(replay,change):
    driver,c,d=replay
    c=c.model_copy(deep=True);d=d.model_copy(deep=True);limit=30*1024*1024
    if change=='body':d.acquisition_request.body='181,0'
    elif change=='doc_id':d.doc_id='fapeg-exportarEditalPdf-181'
    elif change=='candidate':c.external_id='010/2024'
    elif change=='bytes':driver.fixture['pdf']+=b'changed'
    elif change=='redirect':driver.fixture['run'].artifact.url_final+='?redirect=1'
    elif change=='limit':limit=1
    elif change=='missing':d.acquisition_request=None
    with pytest.raises(ValueError):
        if change=='get':driver.download(d.url_requested,max_bytes=limit)
        else:driver.download_document(d,c,max_bytes=limit)
