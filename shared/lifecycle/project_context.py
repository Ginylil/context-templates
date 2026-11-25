#!/usr/bin/env python3
"""Validate informational project profiles; never execute commands or write files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import parse_qsl, unquote, urlsplit

sys.dont_write_bytecode = True
from public_content import findings
from project_context_discovery import DiscoveryError, discover

MAX_BYTES = 65536
SECRET_KEY = re.compile(r'(?i)(password|passwd|secret|token|api[_-]?key|credential|signature)')
PROVIDER = re.compile(r'[a-z][a-z0-9-]*\Z')
EMPTY = {'none', 'undecided'}


class ProfileError(ValueError):
    """An error containing only a fixed, public-safe diagnostic."""


def require(condition, message):
    if not condition:
        raise ProfileError(message)


def fields(value, required, optional=()):
    require(isinstance(value, dict), 'Expected an object')
    require(set(required) <= set(value) <= set(required) | set(optional),
            'Missing or unsupported profile fields')


def text(value):
    require(isinstance(value, str) and bool(value.strip()) and len(value) <= 4096,
            'Expected nonempty bounded text')


def safe_strings(value):
    if isinstance(value, dict):
        for key, item in value.items():
            require(not SECRET_KEY.search(key), 'Credential fields are not allowed')
            safe_strings(item)
    elif isinstance(value, list):
        for item in value:
            safe_strings(item)
    elif isinstance(value, str):
        require(not findings(value.encode('utf-8'), 'profile.json'),
                'Credential signature detected; contents redacted')
        for match in re.finditer(r'[a-zA-Z][a-zA-Z0-9+.-]*://[^\s<>"\x27]+', value):
            try:
                link = urlsplit(match.group())
            except ValueError:
                raise ProfileError('Malformed reference URL; contents redacted') from None
            require(link.scheme in {'https', 'http', 'obsidian', 'file'},
                    'Unsupported reference URL scheme')
            require(link.username is None and link.password is None,
                    'URL credentials are not allowed')
            require(not any(SECRET_KEY.search(key) for key, _ in parse_qsl(link.query)),
                    'Credential-bearing URL parameters are not allowed')
            require(not SECRET_KEY.search(unquote(link.fragment).split('=')[0])
                    or '=' not in unquote(link.fragment),
                    'Credential-bearing URL fragments are not allowed')


def service(value):
    fields(value, ('provider', 'location'))
    text(value['provider'])
    require(PROVIDER.fullmatch(value['provider']) is not None, 'Expected a lowercase provider slug')
    if value['provider'] in EMPTY:
        require(value['location'] is None, 'None/undecided providers cannot declare a location')
    else:
        text(value['location'])


def locations(value):
    require(isinstance(value, list) and bool(value), 'Declare at least one location or explicit none')
    seen = set()
    for item in value:
        fields(item, ('provider', 'location', 'purpose', 'primary'))
        service({key: item[key] for key in ('provider', 'location')})
        text(item['purpose'])
        require(type(item['primary']) is bool, 'Primary must be a boolean')
        identity = (item['provider'], item['location'])
        require(identity not in seen, 'Duplicate provider/location')
        seen.add(identity)
    require(sum(item['primary'] for item in value) == 1, 'Select exactly one primary location')
    require(len(value) == 1 or all(item['provider'] not in EMPTY for item in value),
            'None/undecided cannot be combined with configured locations')


def validate(value):
    fields(value, ('schema_version', 'project', 'source_control', 'work_tracking', 'documentation'),
           ('validation', 'release', 'notes'))
    require(type(value['schema_version']) is int and value['schema_version'] == 1,
            'Unsupported profile version')
    safe_strings(value)
    fields(value['project'], ('name', 'summary'))
    text(value['project']['name'])
    text(value['project']['summary'])
    service(value['source_control'])
    locations(value['work_tracking'])
    locations(value['documentation'])
    if 'validation' in value:
        item = value['validation']
        fields(item, ('provider', 'location', 'execution', 'checks'))
        service({key: item[key] for key in ('provider', 'location')})
        require(item['execution'] in ('remote-ci', 'local', 'manual', 'undecided'),
                'Unsupported execution location')
        require(isinstance(item['checks'], list), 'Checks must be an array')
        for command in item['checks']:
            text(command)
    if 'release' in value:
        fields(value['release'], ('staging', 'production', 'notes'))
        for key in ('staging', 'production'):
            if value['release'][key] is not None:
                text(value['release'][key])
        text(value['release']['notes'])
    if 'notes' in value:
        require(isinstance(value['notes'], list), 'Notes must be an array')
        for note in value['notes']:
            text(note)
    pending = []
    if value['source_control']['provider'] == 'undecided':
        pending.append('source_control')
    for key in ('work_tracking', 'documentation'):
        if any(item['provider'] == 'undecided' for item in value[key]):
            pending.append(key)
    if 'validation' in value and (value['validation']['provider'] == 'undecided'
                                 or value['validation']['execution'] == 'undecided'):
        pending.append('validation')
    return pending


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON field')
        result[key] = value
    return result


def invalid_constant(_):
    raise ProfileError('Nonfinite JSON numbers are not allowed')


def load(path):
    path = Path(path)
    require(not path.is_symlink() and path.is_file(), 'Expected a regular profile file')
    require(path.stat().st_size <= MAX_BYTES, 'Profile exceeds size limit')
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique_object,
                      parse_constant=invalid_constant)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('validate', 'render'):
        child = sub.add_parser(name)
        child.add_argument('profile', type=Path)
    child = sub.add_parser('discover')
    child.add_argument('--root', type=Path, required=True)
    child.add_argument('--profile', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'discover':
            print(json.dumps(discover(args.root, args.profile, load, validate), ensure_ascii=False, indent=2))
            return 0
        profile = load(args.profile)
        pending = validate(profile)
        if args.command == 'render':
            print(json.dumps(profile, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({'status': 'valid-draft' if pending else 'valid-context',
                              'undecided': pending, 'provider_access_verified': False}))
        return 0
    except (OSError, ValueError, RecursionError, TypeError) as error:
        message = str(error) if isinstance(error, (ProfileError, DiscoveryError)) else type(error).__name__
        print('Project context check failed: ' + message, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
