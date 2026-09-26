"""Generate a factual 99-source matrix. Registry presence is never certification."""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tenderproof.source_adapters import SOURCE_ADAPTERS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--acceptance', type=Path)
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text(encoding='utf-8'))
    acceptance = json.loads(args.acceptance.read_text(encoding='utf-8')) if args.acceptance else {}
    verified = {s['source']:s for s in acceptance.get('sources', [])}
    rows = []
    for source in inventory['sources']:
        key = source['source_type']
        adapter = SOURCE_ADAPTERS.get(key)
        evidence = verified.get(key, {})
        observations = source.get('url_observations', [])
        # Older inventories use 'state' while current probing also exposes status.
        blockers = [o.get('state', o.get('status')) for o in observations
                    if o.get('state', o.get('status')) not in ('http_observed', None)]
        row = {'number':source['number'], 'source':key, 'name':source['name'], 'category':source['category'],
               'family_strategy':type(adapter).__name__ if adapter else source['family'],
               'verified_urls':evidence.get('verified_urls',[{'url':o.get('final_url',o['requested_url']), 'observed_at':o['observed_at'],
                                 'state':o.get('state',o.get('status')), 'sha256':o.get('sha256')} for o in observations]),
               'adapter':type(adapter).__name__ if adapter else None,
               'implementation_state':getattr(adapter,'implementation_state','implemented') if adapter else 'pending',
               'offline_validation':evidence.get('offline_validation','pending'),
               'live_adapter_observation':evidence.get('live_adapter_observation','pending'),
               'homologation_state':evidence.get('homologation_state','pending'),
               'homologation_scope':evidence.get('homologation_scope','Nenhum aceite de adaptador; sondagem de endereço não é homologação'),
               'last_validation':evidence.get('last_validation'), 'evidence':evidence.get('evidence',[]),
               'samples':evidence.get('samples',[]), 'coverage':evidence.get('coverage','unproven'),
               'canonical_publication':evidence.get('canonical_publication'),
               'browser_dependency':evidence.get('browser_dependency',source.get('acquisition_recommendation',{}).get('browser_or_official_api_investigation','unknown')),
               'limitations':evidence.get('limitations',source.get('pending',[])),
               'blocker':evidence.get('blocker', '; '.join(sorted(set(str(b) for b in blockers))) or None),
               'next_action':evidence.get('next_action','Implementar contrato específico e validar amostras oficiais' if not adapter else 'Completar aceite documentado do adaptador'),
               'institutional_scope':source.get('scope'), 'scope_status':source.get('scope_status')}
        rows.append(row)
    assert len(rows) == len({r['source'] for r in rows}) == 99
    report = {'schema_version':1, 'generated_at':datetime.now(timezone.utc).isoformat(),
              'inventory_evidence':str(args.inventory), 'total_sources':99,
              'counts':{field:dict(Counter(r[field] for r in rows)) for field in
                        ('implementation_state','offline_validation','live_adapter_observation','homologation_state')},
              'quality_note':'Estados de implementação, testes, observação do adaptador e homologação têm provas separadas. HTTP do inventário não valida um adaptador.',
              'sources':rows}
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines = ['# Matriz de expansão — 99 fontes', '', report['quality_note'], '',
             'Gerado: '+report['generated_at'], '', '| ID | Fonte | Estratégia | Implementação | Offline | Ao vivo (adaptador) | Homologação / cobertura | Impedimento / próxima ação |',
             '|---|---|---|---|---|---|---|---|']
    for row in rows:
        fields = [row['number'],row['name'],row['family_strategy'],row['implementation_state'],row['offline_validation'],
                  row['live_adapter_observation'],row['homologation_state']+' / '+row['coverage'],
                  (row['blocker']+'; ' if row['blocker'] else '')+row['next_action']]
        lines.append('| '+' | '.join(str(f).replace('|','/').replace('\n',' ') for f in fields)+' |')
    lines += ['', 'Detalhes completos de URLs, datas, amostras, evidências, escopo institucional e limitações estão no JSON adjacente.']
    args.output.with_suffix('.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(report['counts']))


if __name__ == '__main__': main()
