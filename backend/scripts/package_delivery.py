from __future__ import annotations

import os
import zipfile
from pathlib import Path

EXCLUDE_DIRS = {
    '.venv', 'venv', 'env', '.env', '__pycache__', '.pytest_cache',
    '.git', '.idea', '.vscode', '.system_generated', 'logs'
}

EXCLUDE_EXTENSIONS = {
    '.pyc', '.pyo', '.pyd', '.log', '.tmp', '.sqlite3'
}

EXCLUDE_FILES = {
    '.env', 'observador_de_concursos_final.zip'
}


def should_exclude(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS or part.startswith('.'):
            # Allow .dockerignore or standard dotfiles that are config
            if part in {'.dockerignore', '.gitignore'}:
                continue
            return True
    if path.suffix.lower() in EXCLUDE_EXTENSIONS:
        return True
    if path.name in EXCLUDE_FILES:
        return True
    return False


def package_project(root_dir: Path, output_zip: Path) -> list[str]:
    included_files: list[str] = []
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]
            for file in sorted(files):
                file_path = Path(root) / file
                if should_exclude(file_path):
                    continue
                rel_path = file_path.relative_to(root_dir)
                zf.write(file_path, rel_path)
                included_files.append(str(rel_path))
    return included_files


def main():
    root = Path(__file__).resolve().parent.parent
    if not (root / 'backend').exists():
        root = root.parent

    out_zip = root / 'observador_de_concursos_final.zip'
    print(f'Packaging project from {root} to {out_zip}...')
    files = package_project(root, out_zip)
    print(f'Successfully packaged {len(files)} files into {out_zip}.')
    print(f'Archive size: {out_zip.stat().st_size / (1024 * 1024):.2f} MB')


if __name__ == '__main__':
    main()
