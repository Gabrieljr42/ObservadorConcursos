"""Positive documentary scope signals; absence never proves employment."""
import re

VERSION = 'tenderproof-selection-scope/1'
_NOTICE = re.compile(r'^EDITAL\s+N[º°o.]?\s*\d{1,4}/\d{4}\s*$', re.I | re.M)
_HEADING = re.compile(
    r'^CHAMADA P[ÚU]BLICA[^\n]{0,500}(?:\n[A-ZÀ-Ý0-9 /,()–—-]{1,200}(?=\n|$)){0,3}', re.M)
_NO_EMPLOYMENT = re.compile(
    r'^(?:\d+(?:\.\d+)*\s+)?A assinatura do TCCB n[ãa]o caracteriza qualquer v[íi]nculo empregat[íi]cio\.', re.I | re.M)


def document_scope(source, artifact, pages):
    """Recognize the observed FAPERN scholarship contract, retaining literal proof.

    Restrict to one numbered original notice and its adjacent public-call heading.
    An unrelated reference to scholarships, or another act in a gazette, is not
    enough. OCR remains advisory for human review, never native field evidence.
    """
    if source != 'fapern_selection' or not pages:
        return None
    if any(p.artifact_id != artifact.artifact_id for p in pages):
        return None
    notices = [(p, m) for p in pages for m in _NOTICE.finditer(p.text)]
    if len(notices) != 1 or notices[0][0].page_number != 1:
        return None
    page, notice = notices[0]
    headings = [m for m in _HEADING.finditer(page.text)
                if 0 <= m.start() - notice.end() <= 200]
    if len(headings) != 1 or not re.search(r'\bBOLSAS\b', headings[0].group()):
        return None
    clauses = [(p, m) for p in pages for m in _NO_EMPLOYMENT.finditer(p.text)]
    if len(clauses) != 1:
        return None
    def evidence(p, match):
        return {'artifact_id': artifact.artifact_id, 'document_sha256': artifact.sha256,
                'page_number': p.page_number, 'snippet': match.group(),
                'start': match.start(), 'end': match.end(),
                'extraction_method': p.extraction_method}
    return {'classification': 'research_scholarship', 'version': VERSION,
            'review_required': True,
            'reason': 'Chamada de bolsas com cláusula expressa de ausência de vínculo empregatício. Fora do escopo de contratação de pessoal; não publicar valores de bolsas como salários.',
            'evidence': [evidence(page, notice), evidence(page, headings[0]), evidence(*clauses[0])]}
