"""Authenticate and verify the real pilot checkpoint without printing secrets."""
import json
import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import httpx


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from app.registration_status import registration_situation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--via-web', action='store_true', help='Verify through the same-origin web proxy')
    args = parser.parse_args()
    base_url = 'http://127.0.0.1:13000/api' if args.via_web else 'http://127.0.0.1:18000'
    private = (ROOT / 'backend/.tenderproof/local-pilot/ACESSO-LOCAL.md').read_text(encoding='utf-8')
    email = re.search(r'E-mail:\s*([^\r\n]+)', private)[1].strip(' `')
    password = re.search(r'Senha:\s*([^\r\n]+)', private)[1].strip(' `')
    with httpx.Client(base_url=base_url, trust_env=False, timeout=45) as client:
        login = client.post('/auth/login', json={'email': email, 'password': password})
        login.raise_for_status()
        refreshed = client.post('/auth/refresh', json={'refresh_token': login.json()['refresh_token']})
        refreshed.raise_for_status()
        client.headers['Authorization'] = 'Bearer ' + refreshed.json()['access_token']
        me = client.get('/auth/me')
        me.raise_for_status()
        first = client.get('/sync/checkpoint')
        first.raise_for_status()
        data = first.json()
        report = {'at': datetime.now(timezone.utc).isoformat(), 'api_base_url': base_url, 'login_http': login.status_code,
                  'refresh_http': refreshed.status_code, 'me_http': me.status_code,
                  'checkpoint_http': first.status_code, 'contests': len(data['concursos']),
                  'sources': len({c['source_id'] for c in data['concursos']}),
                  'structured_jobs': sum(len(c.get('cargos') or []) for c in data['concursos']),
                  'counts': {k: len(data[k]) for k in ('publications','versions','favorites','alerts','notifications')},
                  'catalogue': [], 'open_contest_ids': [], 'ui_verified': False}
        for c in data['concursos']:
            detail = client.get('/concursos/' + str(c['id']))
            detail.raise_for_status()
            review = client.get('/concursos/' + str(c['id']) + '/review-status')
            review.raise_for_status()
            amendments = ((c.get('raw_data') or {}).get('tenderproof') or {}).get('amendments', [])
            detail_amendments = ((detail.json().get('raw_data') or {}).get('tenderproof') or {}).get('amendments', [])
            assert amendments == detail_amendments
            assert c.get('cargos') == detail.json().get('cargos')
            date_value = lambda value: datetime.fromisoformat(value.replace('Z', '+00:00')) if value else None
            situation = registration_situation(SimpleNamespace(
                inscricao_inicio=date_value(c.get('inscricao_inicio')), inscricao_fim=date_value(c.get('inscricao_fim')),
                raw_data=c.get('raw_data'), status=c.get('status')))
            if situation == 'open':
                report['open_contest_ids'].append(c['id'])
            expected_roles = {4: 5, 9: 7, 10: 20, 11: 43, 12: 1, 13: 7, 19: 2, 27: 7, 30: 6}.get(c['id'])
            if expected_roles:
                assert len(c.get('cargos') or []) == expected_roles
            if c['id'] == 11:
                assert c['cargos'][0]['vagas_cadastro_reserva'] == 280
                assert all(job['vagas_cadastro_reserva'] == 20 for job in c['cargos'][1:])
            if c['id'] == 14:
                assert c['inscricao_inicio'][:10] == '2026-09-07'
                assert c['inscricao_fim'][:10] == '2026-09-14'
            if c['id'] == 27:
                for job in c['cargos']:
                    assert job['vagas_pcd_reserva'] == 'CR'
                    assert 'PcD' in job['cadastro_reserva_observacao']
                    assert job['cadastro_reserva'] is (job['vagas_imediatas'] == 0)
            if c['id'] == 18:
                assert c['inscricao_fim'][:10] == '2026-09-10'
                assert c['prova_data'][:10] == '2026-10-18'
            if c['id'] == 30:
                jobs = c['cargos']
                assert sum(job['vagas_imediatas'] for job in jobs) == 20
                assert jobs[0]['remuneracao'] == '6000.00'
                assert all(job['remuneracao'] == '2500.00' for job in jobs[1:])
                assert all(job['cadastro_reserva'] is None and job['taxa_inscricao'] == '97.00' for job in jobs)
                assert all(job['prova_inicio'] == '09:10' for job in jobs[:5])
                assert jobs[5]['prova_inicio'] == '16:10'
                assert all(job['remuneracao_observacao'] and job['vagas_pcd'] == 1 for job in jobs)
            expected_times = {
                26: ('2026-07-22T12:00:00+00:00', '2026-07-25T02:59:00+00:00'),
                27: ('2026-09-10T11:00:00+00:00', '2026-10-07T20:00:00+00:00'),
                28: ('2026-05-12T16:00:00+00:00', '2026-06-10T16:00:00+00:00'),
                29: ('2026-01-12T13:00:00+00:00', '2026-02-12T20:00:00+00:00'),
                30: ('2026-08-10T03:00:00+00:00', '2026-10-09T02:59:00+00:00'),
                32: ('2026-08-18T18:00:00+00:00', '2026-09-18T18:00:00+00:00'),
            }
            if c['id'] in expected_times:
                actual = tuple(date_value(c[name]).isoformat() for name in ('inscricao_inicio', 'inscricao_fim'))
                assert actual == expected_times[c['id']], (c['id'], actual)
                assert all(c[name] == detail.json()[name] for name in ('inscricao_inicio', 'inscricao_fim'))
            report['catalogue'].append({k: c.get(k) for k in ('id','titulo','inscricao_inicio','inscricao_fim','prova_data','cargos')} | {
                'detail_http': detail.status_code, 'review': review.json(), 'amendments': amendments,
                'registration_situation': situation})
            if c['id'] == 3:
                assert amendments, 'Pedrinhas amendment missing from checkpoint'
                assert datetime.fromisoformat(c['inscricao_inicio'].replace('Z', '+00:00')).isoformat() == '2026-09-09T13:00:00+00:00'
                assert datetime.fromisoformat(c['inscricao_fim'].replace('Z', '+00:00')).isoformat() == '2026-09-11T13:00:00+00:00'
                assert c['prova_data'][:10] == '2026-09-27'
                assert not review.json()['pending']
            if c['id'] == 32:
                assert amendments, 'Barra Longa amendment missing from checkpoint'
                assert c['prova_data'][:10] == '2026-10-18'
                assert not review.json()['pending']
                elo = next(a for a in amendments if a['proposal_id'] == 'tpa-663ecb1ce990af4cc1c784310cf8b78b')
                assert elo['changes']['etapas_prova']['new'] == 'Objetiva de Múltipla Escolha e Títulos'
                deadlines = {event['name']: event for event in elo['events'] if 'date' in event}
                assert deadlines['Resultado final']['date'] == '2026-11-30'
                assert deadlines['Entrega dos títulos']['date'] == '2026-11-13'
                assert all(event['end_time'] == '23:59' and event['timezone'] is None for event in deadlines.values())
        second = client.get('/sync/checkpoint')
        second.raise_for_status()
        again = second.json()
        report['repeated_checkpoint_preserved_user_actions'] = all(data[k] == again[k] for k in ('favorites', 'alerts'))
        keys = [(n['user_id'], n.get('alert_id'), n.get('concurso_id'), n['notification_type']) for n in again['notifications']]
        report['notifications_unique'] = len(keys) == len(set(keys))
        assert report['repeated_checkpoint_preserved_user_actions']
        assert report['notifications_unique']
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    path = ROOT / 'backend/.tenderproof/product-completion' / ('delivery-api-current-' + stamp + '.json')
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'catalogue'} | {'receipt': str(path)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
