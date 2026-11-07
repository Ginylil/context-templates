"""Validate actor goals, evidence, scenario actions and recovery references."""
from __future__ import annotations

import re
from urllib.parse import urlsplit

ID = re.compile(r'[a-z][a-z0-9-]{0,63}\Z')
CATEGORIES = {'main', 'alternative', 'error', 'recovery'}
STATUSES = {'verified', 'inferred', 'proposed', 'illustrative'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value, where, maximum=600):
    require(isinstance(value, str) and bool(value.strip()) and len(value) <= maximum,
            f'{where}: expected nonempty text of at most {maximum} characters')


def identifier(value, where):
    require(isinstance(value, str) and bool(ID.fullmatch(value)) and value not in {'constructor', 'prototype'}, f'{where}: invalid ID')


def fields(record, required, optional=(), where='record'):
    require(isinstance(record, dict), f'{where}: expected object')
    require(set(required) <= record.keys(), f'{where}: missing required fields')
    require(record.keys() <= set(required) | set(optional), f'{where}: unknown fields')


def mapping(value, where):
    require(isinstance(value, dict) and bool(value), f'{where}: expected nonempty ID map')
    for key, record in value.items():
        identifier(key, where)
        require(isinstance(record, dict), f'{where}.{key}: expected object')
    return set(value)


def references(values, allowed, where, minimum=1):
    require(isinstance(values, list) and len(values) >= minimum, f'{where}: expected ID list')
    require(all(isinstance(v, str) and v in allowed for v in values),
            f'{where}: unknown reference')
    require(len(values) == len(set(values)), f'{where}: duplicate references')


def steps(values, where):
    require(isinstance(values, list) and bool(values), f'{where}: expected ordered steps')
    for step in values:
        if isinstance(step, str):
            text(step, where, 300)
        else:
            fields(step, {'label', 'owner'}, where=where)
            text(step['label'], where, 300)
            text(step['owner'], where, 64)


def source_ids(sources):
    require(isinstance(sources, list), 'sources: expected list')
    ids = set()
    for source in sources:
        fields(source, {'id', 'label', 'reference'}, where='source')
        identifier(source['id'], 'source.id')
        require(source['id'] not in ids, 'sources: duplicate ID')
        ids.add(source['id'])
        text(source['label'], 'source.label')
        reference = source['reference']
        text(reference, 'source.reference', 2000)
        parsed = urlsplit(reference)
        if parsed.scheme:
            require(parsed.scheme in {'http', 'https'} and bool(parsed.hostname)
                    and parsed.username is None and parsed.password is None,
                    'source.reference: unsafe URL')
        else:
            require(not reference.startswith(('/', '\\')) and '\\' not in reference
                    and '..' not in reference.split('/'),
                    'source.reference: use a repository-relative path')
    return ids


def validate_case(key, case, sources):
    fields(case, {'id', 'name', 'trigger', 'pre', 'success', 'parts', 'scenarios', 'evidence'},
           where=f'use case {key}')
    require(case['id'] == key, f'use case {key}: ID must match its key')
    text(case['name'], 'use case.name', 80)
    for field in ('trigger', 'pre', 'success'):
        text(case[field], f'use case.{field}', 300)
    steps(case['parts'], 'use case.parts')
    evidence = case['evidence']
    fields(evidence, {'status', 'source_ids'}, where='evidence')
    require(isinstance(evidence['status'], str) and evidence['status'] in STATUSES,
            'evidence: unsupported status')
    references(evidence['source_ids'], sources, 'evidence.source_ids', 0)
    require(evidence['status'] != 'verified' or bool(evidence['source_ids']),
            'verified use cases require supporting sources')
    scenarios = case['scenarios']
    require(isinstance(scenarios, list) and bool(scenarios), 'scenarios: expected nonempty list')
    ids = set()
    for scenario in scenarios:
        fields(scenario, {'id', 'name', 'condition', 'result', 'category', 'steps', 'recovery'},
               {'trigger'}, 'scenario')
        identifier(scenario['id'], 'scenario.id')
        require(scenario['id'] not in ids, 'scenarios: duplicate ID')
        ids.add(scenario['id'])
        text(scenario['name'], 'scenario.name', 80)
        for field in ('condition', 'result'):
            text(scenario[field], f'scenario.{field}', 300)
        if 'trigger' in scenario:
            text(scenario['trigger'], 'scenario.trigger', 300)
        require(isinstance(scenario['category'], str) and scenario['category'] in CATEGORIES,
                'scenario: unsupported category')
        if scenario['steps'] is not None:
            steps(scenario['steps'], 'scenario.steps')
    for scenario in scenarios:
        require(isinstance(scenario['recovery'], list), 'scenario.recovery: expected list')
        for recovery in scenario['recovery']:
            fields(recovery, {'label', 'to'}, where='recovery')
            text(recovery['label'], 'recovery.label', 80)
            require(isinstance(recovery['to'], str) and recovery['to'] in ids,
                    'recovery: unknown destination scenario')


def validate(model):
    fields(model, {'schema_version', 'title', 'scope', 'assumptions', 'sources',
                   'actors', 'subjects', 'use_cases'}, where='model')
    require(type(model['schema_version']) is int and model['schema_version'] == 1,
            'model: unsupported schema_version')
    text(model['title'], 'title', 120)
    text(model['scope'], 'scope')
    require(isinstance(model['assumptions'], list), 'assumptions: expected list')
    for assumption in model['assumptions']:
        text(assumption, 'assumption')
    sources = source_ids(model['sources'])
    actors = mapping(model['actors'], 'actors')
    subjects = mapping(model['subjects'], 'subjects')
    cases = mapping(model['use_cases'], 'use_cases')
    reached_subjects = set()
    for actor in model['actors'].values():
        fields(actor, {'name', 'subjects'}, where='actor')
        text(actor['name'], 'actor.name', 48)
        references(actor['subjects'], subjects, 'actor.subjects')
        reached_subjects.update(actor['subjects'])
    require(reached_subjects == subjects, 'subjects: unreachable subject')
    reached_cases = set()
    for subject in model['subjects'].values():
        fields(subject, {'name', 'cases'}, where='subject')
        text(subject['name'], 'subject.name', 80)
        references(subject['cases'], cases, 'subject.cases')
        reached_cases.update(subject['cases'])
    require(reached_cases == cases, 'use_cases: unreachable goal')
    for key, case in model['use_cases'].items():
        validate_case(key, case, sources)
    return model
