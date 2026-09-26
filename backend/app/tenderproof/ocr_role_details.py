"""Read a single role's requirements/pay cells and retain separate evidence."""
import re
from decimal import Decimal

from app.tenderproof.ocr_vacancies import _norm

VERSION = 'tenderproof-ocr-role-details/1'


def preview_role_details(page, region, vacancies=()):
    if page.get('extraction_method') != 'ocr_tesseract' or region.get('boundary_words_excluded'):
        return None
    words = [(i,page['ocr']['words'][i]) for i in region['word_indices']]
    cy = lambda w: w['bbox'][1]+w['bbox'][3]/2
    cx = lambda w: w['bbox'][0]+w['bbox'][2]/2
    labels = {}
    for key in ('REQUISITOS','INGRESSO:','REMUNERACAO:','JORNADA','TRABALHO:'):
        hits = [(i,w) for i,w in words if _norm(w['text']) == key]
        if len(hits) != 1:
            return None
        labels[key] = hits[0]
    req, pay, hours = [labels[k][1] for k in ('REQUISITOS','REMUNERACAO:','JORNADA')]
    scale = max(req['bbox'][3],pay['bbox'][3])
    if abs(cy(req)-cy(pay))>scale or cx(req)>=cx(pay) or cy(hours)<=cy(req):
        return None
    if abs(cy(labels['INGRESSO:'][1])-cy(req))>scale or abs(cy(labels['TRABALHO:'][1])-cy(hours))>scale:
        return None
    heading = sorted([(i,w) for i,w in words if cy(w)<req['bbox'][1]-scale],key=lambda iw:iw[1]['bbox'][0])
    if not heading or max(cy(w) for _,w in heading)-min(cy(w) for _,w in heading)>scale:
        return None
    title = ' '.join(w['text'] for _,w in heading)
    title_match = re.fullmatch(r'\d+\.\s+([^\d]{5,180})',title)
    if not title_match:
        return None
    name = title_match[1].strip()
    body = [(i,w) for i,w in words if cy(req)+scale < cy(w) < hours['bbox'][1]]
    currencies = [(i,w) for i,w in body if w['text']=='R$' and cx(w)>cx(req)]
    if len(currencies)!=1:
        return None
    currency = currencies[0][1]
    amounts = [(i,w) for i,w in body if w['bbox'][0]>currency['bbox'][0]
               and abs(cy(w)-cy(currency))<scale and re.fullmatch(r'\d{1,3}(?:\.\d{3})*,\d{2}',w['text'])]
    if len(amounts)!=1:
        return None
    amount = amounts[0][1]
    left_neighbors = [w for i,w in body if w['bbox'][0]+w['bbox'][2]<currency['bbox'][0]
                      and abs(cy(w)-cy(currency))<scale]
    if not left_neighbors:
        return None
    split = (max(w['bbox'][0]+w['bbox'][2] for w in left_neighbors)+currency['bbox'][0])/2
    requirements_words = [(i,w) for i,w in body if cx(w)<split]
    requirements_words.sort(key=lambda iw:(round(cy(iw[1])/scale),iw[1]['bbox'][0]))
    requirements = ' '.join(w['text'] for i,w in requirements_words)
    if len(requirements)<40 or not re.search(r'\b(?:diploma|certificado|gradua[çc][ãa]o|curso)\b',requirements,re.I):
        return None
    hours_words = sorted([(i,w) for i,w in words if abs(cy(w)-cy(hours))<scale*.65], key=lambda iw:iw[1]['bbox'][0])
    schedule = re.search(r'Jornada\s+de\s+Trabalho:\s*(\d{1,2})\s+horas\s+semanais\b', ' '.join(w['text'] for i,w in hours_words),re.I)
    if not schedule or not 1<=int(schedule[1])<=60:
        return None
    workload = f'{int(schedule[1])} horas semanais'
    # A snapshot may contain multiple alternate crops of the same table. Keep
    # identical table rows together, but refuse conflicting or duplicate roles.
    candidates = []
    for table in vacancies:
        matches = [row for row in table['rows'] if ' '.join(row['nome'].casefold().split())==' '.join(name.casefold().split())]
        if len(matches)>1:
            return None
        candidates.extend(matches)
    association = 'missing_vacancy_row'
    if candidates:
        values = {(row['nome'].casefold(),row['jornada'],row['vagas_imediatas'],row.get('cidade')) for row in candidates}
        association = ('matched' if len(values)==1 and candidates[0]['jornada']==workload else 'conflicting_vacancy_row')
    def evidence(items):
        return {'document_sha256':region['document_sha256'],'page_number':page['page_number'],
                'region_id':region['id'],'word_indices':[i for i,w in items]}
    return {'method_version':VERSION,'review_required':True,'nome':name,
            'remuneracao':str(Decimal(amount['text'].replace('.','').replace(',','.'))),'moeda':'BRL',
            'requisitos':requirements,'jornada':workload,'association_status':association,
            'vacancy_evidence':[row['evidence'] for row in candidates],
            'evidence':{'nome':evidence(heading),'remuneracao':evidence([labels['REMUNERACAO:']]+currencies+amounts),
                        'requisitos':evidence([labels['REQUISITOS'],labels['INGRESSO:']]+requirements_words),
                        'jornada':evidence(hours_words)}}
