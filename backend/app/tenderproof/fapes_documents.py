"""Document roles from observed FAPES labels; effects still require PDF review."""
import hashlib
import re
from app.tenderproof.pilot_adapters import folded


def document_manifest(panel):
    if re.fullmatch(r'(?:editais encerrados|resultados? editais) \d{4}', folded(panel['title'])):
        raise ValueError('painel anual exige separação por edital antes de criar manifesto')
    result = []
    for row in panel['documents']:
        label = folded(row['title'])
        description = folded(row.get('description') or '')
        specific_guidelines = (re.match(r'diretrizes\b', label) is not None
            or re.search(r'diretrizes especificas da fapes', description) is not None)
        notice_label = re.match(r'(?:edital|(?:\d+[aªº]?\s+)?chamada)\b', label)
        if re.search(r'\b(resultado|homologacao|recurso|classificacao)\b', label):
            kind = 'outro'
        elif re.match(r'anexo\b', label):
            kind = 'anexo'
        elif re.search(r'prorrogacao|reabertura', label):
            kind = 'prorrogacao'
        elif notice_label and re.search(r'alteracao|retificad', label):
            kind = 'consolidado'
        elif re.search(r'retificacao|errata|alteracao', label):
            kind = 'retificacao'
        elif specific_guidelines:
            kind = 'outro'
        elif notice_label and row.get('format') == 'pdf':
            kind = 'edital'
        else:
            kind = 'outro'
        result.append({**row, 'kind': kind,
            'document_role': 'specific_guidelines' if specific_guidelines else kind,
            'doc_id': 'fapes-' + hashlib.sha256((panel['panel_id'] + ':' + row['url']).encode()).hexdigest()[:24],
            'effect_review_required': kind in ('consolidado', 'retificacao', 'prorrogacao')})
    originals = {d['url'] for d in result if d['kind'] == 'edital'}
    return {'panel_id': panel['panel_id'], 'title': panel['title'], 'documents': result,
        'original_url': next(iter(originals)) if len(originals) == 1 else None,
        'original_review_required': len(originals) != 1, 'scope_review_required': True}
