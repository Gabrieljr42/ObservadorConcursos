from __future__ import annotations

import json
import logging
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath('.'))

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.connectors.registry import MASTER_SOURCES, get_connector

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('live_audit_99')


def serialize_val(val: Any) -> Any:
    if isinstance(val, (datetime,)):
        return val.isoformat()
    if isinstance(val, (Decimal,)):
        return float(val)
    if isinstance(val, dict):
        return {k: serialize_val(v) for k, v in val.items()}
    if isinstance(val, list):
        return [serialize_val(x) for x in val]
    return val


def build_field_audit(item: dict[str, Any] | None) -> dict[str, str] | None:
    if not item:
        return None
    fields = [
        'titulo', 'orgao', 'modalidade', 'cargo', 'area', 'cidade', 'uf',
        'status', 'vagas', 'salario_min', 'salario_max', 'escolaridade',
        'taxa', 'prova_data', 'edital_numero', 'edital_data',
        'inscricao_inicio', 'inscricao_fim', 'link_pagina', 'link_edital',
        'link_inscricao',
    ]
    audit = {}
    for f in fields:
        val = item.get(f)
        if val is not None and str(val).strip() != '':
            audit[f] = 'MATCH'
        else:
            if f in ('titulo', 'link_pagina', 'status'):
                audit[f] = 'MISMATCH'
            else:
                audit[f] = 'NULL_OK'
    return audit


def audit_single_source(index: int, defn) -> dict[str, Any]:
    st_type = defn.source_type
    base_url = defn.base_url
    list_url = defn.list_urls[0] if defn.list_urls else base_url
    start_time = time.monotonic()

    res_entry: dict[str, Any] = {
        'index': index,
        'source_type': st_type,
        'name': defn.name,
        'canonical_name': defn.banca,
        'category': defn.category,
        'url': list_url,
        'base_url': base_url,
        'status': 'degraded',
        'http_status': None,
        'browser_used': False,
        'technology': 'HTML',
        'visible_valid_items': 0,
        'candidates_found': 0,
        'candidates_rejected': 0,
        'processed': 0,
        'empty_evidence': None,
        'error_type': None,
        'error_message': None,
        'sample': None,
        'field_audit': None,
        'publication_audit': None,
        'evidence_urls': [list_url],
        'duration_seconds': 0.0,
    }

    try:
        connector = get_connector(st_type, base_url=base_url, list_url=list_url)
        if hasattr(connector, 'crawl_with_diagnostics'):
            crawl_res = connector.crawl_with_diagnostics()
            items = crawl_res.items
            run_data = crawl_res.run_data
            res_entry['status'] = run_data.status
            res_entry['http_status'] = run_data.http_status
            res_entry['browser_used'] = run_data.browser_used
            res_entry['candidates_found'] = run_data.candidates_found
            res_entry['candidates_rejected'] = run_data.candidates_rejected
            res_entry['empty_evidence'] = run_data.diagnostics_payload.get('empty_evidence')
            res_entry['error_type'] = run_data.error_type
            res_entry['error_message'] = run_data.error_message
        else:
            items = connector.crawl()
            res_entry['status'] = 'success' if items else 'empty_valid'
            res_entry['candidates_found'] = len(items)

        res_entry['processed'] = len(items)
        res_entry['visible_valid_items'] = len(items)

        if items:
            sample = items[0]
            clean_sample = {
                'external_id': sample.get('external_id'),
                'titulo': sample.get('titulo'),
                'orgao': sample.get('orgao'),
                'modalidade': sample.get('modalidade'),
                'cargo': sample.get('cargo'),
                'cidade': sample.get('cidade'),
                'uf': sample.get('uf'),
                'status': sample.get('status'),
                'vagas': sample.get('vagas'),
                'salario_min': serialize_val(sample.get('salario_min')),
                'salario_max': serialize_val(sample.get('salario_max')),
                'taxa': serialize_val(sample.get('taxa')),
                'inscricao_inicio': serialize_val(sample.get('inscricao_inicio')),
                'inscricao_fim': serialize_val(sample.get('inscricao_fim')),
                'link_pagina': sample.get('link_pagina'),
                'link_edital': sample.get('link_edital'),
                'link_inscricao': sample.get('link_inscricao'),
            }
            res_entry['sample'] = clean_sample
            res_entry['field_audit'] = build_field_audit(sample)

            raw_data = sample.get('raw_data') or {}
            pubs = raw_data.get('publications') or []
            res_entry['publication_audit'] = {
                'total_publications': len(pubs),
                'sample_titles': [p.get('title') for p in pubs[:3] if isinstance(p, dict)],
            }
            if sample.get('link_pagina') and sample['link_pagina'] not in res_entry['evidence_urls']:
                res_entry['evidence_urls'].append(sample['link_pagina'])
            if sample.get('link_edital') and sample['link_edital'] not in res_entry['evidence_urls']:
                res_entry['evidence_urls'].append(sample['link_edital'])

    except Exception as exc:
        res_entry['status'] = 'failed'
        res_entry['error_type'] = exc.__class__.__name__
        res_entry['error_message'] = str(exc)
        logger.warning(f'Source {index:02d} ({st_type}) failed: {exc}')

    res_entry['duration_seconds'] = round(time.monotonic() - start_time, 2)
    logger.info(f'[{index:02d}/99] {st_type:25s} -> {res_entry["status"]:12s} (items: {res_entry["processed"]}, {res_entry["duration_seconds"]}s)')
    return res_entry


