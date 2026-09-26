"""Own disposable PostgreSQL container; credentials stay in child environments."""
import json
import argparse
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
NAME = 'tenderproof-batch99-identity-pg-20260908'
PORT = 55471
FLAGS = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

def command(args, **kwargs):
    return subprocess.run(args, capture_output=True, text=True, creationflags=FLAGS,
                          timeout=kwargs.pop('timeout', 60), **kwargs)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', default='../docs/tenderproof-batch99-identity-postgres.json')
    parser.add_argument('--tests', nargs='+', default=['tests/test_concurso_identity_migration.py',
        'tests/test_tenderproof_batch99_foundations.py', 'tests/test_tenderproof_canonical.py',
        'tests/test_tenderproof_publication_postgres.py'])
    args = parser.parse_args()
    report_path = Path(args.report).resolve()
    log_path = report_path.with_suffix('.log')
    if report_path.exists() or log_path.exists():
        parser.error('preserve earlier evidence: choose a new report path')
    report = {'container': NAME, 'host': '127.0.0.1', 'port': PORT,
              'database': 'tenderproof_acceptance', 'image': 'postgres:16-alpine',
              'data_mount': 'private container tmpfs, no host data volume',
              'scope': 'disposable schema/collector/canonical/publication regression; no production database'}
    created = False
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1', PORT)) == 0:
            raise RuntimeError('reserved loopback port occupied; do not touch existing service')
    existing = command(['docker', 'container', 'inspect', NAME])
    if existing.returncode == 0:
        raise RuntimeError('reserved container already exists; preserve earlier evidence')
    password = secrets.token_hex(24)
    docker_env = os.environ.copy()
    docker_env['POSTGRES_PASSWORD'] = password
    try:
        result = command(['docker', 'run', '--detach', '--rm', '--name', NAME,
            '--publish', f'127.0.0.1:{PORT}:5432', '--env', 'POSTGRES_USER=fixture',
            '--env', 'POSTGRES_DB=tenderproof_acceptance', '--env', 'POSTGRES_PASSWORD',
            '--tmpfs', '/var/lib/postgresql/data:rw,size=512m', 'postgres:16-alpine'],
            env=docker_env, timeout=120)
        if result.returncode:
            raise RuntimeError('docker create failed: '+result.stderr.replace(password, 'REDACTED')[:1000])
        created = True
        deadline = time.monotonic()+45
        while time.monotonic() < deadline:
            ready = command(['docker', 'exec', NAME, 'pg_isready', '-U', 'fixture', '-d', 'tenderproof_acceptance'])
            if ready.returncode == 0:
                break
            time.sleep(1)
        else:
            raise TimeoutError('disposable PostgreSQL not ready')
        test_env = os.environ.copy()
        test_env['TENDERPROOF_TEST_POSTGRES_URL'] = f'postgresql+psycopg://fixture:{password}@127.0.0.1:{PORT}/tenderproof_acceptance'
        test_command = [sys.executable, '-m', 'pytest', '-q', *args.tests, '--disable-warnings', '--tb=short']
        report['command'] = [Path(sys.executable).name, *test_command[1:]]
        start = time.monotonic()
        result = command(test_command, cwd=ROOT, env=test_env, timeout=240)
        output = (result.stdout+'\n'+result.stderr).replace(password, 'REDACTED')
        log_path.write_text(output, encoding='utf8')
        report.update(exit_code=result.returncode, duration_s=round(time.monotonic()-start, 3),
                      output_summary=output[-2200:], test_process_finished=True, log=str(log_path))
        print(output[-2200:], flush=True)
    except Exception as exc:
        report.update(exit_code=1, error_type=type(exc).__name__, error=str(exc).replace(password, 'REDACTED')[:1200])
        raise
    finally:
        if created:
            removed = command(['docker', 'rm', '--force', NAME])
            remaining = command(['docker', 'container', 'inspect', NAME])
            report['cleanup'] = {'removal_exit_code': removed.returncode,
                                 'container_absent': remaining.returncode != 0,
                                 'named_volumes_created': 0}
        else:
            report['cleanup'] = {'created': False, 'existing_resources_preserved': True}
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
        print(json.dumps({'exit_code': report.get('exit_code'), 'cleanup': report['cleanup']}), flush=True)
    return report['exit_code']

if __name__ == '__main__':
    raise SystemExit(main())
