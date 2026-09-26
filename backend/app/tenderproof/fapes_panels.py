"""Read FAPES file panels without mixing documents from different calls."""
import re
from datetime import datetime
from urllib.parse import urljoin, urlsplit, unquote, quote
from bs4 import BeautifulSoup


def discover_sections(html):
    """Use the published menu, including sections whose URL omits 'editais'."""
    soup = BeautifulSoup(html, 'html.parser')
    menus = []
    for item in soup.select('li.dropdown'):
        heading = item.find('a', recursive=False)
        if heading and heading.get_text(' ', strip=True) == 'Editais':
            menus.append(item)
    anchors = []
    for menu in menus:
        for item in menu.select('li.dropdown'):
            heading = item.find('a', recursive=False)
            if heading and heading.get_text(' ', strip=True) in ('Abertos', 'Em Julgamento'):
                anchors.extend(item.select('ul.dropdown-menu a[href]'))
        anchors.extend(a for a in menu.select('a[href]')
            if a.get_text(' ', strip=True) in ('Encerrados', 'Resultados'))
    urls = set()
    for anchor in anchors:
        if anchor['href'] == '#' and anchor.get('data-toggle') == 'dropdown':
            continue
        parts = urlsplit(urljoin('https://fapes.es.gov.br/', anchor['href']))
        path = unquote(parts.path)
        if (parts.scheme != 'https' or parts.netloc != 'fapes.es.gov.br'
                or parts.query or parts.fragment or '..' in path.split('/')
                or '\\' in path or '%' in path):
            raise ValueError('destino de seção fora do contrato público FAPES')
        urls.add('https://fapes.es.gov.br' + quote(path, safe='/'))
    if not urls:
        raise ValueError('menu de seções FAPES não identificado')
    return sorted(urls)


def parse_file_panels(html):
    soup = BeautifulSoup(html, 'html.parser')
    galleries = soup.select('ul.galeriade-arquivos')
    if not galleries:
        raise ValueError('galeria de documentos FAPES não identificada')
    calls, seen = [], set()
    for gallery in galleries:
        for panel in gallery.find_all('li', class_='panel', recursive=False):
            heading = panel.select_one('.panel-heading')
            label = heading.select_one('.paneltitle-value') if heading else None
            match = re.fullmatch(r'heading-(\d+)', heading.get('id','')) if heading else None
            if not label or not match or match[1] in seen:
                raise ValueError('identidade do painel ausente ou repetida')
            section = panel.find(id='collapse-'+match[1])
            if section is None or section.get('aria-labelledby') != heading['id']:
                raise ValueError('documentos sem vínculo com o painel')
            documents = []
            urls = set()
            for row in section.select('table.table-downloads tbody tr'):
                anchors = row.select('.coluna-1 a[href]')
                date = row.select_one('.dataatualizacao-value')
                if len(anchors) != 1 or date is None:
                    raise ValueError('linha documental não interpretada integralmente')
                anchor = anchors[0]
                title = anchor.get_text(' ', strip=True)
                url = urljoin('https://fapes.es.gov.br/', anchor['href'])
                parts = urlsplit(url)
                path = unquote(parts.path)
                if (parts.scheme != 'https' or parts.netloc != 'fapes.es.gov.br' or parts.query or parts.fragment
                        or not path.startswith('/Media/fapes/') or not path.lower().endswith(('.pdf', '.docx', '.doc'))
                        or '..' in path.split('/') or '\\' in path or '%' in path):
                    raise ValueError('destino documental fora do contrato público FAPES')
                url = 'https://fapes.es.gov.br' + quote(path, safe='/')
                if not title:
                    raise ValueError('título documental ausente')
                updated = datetime.strptime(date.get_text(strip=True), '%d/%m/%Y').date().isoformat()
                caption = row.select_one('.caption-value')
                documents.append({'title':title, 'url':url, 'updated_at':updated,
                    'description':caption.get_text(' ', strip=True) if caption else None,
                    'format': path.rsplit('.', 1)[1].lower(),
                    'duplicate_url_in_panel': url in urls})
                urls.add(url)
            if not documents:
                raise ValueError('painel sem documentos interpretados')
            seen.add(match[1])
            calls.append({'panel_id':match[1], 'title':label.get_text(' ',strip=True), 'documents':documents})
    if not calls:
        raise ValueError('galeria sem painéis interpretados')
    return calls
