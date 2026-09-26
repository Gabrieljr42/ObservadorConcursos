"""Fetch a signed-distribution DOC reader for subsequent network-free audits."""
import hashlib
import json
import subprocess
from pathlib import Path


def main():
    subprocess.run(['apt-get', 'update', '-qq'], check=True, timeout=180)
    subprocess.run(['apt-get', 'download', 'antiword'], cwd='/tmp', check=True, timeout=120)
    packages = list(Path('/tmp').glob('antiword_*.deb'))
    if len(packages) != 1:
        raise ValueError('antiword package not unique')
    package = packages[0]
    target = Path('/output')
    subprocess.run(['dpkg-deb', '-x', str(package), str(target)], check=True, timeout=30)
    metadata = subprocess.run(['dpkg-deb', '-f', str(package), 'Package', 'Version', 'Architecture'],
        check=True, capture_output=True, text=True).stdout
    record = {'package':package.name,'sha256':hashlib.sha256(package.read_bytes()).hexdigest(),
        'metadata':metadata,'source':'Configured signed Ubuntu apt repositories in observador-product:local'}
    (target/'package-receipt.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps(record))


if __name__ == '__main__':
    main()