def main():
    print(f'Starting Full LIVE Audit of {len(MASTER_SOURCES)} sources...')
    start_total = time.monotonic()

    results_by_index: dict[int, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_map = {
            executor.submit(audit_single_source, idx, s_def): idx
            for idx, s_def in enumerate(MASTER_SOURCES, 1)
        }
        for future in as_completed(future_map):
            idx = future_map[future]
            try:
                data = future.result()
                results_by_index[idx] = data
            except Exception as exc:
                logger.error(f'Critical error executing source index {idx}: {exc}')

    ordered_sources = [results_by_index[i] for i in range(1, len(MASTER_SOURCES) + 1)]
    total_duration = round(time.monotonic() - start_total, 2)

    status_counts = {'success': 0, 'empty_valid': 0, 'blocked': 0, 'failed': 0, 'degraded': 0}
    total_items = 0
    for s in ordered_sources:
        st = s.get('status', 'degraded')
        status_counts[st] = status_counts.get(st, 0) + 1
        total_items += s.get('processed', 0)

    summary = {
        'total_sources': len(ordered_sources),
        'success': status_counts.get('success', 0),
        'empty_valid': status_counts.get('empty_valid', 0),
        'blocked': status_counts.get('blocked', 0),
        'failed': status_counts.get('failed', 0),
        'degraded': status_counts.get('degraded', 0),
        'total_items': total_items,
        'duration_seconds': total_duration,
    }

    final_payload = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'code_revision': 'final-audit-2026-08-29',
        'summary': summary,
        'sources': ordered_sources,
    }

    out_path = 'audit_live_99.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(final_payload, f, indent=2, ensure_ascii=False)

    print('\n==================================================')
    print('AUDIT SUMMARY:')
    print(f'  Total Sources   : {summary["total_sources"]}')
    print(f'  Success         : {summary["success"]}')
    print(f'  Empty Valid     : {summary["empty_valid"]}')
    print(f'  Blocked         : {summary["blocked"]}')
    print(f'  Failed          : {summary["failed"]}')
    print(f'  Degraded        : {summary["degraded"]}')
    print(f'  Total Items     : {summary["total_items"]}')
    print(f'  Duration        : {summary["duration_seconds"]}s')
    print('==================================================')
    print(f'Saved to {out_path}')


if __name__ == '__main__':
    main()
