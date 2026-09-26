"""Document effects scoped to a function, retained as unapproved suggestions."""
import re
from app.tenderproof.fields import _date_value

VERSION = 'tenderproof-registration-effects/1'
DATE = r'\d{1,2}/\d{1,2}/\d{4}'
WRITTEN_DATE = r'\d{1,2}\s+DE\s+[A-ZÇ]+\s+DE\s+\d{4}'
HEADER = re.compile(r'^PORTARIA\s+CONJUNTA\s+SAD/FACEPE\s+N[º°o.]?\s*(?P<number>\d+)\s+DO\s+DIA\s+(?P<date>'+WRITTEN_DATE+r')\s*$',re.I|re.M)
REFERENCE = re.compile(r'regido\s+pela\s+Portaria\s+Conjunta\s+SAD/FACEPE\s+n[º°o.]?\s*(?P<number>\d+),\s+do\s+dia\s+(?P<date>'+WRITTEN_DATE+r')',re.I)
ANNUL = re.compile(r'Art\.?\s*1[º°o.]?\s+Anular\s+as\s+inscri[çc][õo]es\s+exclusivamente\s+para\s+a\s+fun[çc][ãa]o\s+de\s+(?P<role>[^;,]{1,160}),\s+realizadas\s+no\s+per[íi]odo\s+de\s+(?P<start>'+DATE+r')\s+a\s+(?P<end>'+DATE+r')\s*;',re.I)
REOPEN = re.compile(r'Art\.?\s*2[º°o.]?\s+reabrir\s+o\s+per[íi]odo\s+de\s+inscri[çc][õo]es\s+exclusivamente\s+para\s+a\s+fun[çc][ãa]o\s+de\s+(?P<role>[^;,]{1,160})\s*;',re.I)
SCHEDULE = re.compile(r'Art\.?\s*3[º°o.]?\s+Estabelecer\s+o\s+novo\s+cronograma\s+de\s+atividades\s+exclusivamente\s+para\s+a\s+fun[çc][ãa]o\s+de\s+(?P<role>[^;,]{1,160}),\s+conforme\s+a\s+seguir\s*:',re.I)
PERIOD = re.compile(r'^Inscri[çc][õo]es[ \t]+(?P<start>'+DATE+r')[ \t]+at[ée][ \t]+[àa]s[ \t]+(?P<hour>\d{1,2})h(?P<minute>\d{2})(?:min)?[ \t]+de[ \t]+(?P<end>'+DATE+r')\b',re.I|re.M)


def preview_registration_effects(source, region):
    if source != 'facepe_selection' or region.get('boundary_words_excluded'):
        return []
    text = region['text']
    patterns = (HEADER,REFERENCE,ANNUL,REOPEN,SCHEDULE,PERIOD)
    matches = [list(pattern.finditer(text)) for pattern in patterns]
    if any(len(items)!=1 for items in matches):
        return []
    header,reference,annul,reopen,schedule,period = [items[0] for items in matches]
    if not header.start()<reference.start()<annul.start()<reopen.start()<schedule.start()<period.start():
        return []
    # Adjacent gazette acts or multiple authorities require a smaller region.
    if len(re.findall(r'^PORTARIA\s+CONJUNTA\b',text,re.I|re.M))!=1 or re.search(r'^N[º°o.]?\s*[\d.]+\s*[-–]',text,re.I|re.M):
        return []
    role = ' '.join(reopen['role'].split())
    if any(' '.join(m['role'].split()).casefold()!=role.casefold() for m in (annul,schedule)):
        return []
    act_date, original_date = _date_value(header['date']), _date_value(reference['date'])
    old_start,old_end,new_start,new_end = [_date_value(m[key]) for m,key in
        ((annul,'start'),(annul,'end'),(period,'start'),(period,'end'))]
    if (not all((act_date,original_date,old_start,old_end,new_start,new_end))
            or not original_date<=old_start<=old_end<new_start<=new_end or act_date>new_start
            or not 0<=int(period['hour'])<24 or not 0<=int(period['minute'])<60):
        return []
    evidence = [{'region_id':region['id'],'document_sha256':region['document_sha256'],
                 'page_number':region['page_number'],'start':m.start(),'end':m.end(),'snippet':m[0]}
                for m in (header,reference,annul,reopen,schedule,period)]
    return [{'kind':'registration_reopening','method_version':VERSION,'review_required':True,
             'scope':{'kind':'function','name':role,'exclusive':True},
             'act':{'issuer':'SAD/FACEPE','number':header['number'],'date':act_date},
             'original_act':{'issuer':'SAD/FACEPE','number':reference['number'],'date':original_date},
             'annulled_period':{'start':old_start,'end':old_end},
             'new_period':{'start':new_start,'end':new_end,'end_time':f"{int(period['hour']):02d}:{period['minute']}"},
             'evidence':evidence}]
