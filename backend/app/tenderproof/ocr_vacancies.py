"""Spatial reading of the FUNÇÃO/CARGA/CIDADE/VCG/PCD/TOTAL table.

Partial OCR results are review data, never complete publishable cargo records.
"""
import re
import unicodedata

VERSION = 'tenderproof-ocr-vacancies/1'


def _norm(text):
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().upper()


def preview_vacancies(page, region):
    if page.get('extraction_method') != 'ocr_tesseract':
        return None
    all_words = page['ocr']['words']
    words = [(i, all_words[i]) for i in region['word_indices']]
    cx = lambda w: w['bbox'][0] + w['bbox'][2]/2
    cy = lambda w: w['bbox'][1] + w['bbox'][3]/2
    headers = {}
    for label in ('FUNCAO', 'CARGA', 'REGIME', 'CIDADE', 'VCG', 'PCD'):
        matches = [(i,w) for i,w in words if _norm(w['text']) == label]
        if len(matches) != 1:
            return None
        headers[label] = matches[0]
    h = {key: word for key, (_,word) in headers.items()}
    if not all(cx(h[a]) < cx(h[b]) for a,b in zip(h, list(h)[1:])):
        return None
    scale = max(w['bbox'][3] for w in h.values())
    if max(cy(w) for w in h.values())-min(cy(w) for w in h.values()) > scale*2:
        return None
    totals = [(i,w) for i,w in words if _norm(w['text']) == 'TOTAL' and cx(w)>cx(h['PCD'])
              and abs(cy(w)-cy(h['PCD'])) < scale*2]
    if len(totals) != 1:
        return None
    headers['TOTAL'] = totals[0]; h['TOTAL'] = totals[0][1]
    header_bottom = max(w['bbox'][1]+w['bbox'][3] for w in h.values())
    split_role_hours = (cx(h['FUNCAO'])+cx(h['CARGA']))/2
    split_hours_regime = (cx(h['CARGA'])+cx(h['REGIME']))/2
    anchors = sorted([(i,w) for i,w in words if re.fullmatch(r'\d{1,2}h', w['text'], re.I)
                      and split_role_hours<cx(w)<split_hours_regime and cy(w)>header_bottom], key=lambda iw:cy(iw[1]))
    footers = [(i,w) for i,w in words if _norm(w['text']) == 'TOTAL'
               and cx(w)<split_role_hours and cy(w)>header_bottom]
    if len(footers) != 1 or not anchors:
        return None
    footer = footers[0][1]
    anchors = [(i,w) for i,w in anchors if cy(w)<cy(footer)]
    if not anchors or len(anchors)>100:
        return None
    row_centers = [cy(w) for _,w in anchors]
    edges = [header_bottom]+[(a+b)/2 for a,b in zip(row_centers,row_centers[1:])]+[(row_centers[-1]+cy(footer))/2]
    if any(b-a < scale*.6 for a,b in zip(row_centers,row_centers[1:])):
        return None
    # Numeric columns are delimited by their observed headers, not fixed pixels.
    city_right = (h['CIDADE']['bbox'][0]+h['CIDADE']['bbox'][2]+h['VCG']['bbox'][0])/2
    count_edges = [city_right, (cx(h['VCG'])+cx(h['PCD']))/2, (cx(h['PCD'])+cx(h['TOTAL']))/2,
                   cx(h['TOTAL'])+(cx(h['TOTAL'])-cx(h['PCD']))/2]

    def cell(items, left, right):
        return sorted([(i,w) for i,w in items if left <= cx(w) < right], key=lambda iw:iw[1]['bbox'][0])

    def number(items):
        value = ''.join(w['text'] for _,w in items)
        if value in ('-', '–', '—'):
            return 0
        return int(value) if re.fullmatch(r'\d{1,5}', value) else None

    rows = []
    for n, (_,anchor) in enumerate(anchors):
        items = [(i,w) for i,w in words if edges[n] <= cy(w) < edges[n+1]]
        name_words = cell(items, 0, anchor['bbox'][0])
        name = ' '.join(w['text'] for _,w in name_words if w['text'] != '|')
        # Multi-line names require a different row segmentation contract.
        if not name or any(abs(cy(w)-cy(anchor))>scale for _,w in name_words):
            return None
        counts = [number(cell(items,a,b)) for a,b in zip(count_edges,count_edges[1:])]
        if counts[0] is None or counts[2] is None or counts[2] < counts[0]:
            return None
        if counts[1] is not None and counts[0]+counts[1] != counts[2]:
            return None
        city_left = (h['REGIME']['bbox'][0]+h['REGIME']['bbox'][2]+h['CIDADE']['bbox'][0])/2
        city = ' '.join(w['text'] for _,w in cell(items,city_left,city_right) if w['text'] not in ('-', '|'))
        schedule = cell(items,anchor['bbox'][0],split_hours_regime)
        if not any(_norm(w['text']) == 'SEMANAIS' for _,w in schedule):
            return None
        evidence_indices = sorted(set(i for i,w in items if cx(w)<count_edges[-1]))
        rows.append({'nome':name,'cidade':city or None,'jornada':f"{int(anchor['text'][:-1])} horas semanais",
                     'vagas_ampla_concorrencia':counts[0],'vagas_pcd':counts[1],'vagas_imediatas':counts[2],
                     'cadastro_reserva':None,'remuneracao':None,'requisitos':None,'taxa_inscricao':None,
                     'pending_fields':['cadastro_reserva','remuneracao','requisitos','taxa_inscricao']+(['vagas_pcd'] if counts[1] is None else []),
                     'evidence':{'document_sha256':region['document_sha256'],'page_number':page['page_number'],
                                 'region_id':region['id'],'word_indices':evidence_indices}})
    footer_items = [(i,w) for i,w in words if abs(cy(w)-cy(footer))<scale*.8]
    footer_counts = [number(cell(footer_items,a,b)) for a,b in zip(count_edges,count_edges[1:])]
    if footer_counts[0] != sum(r['vagas_ampla_concorrencia'] for r in rows) or footer_counts[2] != sum(r['vagas_imediatas'] for r in rows):
        return None
    if footer_counts[1] is None or footer_counts[0]+footer_counts[1] != footer_counts[2]:
        return None
    if sum(r['vagas_pcd'] or 0 for r in rows)>footer_counts[1]:
        return None
    if all(r['vagas_pcd'] is not None for r in rows) and sum(r['vagas_pcd'] for r in rows)!=footer_counts[1]:
        return None
    return {'method_version':VERSION,'review_required':True,'rows':rows,
            'total_vagas':footer_counts[2],'total_pcd':footer_counts[1],
            'header_word_indices':[i for i,w in headers.values()],
            'footer_word_indices':[i for i,w in footer_items if cx(w)<count_edges[-1]],
            'notice':'Quadro de vagas lido por coordenadas. Remuneração, requisitos, taxa e cadastro de reserva ainda precisam de extração e conferência.'}
