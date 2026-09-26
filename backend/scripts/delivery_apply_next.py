"""Apply an explicitly selected, independently checked proposal from the batch."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select
from app.database import SessionLocal
from app.models import User
from app.tenderproof import publication
from app.tenderproof.publication_models import PublicationOutbox, PublicationProposal
from app.tenderproof.store import get_store

ROOT = Path('/var/lib/observador/tenderproof/product-completion')


def main():
    parser = argparse.ArgumentParser()
    six_sources = {'legatus_open', 'funvapi_open', 'funcern_selection', 'fgv_open', 'fcc_open', 'facet_open', 'consep_open'}
    three_sources = {'objetiva_open', 'institutomais_open', 'ibam_open'}
    six_sources |= three_sources
    parser.add_argument('--source', required=True, choices=['consulpam_open', 'faped_selection', 'fumarc_open', 'fapese_selection', 'ibade_open', 'omni_open', 'consulpam_jobs', 'contemax_open', 'quadrix_open', 'msconcursos_open', 'cris_jobs', 'cotec_jobs', 'exame_open', 'cotec_open', *sorted(six_sources)])
    parser.add_argument('--precise-three', action='store_true')
    args = parser.parse_args()
    if args.source == 'consep_open':
        packet = json.loads((ROOT / 'delivery-next-reextract-consep-precision-v3-20260909.json').read_text())
        pinned = next(p for p in packet['proposals'] if p['source'] == args.source)
        assert pinned['id'] == 'tpp-7c283d64ce9df519f9234936e2fc87a8'
        assert pinned['proposal_hash'] == '39b19297e8c9c6593684e4b2f7f9173508e7999f7b6ef0d194384b26a262df74'
    elif args.source == 'cotec_jobs':
        packet = json.loads((ROOT / 'delivery-roles-cotec-itacarambi-20260909-v2.json').read_text())
        pinned = packet['proposal']
        assert pinned['id'] == 'tpp-132598e22af9859dfba47af8a99325d3'
        assert pinned['proposal_hash'] == 'fd32bb67b075761dcaf8d2f93b31b1cc4fe2e26dc293843ca168409712666a19'
    elif args.source in three_sources:
        packet = json.loads((ROOT / ('delivery-three-precise-proposed-20260909-v2.json' if args.precise_three else 'delivery-next-reextract-three-2026-20260909.json')).read_text())
        pinned = next(p for p in packet['proposals'] if p['source'] == args.source)
    elif args.source in ('exame_open', 'cotec_open'):
        packet = json.loads((ROOT / 'delivery-exame-cotec-proposed-20260909.json').read_text())
        pinned = next(p for p in packet['proposals'] if p['source'] == args.source)
    elif args.source == 'facet_open':
        packet = json.loads((ROOT / 'delivery-next-reextract-facet-title-20260909.json').read_text())
        pinned = packet['proposal']
        title = next(field for field in packet['run']['fields'] if field['field'] == 'titulo')
        assert title['value'] == 'Prefeitura de Floresta/PE – 2026'
    elif args.source in six_sources:
        packet = json.loads((ROOT / 'delivery-next-reextract-six-2026-20260909.json').read_text())
        pinned = next(p for p in packet['proposals'] if p['source'] == args.source)
    elif args.source == 'cris_jobs':
        packet = json.loads((ROOT / 'delivery-cris-jobs-proposed-20260909.json').read_text())
        pinned = packet['proposal']
        assert pinned['id'] == 'tpp-da44c03c106e228a3fe349bfcc98fd4f'
        assert pinned['proposal_hash'] == '756c314b75b7bdec3be54ce7baccda03ecf20108a91281f2dadfb69f19d2c55e'
    elif args.source == 'contemax_open':
        packet = json.loads((ROOT / 'delivery-next-reextract-contemax-orgao-20260909.json').read_text())
        pinned = packet['proposal']
        packet['authorization'] = pinned['authorization']
        assert packet['identity']['orgao'] == 'Prefeitura Municipal De Cubati'
    elif args.source == 'consulpam_jobs':
        packet = json.loads((ROOT / 'delivery-roles-consulpam-maranguape-20260909-v2.json').read_text())
        pinned = packet['proposal']
        packet['authorization'] = pinned['authorization']
        assert packet['cargo_count'] == 43
        assert packet['cargos'][0]['vagas_cadastro_reserva'] == 280
        assert all(c['vagas_cadastro_reserva'] == 20 for c in packet['cargos'][1:])
    elif args.source == 'fapese_selection':
        packet = json.loads((ROOT / 'delivery-fapese-proposal-20260909.json').read_text())
        pinned = packet['proposal']
    else:
        packet_name = ('delivery-next-proposals-ibade-omni-contemax-20260909.json'
            if args.source in ('ibade_open', 'omni_open') else 'delivery-next-real-proposals-20260909.json')
        if args.source in ('quadrix_open', 'msconcursos_open'):
            packet_name = 'delivery-next-reextract-quadrix-msconcursos-20260909.json'
        packet = json.loads((ROOT / packet_name).read_text())
        pinned = next(p for p in packet['proposals'] if p['source'] == args.source)
    fields = ['titulo', 'orgao', 'edital_numero', 'inscricao_inicio', 'inscricao_fim']
    if args.source == 'fapese_selection':
        fields = ['inscricao_inicio', 'inscricao_fim'] if pinned['action'] == 'update' else ['titulo', 'orgao', 'edital_numero']
    if args.source in ('consulpam_jobs', 'cris_jobs', 'cotec_jobs'):
        fields = ['cargos']
    if args.source in ('faped_selection', 'fumarc_open'):
        fields.append('cargos')
    if args.source in {'quadrix_open', 'msconcursos_open', 'exame_open', 'cotec_open', *six_sources}:
        fields.append('prova_data')
    if args.precise_three:
        assert args.source in three_sources and pinned['action'] == 'update'
        fields = ['inscricao_inicio', 'inscricao_fim']
    assert set(fields) <= set(pinned['eligible_fields'])
    with SessionLocal() as db:
        record = db.get(PublicationProposal, pinned['id'])
        assert record and record.proposal_hash == pinned['proposal_hash']
        user = db.get(User, record.owner_user_id)
        store = get_store()
        if record.state == 'proposed':
            publication.approve_proposal(db, proposal_id=record.id, proposal_hash=record.proposal_hash,
                fields=fields, user=user, store=store, authorization=packet['authorization'])
        result = publication.apply_proposal(db, proposal_id=record.id, proposal_hash=record.proposal_hash, user=user, store=store)
        again = publication.apply_proposal(db, proposal_id=record.id, proposal_hash=record.proposal_hash, user=user, store=store)
        assert result['version_id'] == again['version_id']
        outbox = db.scalar(select(PublicationOutbox).where(PublicationOutbox.proposal_id == record.id))
        notifications = publication.drain_outbox(db, outbox_id=outbox.id, user=user) if outbox else None
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        receipt = ROOT / ('delivery-next-applied-' + args.source + '-' + stamp + '.json')
        receipt.write_text(json.dumps({'authorization': packet['authorization'], 'fields': fields, 'application': result,
            'notifications': notifications, 'idempotent_version': again['version_id']}, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
        print(json.dumps({'receipt': str(receipt), 'source': args.source, 'concurso_id': result['concurso_id'], 'version_id': result['version_id'], 'state': result['state']}))


if __name__ == '__main__':
    main()
