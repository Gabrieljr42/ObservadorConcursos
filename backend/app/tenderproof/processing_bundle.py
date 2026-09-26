"""Deterministic zipapp: fixed worker + verified pure-Python pypdf sources.

No pip, environment, user files, native extensions or network resolution. A source
upgrade must explicitly update the reviewed version/fingerprint and rerun tests.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import io
from pathlib import Path
import zipfile

from app.tenderproof.processing import ProcessingError

PYPDF_VERSION = '6.16.2'
PYPDF_SOURCE_SHA256 = '86ac853161260359fbb55490ac05da42109d757f30b7dce6174642682ee97c82'


def build_processing_bundle() -> tuple[bytes, dict]:
    import pypdf
    if importlib.metadata.version('pypdf') != PYPDF_VERSION:
        raise ProcessingError('dependency_bundle_version_mismatch')
    root = Path(pypdf.__file__).resolve().parent
    sources = sorted(root.rglob('*.py'))
    fingerprint = hashlib.sha256()
    entries = []
    for path in sources:
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ProcessingError('dependency_bundle_source_mismatch')
        relative = path.relative_to(root).as_posix()
        data = path.read_bytes()
        fingerprint.update(relative.encode() + b'\x00' + data + b'\x00')
        entries.append(('pypdf/' + relative, data))
    if fingerprint.hexdigest() != PYPDF_SOURCE_SHA256:
        raise ProcessingError('dependency_bundle_source_mismatch')
    distribution = importlib.metadata.distribution('pypdf')
    license_file = next((p for p in (distribution.files or []) if str(p).replace('\\', '/').endswith('/licenses/LICENSE')), None)
    if license_file is None:
        raise ProcessingError('dependency_bundle_license_missing')
    entries.append(('pypdf-LICENSE', Path(distribution.locate_file(license_file)).read_bytes()))
    worker = Path(__file__).with_name('processing_worker.py').read_bytes()
    entries.append(('__main__.py', worker))
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data, compresslevel=9)
    payload = output.getvalue()
    return payload, {'pypdf_version': PYPDF_VERSION, 'pypdf_source_sha256': PYPDF_SOURCE_SHA256,
                     'worker_sha256': hashlib.sha256(worker).hexdigest(),
                     'bundle_sha256': hashlib.sha256(payload).hexdigest(), 'bundle_bytes': len(payload),
                     'python_source_files': len(sources), 'contains_secrets': False}
