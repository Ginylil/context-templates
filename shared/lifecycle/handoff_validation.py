"""Offline handoff contracts, source identities and redacted content checks."""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import re

_spec = importlib.util.spec_from_file_location(
    'ct_handoff_public_content', Path(__file__).with_name('public_content.py'))
_content = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_content)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(value, names, where):
    require(isinstance(value, dict) and set(value) == set(names.split()),
            f'{where}: missing or unknown fields')


def text(value, where):
    require(isinstance(value, str) and bool(value.strip()), f'{where}: nonempty text required')
    require(not any(ord(c) < 32 for c in value), f'{where}: control characters are not allowed')


def strings(value, where, minimum=0):
    require(isinstance(value, list) and len(value) >= minimum, f'{where}: expected text list')
    for item in value:
        text(item, where)
    require(len(value) == len(set(value)), f'{where}: duplicate entries')


def records(value, where):
    require(isinstance(value, list) and all(isinstance(x, dict) for x in value),
            f'{where}: expected object list')


def safe(data, name):
    # Environment-file spelling must be safe on case-insensitive filesystems too.
    require(not _content.findings(data, str(name).casefold()),
            'Credential/signing-file finding; contents redacted')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON property')
        result[key] = value
    return result


def load(path):
    path = Path(path)
    safe(b'', path.name)
    require(not path.is_symlink() and path.is_file(), 'Expected a regular JSON file')
    require(path.stat().st_size <= 2_000_000, 'JSON file exceeds 2 MB')
    raw = path.read_bytes()
    safe(raw, path.name)
    def invalid_constant(_):
        raise ValueError('Non-finite JSON number')
    return json.loads(raw, object_pairs_hook=unique_object, parse_constant=invalid_constant)


def timestamp(value):
    text(value, 'checked_at')
    try:
        observed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        require(observed.tzinfo is not None, 'checked_at: timezone required')
        require(observed <= dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5),
                'checked_at: future observation')
    except (ValueError, OverflowError) as error:
        raise ValueError('checked_at: invalid, naive or future timestamp') from error


def source_file(reference, base):
    fields(reference, 'path sha256', 'reference')
    text(reference['path'], 'reference.path')
    require(isinstance(reference['sha256'], str) and
            re.fullmatch(r'[0-9a-f]{64}', reference['sha256']), 'reference: invalid SHA-256')
    path = Path(reference['path'])
    if not path.is_absolute():
        path = Path(base) / path
    require(not path.is_symlink() and path.is_file(), 'Source: expected a regular file')
    safe(b'', path.resolve().name)
    require(path.stat().st_size <= 2_000_000, 'Source exceeds 2 MB; use a sanitized excerpt')
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == reference['sha256'], 'Source: stale or mismatched digest')
    safe(data, path.name)
    return path.resolve()


def validate_input(value, base):
    fields(value, 'schema_version scope request constraints continuation selected_next_action sources', 'input')
    require(type(value['schema_version']) is int and value['schema_version'] == 1, 'Unsupported schema_version')
    safe(json.dumps(value, ensure_ascii=False).encode('utf-8'), 'input.json')
    fields(value['scope'], 'description workspace', 'scope')
    text(value['scope']['description'], 'scope.description')
    workspace = value['scope']['workspace']
    if workspace is not None:
        text(workspace, 'workspace')
        require(Path(workspace).is_absolute() and Path(workspace).is_dir(),
                'workspace: expected an existing absolute directory')
    text(value['request'], 'request')
    strings(value['constraints'], 'constraints')
    require(isinstance(value['continuation'], str) and value['continuation'] in
            ('needed', 'blocked', 'complete', 'undecided'), 'Unknown continuation state')
    if value['selected_next_action'] is not None:
        text(value['selected_next_action'], 'selected_next_action')
    require(value['continuation'] != 'complete' or value['selected_next_action'] is None,
            'Completed scope cannot manufacture a next action')
    records(value['sources'], 'sources')
    require(bool(value['sources']), 'Include at least a sanitized conversation source')
    sources = {}
    for source in value['sources']:
        fields(source, 'id kind location status checked_at reference', 'source')
        key = source['id']
        require(isinstance(key, str) and re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', key),
                'source.id: expected lowercase hyphenated identifier')
        require(key not in sources, 'Duplicate source identifier')
        require(isinstance(source['kind'], str) and source['kind'] in
                ('file', 'git', 'github', 'conversation', 'artifact'), 'Unknown source kind')
        text(source['location'], 'source.location')
        require(source['status'] in ('verified', 'unverified'), 'Unknown source status')
        if source['status'] == 'verified':
            timestamp(source['checked_at'])
            source_file(source['reference'], base)
            if source['kind'] == 'file':
                require(source['location'] == source['reference']['path'], 'File location must match reference')
        else:
            require(source['reference'] is None and source['checked_at'] is None,
                    'Unverified source cannot claim checked evidence')
        sources[key] = source
    require(any(source['kind'] == 'conversation' for source in sources.values()),
            'Include a sanitized user-request/conversation source')
    return sources


