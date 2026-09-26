"""Public FAPEAM listing protocol. Discovery does not classify personnel scope."""
import html
import json
import re
from dataclasses import dataclass
from urllib.parse import urlencode, urlsplit, unquote
from bs4 import BeautifulSoup

TABS = ('editais-abertos', 'fluxo-continuo', 'editais-encerrados', 'editais-resultados')
ENDPOINT = 'https://www.fapeam.am.gov.br/wp-admin/admin-ajax.php'


@dataclass(frozen=True)
class FapeamListingRequest:
    """Only the observed public read action; URL and body cannot be supplied."""
    tab: str
    page: int

    def transport(self, url, source):
        expected, request = listing_request(self.tab, self.page)
        if source != 'fapeam_selection' or url != expected:
            raise ValueError('requisição de listagem incompatível com fonte ou destino')
        return request


def acquire_page(fetch, *, tab, page):
    url, _ = listing_request(tab, page)
    request = FapeamListingRequest(tab, page)
    def validate(target):
        request.transport(target, 'fapeam_selection')
    response = fetch(url, validate, 2*1024*1024, public_listing_request=request)
    parsed = parse_listing(response.content.decode('utf-8-sig'), tab=tab, page=page)
    return response, parsed


def listing_request(tab, page):
    if tab not in TABS or type(page) is not int or page < 1:
        raise ValueError('aba ou página FAPEAM inválida')
    action = 'get-editais-resultados' if tab == 'editais-resultados' else 'get-editais'
    return ENDPOINT + '?action=' + action, {
        'method':'POST', 'content_type':'application/x-www-form-urlencoded; charset=utf-8',
        'body':urlencode({'tipo':tab,'p':page,'paginacao':'1'})}


def validate_detail_url(url):
    if not isinstance(url, str):
        raise ValueError('URL de edital inválida')
    p = urlsplit(url)
    if (p.scheme != 'https' or p.netloc != 'www.fapeam.am.gov.br' or p.query or p.fragment
            or not re.fullmatch(r'/editais/[a-z0-9_-]+/', unquote(p.path))):
        raise ValueError('URL fora do catálogo oficial FAPEAM')


def parse_listing(payload, *, tab, page):
    listing_request(tab, page)
    if not isinstance(payload, str) or len(payload.encode('utf-8')) > 2*1024*1024:
        raise ValueError('resposta FAPEAM fora do limite')
    data = json.loads(payload)
    if (not isinstance(data,dict) or not isinstance(data.get('editais_formatted'),list)
            or not isinstance(data.get('paginacao'),str)):
        raise ValueError('contrato de listagem FAPEAM ausente')
    rows = []; ids = set(); urls = set()
    for item in data['editais_formatted']:
        if (not isinstance(item,dict) or type(item.get('ID')) is not int or item['ID'] < 1
                or not isinstance(item.get('post_title'),str) or not item['post_title'].strip()
                or not isinstance(item.get('vigencia'),str)):
            raise ValueError('item FAPEAM incompleto')
        validate_detail_url(item.get('permalink'))
        if item['ID'] in ids or item['permalink'] in urls:
            raise ValueError('identidade repetida na página FAPEAM')
        ids.add(item['ID']); urls.add(item['permalink'])
        rows.append({'external_id':str(item['ID']), 'title':html.unescape(item['post_title']),
            'url':item['permalink'], 'period_observed':item['vigencia'],
            'scope_status':'requires_document_review', 'raw':item})
    nav = BeautifulSoup(data['paginacao'],'html.parser')
    linked = set()
    for anchor in nav.find_all('a'):
        match = re.fullmatch(r"get_editais\('([^']+)',([1-9]\d*),true\);?", anchor.get('onclick',''))
        if not match or match[1] != tab:
            raise ValueError('paginação FAPEAM não reconhecida ou de outra aba')
        linked.add(int(match[2]))
    if data['paginacao'].strip():
        current=nav.select('.current')
        if len(current)!=1 or current[0].get_text(strip=True)!=str(page) or not rows:
            raise ValueError('página atual FAPEAM não corroborada')
    elif page != 1:
        raise ValueError('fim de paginação FAPEAM sem marcador de página')
    return {'items':rows,'linked_pages':sorted(linked),
        'terminal':not any(n>page for n in linked), 'scope_complete':False}
