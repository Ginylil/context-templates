#!/usr/bin/env python3
"""Read-only, redacted heuristic credential checks for public files."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SIGNATURES = {
    'private-key': rb'-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----',
    'aws-key': rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'github-token': rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b',
    'openai-token': rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{30,}\b',
    'google-key': rb'\bAIza[A-Za-z0-9_-]{35}\b',
    'google-oauth-token': rb'\bya29\.[A-Za-z0-9_-]{20,}\b',
    'slack-token': rb'\bxox[baprs]-[A-Za-z0-9-]{20,}\b',
    'stripe-key': rb'\b(?:sk|rk)_live_[A-Za-z0-9]{20,}\b',
    'jwt': rb'\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\b',
    'credential-assignment': rb'''(?i)["']?(?:api[_-]?key|access[_-]?token|client[_-]?secret|secret[_-]?key|password|passwd|token)["']?\s*[:=]\s*["']([A-Za-z0-9_+./=-]{20,})["']''',
}
PATTERNS = {name: re.compile(pattern) for name, pattern in SIGNATURES.items()}
PRIVATE_SUFFIXES = {'.p8', '.p12', '.pfx', '.pem', '.key', '.jks', '.keystore', '.mobileprovision'}


def findings(data, name):
    result = []
    path = Path(name)
    if path.suffix.lower() in PRIVATE_SUFFIXES or (path.name.startswith('.env') and path.name not in ('.env.example', '.env.template')):
        result.append({'path': name, 'line': 0, 'rule': 'credential-file'})
    for rule, pattern in PATTERNS.items():
        for match in pattern.finditer(data):
            if rule == 'credential-assignment':
                value = match.group(1)
                if len(set(value)) < 8:
                    continue
            # Never return matched bytes or raw source lines, including fixtures.
            result.append({'path': name, 'line': data[:match.start()].count(b'\n') + 1, 'rule': rule})
    return result


def scan(root, history=False, staged=False):
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
    return {'scanned': count, 'findings': issues,
            'limitation': 'Heuristic signatures and credential-file checks; no validation of credential activity or guarantee of absence.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', action='store_true', help='Also inspect blobs reachable from all local refs')
    parser.add_argument('--staged', action='store_true', help='Scan changed index blobs instead of working-tree files')
    args = parser.parse_args()
    try:
        result = scan(ROOT, history=args.history, staged=args.staged)
        print(json.dumps(result, indent=2))
        return 1 if result['findings'] else 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(f'Secret scan could not complete: {type(error).__name__}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
