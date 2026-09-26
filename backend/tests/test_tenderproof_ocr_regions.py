import json
import pytest
from fastapi import HTTPException

from app.tenderproof import ocr_regions as regions, review_cases as review
from test_tenderproof_publication import env
from test_tenderproof_review_cases import setup_case


def scanned_page():
    def word(text,x,y,w=80):
        return {'text':text,'bbox':[x,y,w,20],'line':[1,1,1],'confidence':90}
    # Engine order mixes both columns and places the second visual line first.
    words=[word('16/08/2024',10,100),word('30/08/2024',120,100),
           word('Outro órgão: 2099',600,50,250),word('Inscrições FACEPE',10,50,250),
           word('limite',490,150,40)]
    return {'page_number':1,'text':'16/08/2024 30/08/2024 Outro órgão: 2099 Inscrições FACEPE limite',
        'extraction_method':'ocr_tesseract','extractor_version':'tenderproof-ocr-v1',
        'ocr':{'image_width':1000,'image_height':1000,'image_sha256':'b'*64,'words':words}}


def test_region_reconstructs_visual_lines_and_excludes_other_column():
    page=scanned_page()
    region=regions.region_from_page(page,'a'*64,[0,0,5000,10000])
    assert region['text']=='Inscrições FACEPE\n16/08/2024 30/08/2024'
    assert region['word_indices']==[3,0,1]
    assert region['boundary_words_excluded']==1
    assert region['review_required']
    assert region['text'] not in page['text']
    assert regions.region_from_page(page,'a'*64,[0,0,5000,10000])['id']==region['id']
    assert regions.region_from_page(page,'c'*64,[0,0,5000,10000])['id']!=region['id']


@pytest.mark.parametrize('bounds',[[0,0,0,10000],[5000,0,100,10000],[-1,0,5000,10000],[0,0,10001,10000],[False,0,5000,10000]])
def test_invalid_region_limits_rejected(bounds):
    with pytest.raises(HTTPException): regions.region_from_page(scanned_page(),'a'*64,bounds)


def test_region_persists_with_draft_and_keeps_approval_bound_to_document(env):
    queue,case,_=setup_case(env)
    run,store=env[4],env[5]
    with queue._db(write=True) as db:
        row=db.execute('SELECT payload FROM document_effect_cases WHERE id=?',(case['id'],)).fetchone()
        payload=json.loads(row['payload'])
        for document in payload['documents']:
            document['pages']=[scanned_page()]
        db.execute('UPDATE document_effect_cases SET payload=? WHERE id=?',(json.dumps(payload),case['id']))
    artifact_id=case['documents'][0]['artifact']['artifact_id']
    region=regions.create_region(queue,store,run,case['id'],case['revision_hash'],artifact_id,1,[0,0,5000,10000])
    same=regions.create_region(queue,store,run,case['id'],case['revision_hash'],artifact_id,1,[0,0,5000,10000])
    assert same==region
    current=review.current(queue,run)
    assert len(current['ocr_regions'])==1 and current['approved_at'] is None
    decision={'sha256':run.artifact.sha256,'page':1,'region_id':region['id'],'snippet':region['text'],
              'reason':'Conferência sintética do recorte e do documento.', 'effect':'no_field_change'}
    review.save_draft(queue,run,case['id'],case['revision_hash'],0,[decision])
    restored=review.current(queue,run)
    assert restored['draft'][0]['region_id']==region['id'] and restored['ocr_regions']==[region]
    assert queue.review_for_run(run)['pending']
    with pytest.raises(HTTPException):
        review.approve(queue,store,run,case['id'],case['revision_hash'],[{**decision,'region_id':'ocr-region-'+'0'*64}])
    with pytest.raises(HTTPException):
        regions.create_region(queue,store,run.model_copy(update={'owner_user_id':2}),case['id'],case['revision_hash'],artifact_id,1,[0,0,5000,10000])
    result=review.approve(queue,store,run,case['id'],case['revision_hash'],[decision])
    assert result['approved_at']


def test_region_cannot_cross_page_or_document():
    page=scanned_page(); region=regions.region_from_page(page,'a'*64,[0,0,5000,10000])
    case={'ocr_regions':[region]};doc={'artifact':{'sha256':'c'*64}}
    with pytest.raises(HTTPException): regions.decision_text(case,doc,page,{'region_id':region['id']})
    doc['artifact']['sha256']='a'*64
    with pytest.raises(HTTPException): regions.decision_text(case,doc,{**page,'page_number':2},{'region_id':region['id']})