def references(ids, sources, verified=False, minimum=0):
    strings(ids, 'source_ids', minimum)
    require(all(key in sources for key in ids), 'Unknown source reference')
    if verified:
        require(all(sources[key]['status'] == 'verified' for key in ids),
                'Unverified source cannot support a verified claim')


def validate_output(intake, output, base):
    sources = validate_input(intake, base)
    fields(output, 'schema_version input_sha256 status summary read_first verified_state unverified_state '
           'decision_frame objective objective_kind constraints validation blockers final_response', 'output')
    require(type(output['schema_version']) is int and output['schema_version'] == 1, 'Unsupported schema_version')
    safe(json.dumps(output, ensure_ascii=False).encode('utf-8'), 'output.json')
    require(output['input_sha256'] == digest(intake), 'Output is bound to stale or different input')
    require(output['constraints'] == intake['constraints'], 'Preserve all input constraints exactly')
    text(output['summary'], 'summary')
    require(output['status'] in ('ready', 'blocked', 'no-follow-up'), 'Unknown output status')
    expected = {'needed': ('ready', 'blocked'), 'blocked': ('blocked',),
                'complete': ('no-follow-up',), 'undecided': ('ready', 'blocked')}
    require(output['status'] in expected[intake['continuation']], 'Output contradicts continuation state')
    fields(output['decision_frame'], 'deciding not_deciding reason', 'decision_frame')
    strings(output['decision_frame']['deciding'], 'deciding', 1)
    strings(output['decision_frame']['not_deciding'], 'not_deciding')
    text(output['decision_frame']['reason'], 'decision_frame.reason')
    records(output['blockers'], 'blockers')
    for item in output['blockers']:
        fields(item, 'reason next_action', 'blocker')
        text(item['reason'], 'blocker.reason')
        text(item['next_action'], 'blocker.next_action')
    require(bool(output['blockers']) == (output['status'] == 'blocked'), 'Blocked output needs actionable blockers')
    kind = output['objective_kind']
    if output['status'] == 'no-follow-up':
        require(output['objective'] is None and kind == 'none', 'Completed work must not invent follow-up')
    else:
        text(output['objective'], 'objective')
        require(isinstance(kind, str) and kind in
                ('continue-work', 'resolve-blocker', 'establish-next-action'), 'Expected one objective kind')
        if output['status'] == 'blocked':
            require(kind == 'resolve-blocker', 'Blocked objective must resolve the blocker')
        elif intake['continuation'] == 'undecided':
            require(kind == 'establish-next-action', 'Undecided scope needs a focused next-action assessment')
        if intake['selected_next_action'] is not None and output['status'] == 'ready':
            require(output['objective'] == intake['selected_next_action'], 'Preserve the selected next action')
    records(output['read_first'], 'read_first')
    require(output['status'] == 'no-follow-up' or bool(output['read_first']), 'Name what to read or verify first')
    for item in output['read_first']:
        fields(item, 'source_id instruction', 'read_first')
        references([item['source_id']], sources)
        text(item['instruction'], 'read_first.instruction')
    records(output['verified_state'], 'verified_state')
    for item in output['verified_state']:
        fields(item, 'statement source_ids', 'verified_state')
        text(item['statement'], 'verified_state.statement')
        references(item['source_ids'], sources, verified=True, minimum=1)
    records(output['unverified_state'], 'unverified_state')
    unchecked = set()
    for item in output['unverified_state']:
        fields(item, 'statement check_first source_ids', 'unverified_state')
        text(item['statement'], 'unverified_state.statement')
        text(item['check_first'], 'unverified_state.check_first')
        references(item['source_ids'], sources)
        unchecked.update(item['source_ids'])
    require({key for key, source in sources.items() if source['status'] == 'unverified'} <= unchecked,
            'Carry every unverified source with a first verification step')
    records(output['validation'], 'validation')
    for item in output['validation']:
        fields(item, 'instruction previous_result source_ids', 'validation')
        text(item['instruction'], 'validation.instruction')
        require(item['previous_result'] in ('passed', 'failed', 'blocked', 'not-run'), 'Unknown check result')
        executed = item['previous_result'] in ('passed', 'failed')
        references(item['source_ids'], sources, verified=executed, minimum=int(executed))
    strings(output['final_response'], 'final_response', 1)
    return sources
