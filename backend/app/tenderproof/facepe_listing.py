"""Discover FACEPE personnel selections through the current official SAD menu.

These parsers report observed coverage; a Drive HTTP table is not proof that
all lazy-loaded documents have been enumerated.
"""
import re
from urllib.parse import urljoin, urlsplit, parse_qs

from bs4 import BeautifulSoup

SAD_ROOT = 'https://www.sad.pe.gov.br/concursos-e-selecoes'
_CATEGORY = '/concursos-e-selecoes/64-concursos-e-selecoes-simplificadas/'
_ID = r'[A-Za-z0-9_-]{10,100}'


def validate_listing_url(url):
    p = urlsplit(url)
    if (p.scheme != 'https' or p.netloc != 'www.sad.pe.gov.br'
            or p.query or p.fragment
            or not (p.path == '/concursos-e-selecoes' or re.fullmatch(
                re.escape(_CATEGORY) + r'[1-9]\d*-selecoes-simplificadas-[a-z-]+', p.path))):
        raise ValueError('URL fora das listagens oficiais SAD')


def folder_identity(url):
    p = urlsplit(url)
    match = re.fullmatch(r'/drive/folders/(' + _ID + ')', p.path)
    if (p.scheme != 'https' or p.netloc != 'drive.google.com' or p.fragment
            or not match or p.query not in ('', 'usp=sharing', 'usp=drive_link')):
        raise ValueError('Pasta pública Drive inválida')
    return match[1]


def _soup(html, *, keep_type_icons=False):
    if len(html.encode('utf-8')) > 4 * 1024 * 1024:
        raise ValueError('Página excede limite de leitura')
    soup = BeautifulSoup(html, 'html.parser')
    selector = 'script, style, template, noscript, [hidden]'
    if not keep_type_icons:
        selector += ', [aria-hidden="true"]'
    for n in soup.select(selector):
        n.decompose()
    return soup


def parse_sad_listing(html, url):
    validate_listing_url(url)
    soup = _soup(html)
    bodies = soup.select('[itemprop="articleBody"]')
    if len(bodies) != 1:
        raise ValueError('Corpo do artigo SAD ausente ou ambíguo')
    body = bodies[0]
    navigation = []
    for a in soup.select('a[href]'):
        target = urljoin(url, a['href'])
        try:
            validate_listing_url(target)
        except ValueError:
            continue
        if target != url and target not in navigation:
            navigation.append(target)
    items = []
    # The source uses sibling paragraphs for agency headings and card groups.
    # Stop at every subsequent agency heading, even when it has no folder.
    active = None
    for node in body.children:
        if getattr(node, 'name', None) is None:
            continue
        if node.name == 'p' and node.select_one('span strong'):
            text = node.get_text(' ', strip=True)
            active = text if re.search(r'\bFACEPE\b', text) else None
            continue
        if active is None:
            continue
        for a in node.select('a[href]'):
            target = urljoin(url, a['href'])
            identity = folder_identity(target)
            title = a.get_text(' ', strip=True)
            if not title:
                raise ValueError('Seleção FACEPE sem título')
            item = {'folder_id': identity, 'url': target, 'title_observed': title,
                    'agency_observed': active, 'listing_url': url}
            if any(x['folder_id'] == identity and x['title_observed'] != title for x in items):
                raise ValueError('Pasta FACEPE com títulos conflitantes')
            if item not in items:
                items.append(item)
    return {'items': items, 'next_urls': navigation, 'scope_complete': False,
            'diagnostic': 'Navegação observada; situação e documentos exigem conferência.'}


def parse_drive_rows(html, url):
    folder_id = folder_identity(url)
    # Drive hides decorative type icons from accessibility, but their SVG title
    # still supplies the observed MIME label, including extensionless PDFs.
    soup = _soup(html, keep_type_icons=True)
    grids = soup.select('[role="grid"][aria-rowcount]')
    if len(grids) != 1:
        raise ValueError('Tabela pública Drive ausente ou ambígua')
    grid = grids[0]
    try:
        declared = int(grid['aria-rowcount'])
    except ValueError as exc:
        raise ValueError('Contagem Drive inválida') from exc
    rows = grid.select('tr[data-id][data-target="doc"]')
    items = []
    for index, row in enumerate(rows, 1):
        identity = row['data-id']
        names = row.select('td[data-column-id="16"] strong')
        if (not re.fullmatch(_ID, identity) or len(names) != 1
                or row.get('aria-rowindex') != str(index)
                or any(x['file_id'] == identity for x in items)):
            raise ValueError('Linha Drive com identidade, ordem ou título inválido')
        type_node = row.select_one('svg title')
        items.append({'file_id': identity, 'name': names[0].get_text(' ', strip=True),
                      'type_observed': type_node.get_text(' ', strip=True) if type_node else None,
                      'view_url': 'https://drive.google.com/file/d/' + identity + '/view'})
    if len(items) != declared or declared < 1:
        raise ValueError('Tabela Drive incompleta ou vazio não comprovado')
    return {'folder_id': folder_id, 'items': items, 'declared_rows': declared,
            'scope_complete': False,
            'diagnostic': 'Linhas HTTP conferidas; carregamento adicional requer navegação.'}


def download_url_from_view(html, file_id):
    if not re.fullmatch(_ID, file_id):
        raise ValueError('Identidade de arquivo inválida')
    # Read the URL exposed by the public viewer, never execute its scripts.
    import json
    values = re.findall(r'"(https://drive\.usercontent\.google\.com/uc\?[^"<>]+)"', html)
    urls = set()
    for value in values:
        target = json.loads('"' + value + '"')
        p = urlsplit(target)
        q = parse_qs(p.query, keep_blank_values=True)
        if (p.netloc != 'drive.usercontent.google.com' or p.fragment
                or q != {'id': [file_id], 'export': ['download']}):
            raise ValueError('Download Drive altera identidade ou parâmetros')
        urls.add(target)
    if len(urls) != 1:
        raise ValueError('Download público não é único ou não foi observado')
    return urls.pop()
