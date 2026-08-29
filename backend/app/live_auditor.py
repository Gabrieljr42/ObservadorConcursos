from __future__ import annotations

import json
import logging
import re
import sys
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.connectors.base import HEADERS, BaseConnector, CrawlResult
from app.connectors.registry import MASTER_SOURCES, get_connector

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('live_auditor')


def inspect_live_source(source_def_or_type: str | Any, verbose: bool = False) -> dict[str, Any]:
    """Audit a single source in real time against its live website."""
    if isinstance(source_def_or_type, str):
        matching = [s for s in MASTER_SOURCES if s.source_type == source_def_or_type]
        if not matching:
            raise ValueError(f'Unknown source type: {source_def_or_type}')
        defn = matching[0]
    else:
        defn = source_def_or_type

    source_type = defn.source_type
    base_url = defn.base_url
    list_url = defn.list_urls[0] if defn.list_urls else base_url

    audit_result: dict[str, Any] = {
        'source_type': source_type,
        'name': defn.name,
        'base_url': base_url,
        'list_url': list_url,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'http_status': None,
        'http_ok': False,
        'browser_needed': False,
        'technology': 'Unknown',
        'visible_items_estimated': 0,
        'candidates_found': 0,
        'candidates_rejected': 0,
        'processed': 0,
        'crawler_status': None,
        'crawler_diagnostics': {},
        'sample_item': None,
        'publications_count': 0,
        'status': 'BROKEN',
        'issues': [],
        'notes': '',
    }

    # Step 1: Probe list_url via HTTPX
    raw_html = ''
    try:
        with httpx.Client(timeout=25.0, follow_redirects=True, headers=HEADERS, verify=False) as client:
            resp = client.get(list_url)
            audit_result['http_status'] = resp.status_code
            raw_html = resp.text
            if resp.status_code < 400 and len(raw_html) > 500:
                audit_result['http_ok'] = True
            
            # Detect server technology
            server_hdr = resp.headers.get('server', '').lower()
            x_powered = resp.headers.get('x-powered-by', '').lower()
            if 'cloudflare' in server_hdr or 'cf-ray' in resp.headers:
                audit_result['technology'] = 'Cloudflare'
            elif 'wordpress' in raw_html.lower() or 'wp-content' in raw_html.lower():
                audit_result['technology'] = 'WordPress'
            elif 'asp.net' in x_powered or 'viewstate' in raw_html.lower():
                audit_result['technology'] = 'ASP.NET'
            elif 'sharepoint' in raw_html.lower() or 'sp.js' in raw_html.lower():
                audit_result['technology'] = 'SharePoint'
            elif 'react' in raw_html.lower() or 'id="__next"' in raw_html:
                audit_result['technology'] = 'React/Next.js'
            elif 'angular' in raw_html.lower() or 'ng-app' in raw_html:
                audit_result['technology'] = 'Angular'
            elif 'vue' in raw_html.lower():
                audit_result['technology'] = 'Vue.js'
            else:
                audit_result['technology'] = 'HTML/PHP'
    except Exception as exc:
        audit_result['issues'].append(f'HTTP probe failed: {exc.__class__.__name__}: {str(exc)[:150]}')

    # Step 2: Test Connector live execution
    try:
        connector = get_connector(source_type, base_url=base_url, list_url=list_url)
        if hasattr(connector, 'crawl_with_diagnostics'):
            crawl_res: CrawlResult = connector.crawl_with_diagnostics()
            items = crawl_res.items
            run_data = crawl_res.run_data
            audit_result['crawler_status'] = run_data.status
            audit_result['crawler_diagnostics'] = run_data.diagnostics_payload
            audit_result['candidates_found'] = run_data.candidates_found
            audit_result['candidates_rejected'] = run_data.candidates_rejected
            audit_result['browser_needed'] = run_data.browser_used
            if run_data.http_status:
                audit_result['http_status'] = run_data.http_status
        else:
            items = connector.crawl()
            audit_result['candidates_found'] = len(items)

        audit_result['processed'] = len(items)

        if items:
            sample = items[0]
            audit_result['sample_item'] = {
                'titulo': sample.get('titulo'),
                'orgao': sample.get('orgao'),
                'status': sample.get('status'),
                'cidade': sample.get('cidade'),
                'uf': sample.get('uf'),
                'vagas': sample.get('vagas'),
                'salario_min': str(sample.get('salario_min')),
                'salario_max': str(sample.get('salario_max')),
                'link_pagina': sample.get('link_pagina'),
                'link_edital': sample.get('link_edital'),
            }
            raw_data = sample.get('raw_data') or {}
            pubs = raw_data.get('publications') or []
            audit_result['publications_count'] = len(pubs)
            # A successful parse is evidence that the crawler ran, not proof
            # that it matches the live portal. VERIFIED requires an independent
            # browser comparison of counts, sample details and publications.
            audit_result['status'] = 'PARTIAL'
            audit_result['issues'].append(
                'Live crawler produced items, but independent browser comparison is still required for VERIFIED'
            )
        else:
            crawler_status = audit_result.get('crawler_status')
            empty_evidence = bool(
                getattr(locals().get('run_data', None), 'diagnostics_payload', {}).get('empty_evidence')
            )
            if crawler_status == 'empty_valid' and empty_evidence:
                audit_result['status'] = 'EMPTY_VERIFIED'
            elif crawler_status == 'blocked' or audit_result['http_status'] in (401, 403, 429):
                audit_result['status'] = 'BLOCKED'
            elif crawler_status == 'failed' or not audit_result['http_ok']:
                audit_result['status'] = 'BROKEN'
            else:
                audit_result['status'] = 'NOT_AUDITED'
                audit_result['issues'].append(
                    'Zero parsed items without explicit, source-specific proof of an empty official listing'
                )

    except Exception as exc:
        audit_result['status'] = 'BROKEN'
        audit_result['issues'].append(f'Crawler execution failed: {exc.__class__.__name__}: {str(exc)[:200]}')

    if verbose:
        print(json.dumps(audit_result, indent=2, ensure_ascii=False))

    return audit_result


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'ibfc_open'
    res = inspect_live_source(target, verbose=True)
