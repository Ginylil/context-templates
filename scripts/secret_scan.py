#!/usr/bin/env python3
"""Read-only, redacted heuristic credential checks for public files and packages."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import importlib.util
import subprocess
import sys
import zipfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
# Load the fixed repository scanner module, never a manifest-selected helper.
_spec = importlib.util.spec_from_file_location(
    'ct_public_content', ROOT / 'shared/lifecycle/public_content.py')
_content = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_content)
SIGNATURES = _content.SIGNATURES
PATTERNS = _content.PATTERNS
PRIVATE_SUFFIXES = _content.PRIVATE_SUFFIXES
findings = _content.findings


def scan(root, packages=None, history=False, staged=False):
    issues, count = [], 0
    if staged:
        # Read the index, never the potentially different working-tree contents.
        changed = set(subprocess.check_output(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMRT', '-z'], cwd=root).split(b'\0'))
        entries = subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=root).split(b'\0')
        for entry in entries:
            if not entry:
                continue
            metadata, raw_name = entry.split(b'\t', 1)
            if raw_name not in changed:
                continue
            mode, oid, stage = metadata.split()
            name = raw_name.decode('utf-8')
            if stage != b'0':
                raise ValueError('Unmerged index entry')
            if mode == b'120000':
                issues.append({'path': name, 'line': 0, 'rule': 'public-symlink'})
            else:
                data = subprocess.check_output(['git', 'cat-file', 'blob', oid], cwd=root)
                issues.extend(findings(data, name)); count += 1
        names = []
    else:
        names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=root).split(b'\0')
    for raw in names:
        if not raw:
            continue
        name = raw.decode('utf-8')
        path = root / name
        if path.is_symlink():
            issues.append({'path': name, 'line': 0, 'rule': 'public-symlink'})
        elif path.is_file():
            issues.extend(findings(path.read_bytes(), name)); count += 1
    if history:
        entries = subprocess.check_output(['git', 'rev-list', '--objects', '--all'], cwd=root, text=True).splitlines()
        for entry in entries:
            oid, _, name = entry.partition(' ')
            kind = subprocess.check_output(['git', 'cat-file', '-t', oid], cwd=root, text=True).strip()
            if kind == 'blob':
                data = subprocess.check_output(['git', 'cat-file', 'blob', oid], cwd=root)
                # Classify the original filename before adding history context,
                # so a root-level .env remains a credential-file finding.
                for issue in findings(data, name):
                    issues.append({**issue, 'path': 'history:' + oid[:12] + ':' + issue['path']})
                count += 1
    if packages is not None:
        catalog = json.loads((packages / 'catalog.json').read_text(encoding='utf-8'))
        for item in catalog['skills']:
            with zipfile.ZipFile(packages / item['archive']) as archive:
                for name in archive.namelist():
                    if not name.endswith('/'):
                        issues.extend(findings(archive.read(name), item['archive'] + ':' + name)); count += 1
    return {'scanned': count, 'findings': issues,
            'limitation': 'Heuristic signatures and credential-file checks; no validation of credential activity or guarantee of absence.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packages', type=Path, help='Scan archives named in this directory catalog.json as well')
    parser.add_argument('--history', action='store_true', help='Also inspect blobs reachable from all local refs')
    parser.add_argument('--staged', action='store_true', help='Scan changed index blobs instead of working-tree files')
    args = parser.parse_args()
    try:
        result = scan(ROOT, args.packages, args.history, args.staged)
        print(json.dumps(result, indent=2))
        return 1 if result['findings'] else 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        print(f'Secret scan could not complete: {type(error).__name__}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
