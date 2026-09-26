"""Corroborate an abbreviated API title against an explicit PDF masthead."""
import re

PDF_EVENT_URL = r'https?://(?:www\.)?cebraspe\.org\.br/concursos/([A-Za-z0-9_]+)(?=[/\s.,;)]|$)'


def masthead(candidate, pages):
    if candidate.source != 'cebraspe_open':
        return None
    code = re.fullmatch(r'(?P<issuer>[A-Za-z]+(?:_[A-Za-z]+)*)_(?P<year>\d{2})(?P<role>(?:_[A-Za-z]+)*)', candidate.external_id or '')
    if not code or re.sub(r'[^a-z0-9]', '', (candidate.title_observed or '').casefold()) != re.sub('_', '', candidate.external_id).casefold():
        return None
    ids = set(re.findall(PDF_EVENT_URL, '\n'.join(p.text for p in pages), re.I))
    if {v.casefold() for v in ids} != {candidate.external_id.casefold()}:
        return None
    first = [p for p in pages if p.page_number == 1 and not p.error and not p.truncated]
    if len(first) != 1:
        return None
    page = first[0]
    from app.tenderproof.fields import _DATED_NOTICE, _dated_notice_value
    notices = list(_DATED_NOTICE.finditer(page.text))
    if len(notices) != 1 or not _dated_notice_value(notices[0]):
        return None
    notice = notices[0]
    if _dated_notice_value(notice).rsplit('/', 1)[1][-2:] != code['year']:
        return None
    abbreviation = re.search(r'[–—-]\s*([^,]+),', notice.group(0))
    expected = re.sub('_', '', code['issuer']+code['role']).casefold()
    if not abbreviation or re.sub(r'[^a-z0-9]', '', abbreviation[1].casefold()) != expected:
        return None
    header = page.text[:notice.start()]
    orgs = list(re.finditer(r'^(?P<org>FUNDAÇÃO[^\n]{5,180})[ \t]*\(' + re.escape(code['issuer']) + r'\)[ \t]*$', header, re.M))
    orgs += list(re.finditer(r'^(?P<org>MINIST[ÉE]RIO P[ÚU]BLICO DO ESTADO D[EO] [A-ZÀ-Ü][A-ZÀ-Ü \-]{2,80})[ \t]*$', header, re.M))
    if len(orgs) != 1:
        return None
    org = orgs[0]
    selection = re.search(r'^(?:[IVXLCDM]+\s+)?CONCURSO PÚBLICO PARA[^\n]*(?:\n(?!\s*\n)[^\n]+)*', header[org.end():], re.M)
    if not selection:
        return None
    return {'page': page, 'orgao': ' '.join(org['org'].split()),
            'titulo': ' '.join(org.group(0).split()), 'snippet': org.group(0)}
