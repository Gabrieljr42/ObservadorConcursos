"""Auditable user-selected OCR regions. Never publishes extracted values."""
import hashlib
import json

from fastapi import HTTPException

VERSION = 'tenderproof-ocr-region/1'


def region_from_page(page, sha256, bounds):
    """Bounds are left/top/right/bottom in ten-thousandths of the raster."""
    if (len(bounds) != 4 or any(type(v) is not int or not 0 <= v <= 10000 for v in bounds)
            or bounds[0] >= bounds[2] or bounds[1] >= bounds[3]):
        raise HTTPException(422, 'Informe limites válidos para a região da página')
    ocr = page.get('ocr') or {}
    width, height = ocr.get('image_width'), ocr.get('image_height')
    words = ocr.get('words')
    if (page.get('extraction_method') != 'ocr_tesseract' or type(width) is not int or type(height) is not int
            or not 0 < width <= 3600 or not 0 < height <= 3600 or not isinstance(words, list)):
        raise HTTPException(409, 'Esta página não possui coordenadas OCR; prepare os documentos novamente')
    left, top, right, bottom = [v * dimension / 10000 for v, dimension in zip(bounds, (width,height,width,height))]
    selected, crossing = [], 0
    for index, word in enumerate(words):
        box = word.get('bbox', [])
        if (len(box) != 4 or any(type(v) is not int for v in box) or min(box) < 0
                or not word.get('text') or box[0]+box[2] > width or box[1]+box[3] > height):
            raise HTTPException(409, 'Coordenadas OCR inválidas; prepare os documentos novamente')
        x, y, w, h = box
        if x >= left and y >= top and x+w <= right and y+h <= bottom:
            selected.append((index,word))
        elif x < right and x+w > left and y < bottom and y+h > top:
            crossing += 1
    if not selected:
        raise HTTPException(422, 'Nenhuma palavra inteira nesta região; ajuste os limites')
    # Reconstruct visual lines inside this region, rather than retaining the
    # engine's reading order which may have merged columns or separated tables.
    lines = []
    for index, word in sorted(selected,key=lambda pair:(pair[1]['bbox'][1]+pair[1]['bbox'][3]/2,pair[1]['bbox'][0])):
        center = word['bbox'][1]+word['bbox'][3]/2
        if not lines or abs(center-lines[-1]['center']) > max(2,min(word['bbox'][3],lines[-1]['height'])*.45):
            lines.append({'center':center,'height':word['bbox'][3],'words':[]})
        lines[-1]['words'].append((index,word))
        centers = sorted(w['bbox'][1]+w['bbox'][3]/2 for _,w in lines[-1]['words'])
        heights = sorted(w['bbox'][3] for _,w in lines[-1]['words'])
        lines[-1]['center'] = centers[len(centers)//2]
        lines[-1]['height'] = heights[len(heights)//2]
    ordered = [sorted(line['words'],key=lambda pair:pair[1]['bbox'][0]) for line in lines]
    text = '\n'.join(' '.join(w['text'] for _,w in line) for line in ordered)
    value = {'method_version':VERSION,'document_sha256':sha256,'page_number':page['page_number'],
             'extractor_version':page.get('extractor_version'),'image_sha256':ocr.get('image_sha256'),
             'bounds':bounds,'word_indices':[i for line in ordered for i,_ in line],
             'text':text,'boundary_words_excluded':crossing,'review_required':True}
    value['id'] = 'ocr-region-'+hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return value


def decision_text(case, document, page, decision):
    region_id = decision.get('region_id')
    if not region_id:
        return page['text']
    region = next((r for r in case.get('ocr_regions',[]) if r['id']==region_id),None)
    if not region or region['document_sha256'] != document['artifact']['sha256'] or region['page_number'] != page['page_number']:
        raise HTTPException(422, 'Região OCR não corresponde ao documento e à página da decisão')
    rebuilt = region_from_page(page,document['artifact']['sha256'],region['bounds'])
    if rebuilt['id'] != region['id']:
        raise HTTPException(409, 'A interpretação da região OCR mudou; confira o recorte novamente')
    return rebuilt['text']


def create_region(queue, store, run, case_id, revision_hash, artifact_id, page_number, bounds):
    from app.tenderproof import review_cases as review
    from app.tenderproof.contracts import Artifact, PageText, FieldState
    from app.tenderproof.fields import extract_fields, METHOD_VERSION
    case = review.read(queue,case_id,run.owner_user_id)
    if case['run_id'] != run.run_id or case['revision_hash'] != revision_hash or case['approved_at'] is not None:
        raise HTTPException(409, 'Recorte exige a revisão pendente correspondente')
    document = next((d for d in case['documents'] if d['artifact']['artifact_id']==artifact_id),None)
    page = next((p for p in document['pages'] if p['page_number']==page_number),None) if document else None
    if not page:
        raise HTTPException(422, 'Documento ou página não pertence à revisão')
    artifact = Artifact.model_validate(document['artifact'])
    content = store.load_artifact_bytes(artifact)
    if content is None or hashlib.sha256(content).hexdigest()!=artifact.sha256:
        raise HTTPException(409, 'PDF preservado ausente ou divergente')
    region = region_from_page(page,artifact.sha256,bounds)
    candidate = next(c for c in run.candidates if c.candidate_id==run.selected_candidate_id)
    fields = extract_fields(candidate=candidate,artifact=artifact,pages=[PageText(
        artifact_id=artifact_id,page_number=page_number,text=region['text'],char_count=len(region['text']),
        extraction_method='ocr_tesseract')])
    for field in fields:
        if field.state == FieldState.UNKNOWN:
            field.state = FieldState.FAILED
            field.reason = 'Interpretação estruturada deste recorte OCR ainda pendente; não significa informação ausente no documento.'
        for evidence in field.evidence:
            evidence.method = 'ocr-region-preview'
            evidence.method_version = VERSION
    region['preview_fields'] = [f.model_dump(mode='json') for f in fields]
    region['preview_fields_version'] = METHOD_VERSION
    from app.tenderproof.registration_effects import preview_registration_effects, VERSION as EFFECTS_VERSION
    region['preview_effects'] = preview_registration_effects(run.source,region)
    region['preview_effects_version'] = EFFECTS_VERSION
    from app.tenderproof.ocr_vacancies import preview_vacancies
    region['preview_vacancies'] = preview_vacancies(page,region)
    from app.tenderproof.ocr_role_details import preview_role_details
    tables = []
    for saved in case.get('ocr_regions',[]):
        if saved['document_sha256'] != artifact.sha256:
            continue
        saved_page = next((p for p in document['pages'] if p['page_number']==saved['page_number']),None)
        if saved_page is None:
            continue
        rebuilt = region_from_page(saved_page,artifact.sha256,saved['bounds'])
        if rebuilt['id'] != saved['id']:
            continue
        table = preview_vacancies(saved_page,rebuilt)
        if table:
            tables.append(table)
    region['preview_role_details'] = preview_role_details(page,region,tables)
    with queue._db(write=True) as db:
        row = db.execute('SELECT payload,approved_at FROM document_effect_cases WHERE id=? AND owner=?',
                         (case_id,run.owner_user_id)).fetchone()
        payload = json.loads(row['payload'])
        if row['approved_at'] is not None or review.revision(queue,run,db)!=case['revision']:
            raise HTTPException(409, 'A revisão mudou; atualize antes de recortar')
        regions = payload.setdefault('ocr_regions',[])
        existing = next((r for r in regions if r['id']==region['id']),None)
        if existing:
            # Region identity binds text/coordinates; refresh only advisory
            # field suggestions, keeping saved decisions and drafts intact.
            existing.update(preview_fields=region['preview_fields'],preview_fields_version=METHOD_VERSION)
            existing.update(preview_effects=region['preview_effects'],preview_effects_version=EFFECTS_VERSION)
            existing['preview_vacancies'] = region['preview_vacancies']
            existing['preview_role_details'] = region['preview_role_details']
        elif len(regions)>=500:
            raise HTTPException(409, 'Limite de regiões desta revisão atingido')
        else:
            regions.append(region)
        db.execute('UPDATE document_effect_cases SET payload=? WHERE id=? AND owner=?',
                   (json.dumps(payload,ensure_ascii=False),case_id,run.owner_user_id))
    return region
