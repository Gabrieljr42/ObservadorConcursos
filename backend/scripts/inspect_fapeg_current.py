"""Preserve current official FAPEG entry points and selection detail evidence."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urldefrag

import httpx
from bs4 import BeautifulSoup


def main():
    root = Path('.tenderproof/product-completion/fapeg') / datetime.now(timezone.utc).strftime('discovery-%Y%m%dT%H%M%SZ')
    root.mkdir(parents=True)
    report = {'pages': [], 'source_integrated': False}
    pending = ['https://goias.gov.br/administracao/processos-seletivos-simplificados/', 'https://goias.gov.br/fapeg/']
    seen = set()
    with httpx.Client(timeout=30, follow_redirects=False, trust_env=False) as client:
        while pending:
            url = pending.pop(0)
            if url in seen:
                continue
            seen.add(url)
            row = {'url': url}
            report['pages'].append(row)
            try:
                with client.stream('GET', url) as response:
                    row['status'] = response.status_code
                    raw = bytearray()
                    for chunk in response.iter_bytes():
                        raw.extend(chunk)
                        if len(raw) > 8 * 1024 * 1024:
                            raise ValueError('HTML byte limit')
                sha = hashlib.sha256(raw).hexdigest()
                (root / (sha + '.html')).write_bytes(raw)
                row['sha256'] = sha
                soup = BeautifulSoup(bytes(raw), 'html.parser')
                links = [{'title': a.get_text(' ', strip=True), 'url': urljoin(url, a['href'])} for a in soup.select('a[href]')]
                row['relevant_links'] = [a for a in links if any(t in (a['title'] + ' ' + a['url']).lower() for t in ('fapeg', 'edita', 'chamada', 'seletivo'))]
                row['headings'] = [h.get_text(' ', strip=True) for h in soup.select('h1,h2,h3')]
                row['document_buttons'] = [{'classes': b.get('class'), 'id': b['data-id'], 'row': b.find_parent('tr').get_text(' ', strip=True)} for b in soup.select('tr button[data-id]')]
                for script in soup.select('script[src]'):
                    script_url=urljoin(url,script['src'])
                    if script_url=='https://selecao.go.gov.br/assets/externo/js/app/edital/index.js':
                        pending.append(script_url)
                for link in links:
                    p = urlsplit(link['url'])
                    if p.scheme == 'https' and p.hostname == 'selecao.go.gov.br' and p.path.startswith('/edital/') and 'fapeg' in (link['title'] + p.path).lower():
                        pending.append(urldefrag(link['url'])[0])
                    if p.scheme=='https' and p.hostname=='goias.gov.br' and p.path in ('/fapeg/editais/','/fapeg/editais/inscricoes-abertas/','/fapeg/editais/em-andamento/','/fapeg/editais/encerrados/') and not p.query:
                        pending.append(urldefrag(link['url'])[0])
            except Exception as exc:
                row['error'] = type(exc).__name__ + ': ' + str(exc)
            (root / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps({'url': url, 'status': row.get('status'), 'error': row.get('error')}), flush=True)
    print(str(root), flush=True)


if __name__ == '__main__':
    main()
