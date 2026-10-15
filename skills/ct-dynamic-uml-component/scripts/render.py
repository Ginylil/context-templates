#!/usr/bin/env python3
"""Validate a diagram model and emit one offline HTML file. Standard library only."""
from __future__ import annotations

import argparse
import base64
import html
import importlib.util
import json
import math
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

KINDS = {
    'sequence': {'participant'},
    'class': {'class'},
    'flowchart': {'process', 'decision', 'terminal', 'subprocess'},
    'state': {'state', 'initial', 'final', 'decision'},
    'activity': {'action', 'decision', 'initial', 'final', 'fork', 'join'},
    'component': {'component'},
}
EDGES = {
    'sequence': {'call', 'signal', 'return'},
    'class': {'association', 'composition', 'aggregation', 'inheritance', 'dependency'},
    'flowchart': {'flow'}, 'state': {'transition'}, 'activity': {'flow'},
    'component': {'dependency'},
}
ID = re.compile(r'[a-z][a-z0-9-]{0,63}\Z')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def string(value, where, maximum=4000):
    require(isinstance(value, str) and bool(value.strip()) and len(value) <= maximum,
            f'{where}: expected nonempty text, at most {maximum} characters')


def number(value, where, low=0, high=3000):
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and low <= value <= high, f'{where}: invalid coordinate/size')


def records(value, where, minimum=1):
    require(isinstance(value, list) and len(value) >= minimum and all(isinstance(x, dict) for x in value),
            f'{where}: expected a list of objects (minimum {minimum})')


def identifiers(items, where):
    ids = []
    for item in items:
        value = item.get('id')
        require(isinstance(value, str) and ID.fullmatch(value), f'{where}: invalid id')
        ids.append(value)
    require(len(ids) == len(set(ids)), f'{where}: duplicate ids')
    return set(ids)


def validate(model, expected=None, _depth=0):
    require(_depth <= 4, "subflows: maximum nesting depth is four")
    require(isinstance(model, dict), 'model: expected object')
    kind = model.get('type')
    require(isinstance(kind, str) and kind in KINDS, 'type: unsupported diagram')
    require(expected is None or kind == expected, f'type: expected {expected}, received {kind}')
    for key in ('title', 'lede', 'evidence'):
        string(model.get(key), key)
    for key in ('kicker', 'canvasLabel'):
        if key in model:
            string(model[key], key)
    for key in ('width', 'height'):
        number(model.get(key), key, 200, 3000)
    nodes = model.get('nodes'); records(nodes, 'nodes', 2)
    edges = model.get('edges'); records(edges, 'edges', 1)
    node_ids = identifiers(nodes, 'nodes'); edge_ids = identifiers(edges, 'edges')
    for n in nodes:
        string(n.get('label'), f"node {n['id']}.label", 60)
        string(n.get('detail'), f"node {n['id']}.detail")
        require(isinstance(n.get('kind'), str) and n['kind'] in KINDS[kind], f"node {n['id']}: unsupported shape")
        number(n.get('x'), 'node.x', 0, model['width'])
        number(n.get('y'), 'node.y', 0, model['height'])
        for key in ('w', 'h'):
            if key in n:
                number(n[key], f'node.{key}', 8, 600)
        if 'role' in n:
            string(n['role'], 'node.role', 40)
        for key in ('fields', 'methods'):
            if key in n:
                require(n['kind'] == 'class' and isinstance(n[key], list), f'node.{key}: class members only')
                for member in n[key]:
                    string(member, f'node.{key}', 50)
        width = 24 if n['kind'] in {'initial', 'final'} else n.get('w', 180)
        height = (24 if n['kind'] in {'initial', 'final'} else 8 if n['kind'] in {'fork', 'join'}
                  else 64 + 22 * (len(n.get('fields', [])) + len(n.get('methods', [])))
                  if n['kind'] == 'class' else n.get('h', 66))
        require(width/2 <= n['x'] <= model['width']-width/2
                and height/2 <= n['y'] <= model['height']-height/2, f"node {n['id']}: shape outside canvas")
    for e in edges:
        require(isinstance(e.get('from'), str) and isinstance(e.get('to'), str)
                and e['from'] in node_ids and e['to'] in node_ids, f"edge {e['id']}: unknown endpoint")
        require(e['from'] != e['to'] or kind in {'sequence', 'state'}, 'self edges supported only in sequence and state diagrams')
        require(isinstance(e.get('kind'), str) and e['kind'] in EDGES[kind], f"edge {e['id']}: unsupported relationship")
        string(e.get('label'), 'edge.label', 70); string(e.get('detail'), 'edge.detail')
        for key in ('sourceMultiplicity', 'targetMultiplicity'):
            if key in e:
                require(kind == 'class', 'multiplicity: class diagrams only')
                string(e[key], key, 12)
        if 'via' in e:
            records(e['via'], 'edge.via', 1)
        points = e.get('via', []) + ([e['labelAt']] if 'labelAt' in e else [])
        for p in points:
            require(isinstance(p, dict), 'edge: expected point object')
            number(p.get('x'), 'edge.point.x', 0, model['width'])
            number(p.get('y'), 'edge.point.y', 0, model['height'])
    if kind == 'sequence':
        require(model['height'] >= 142 + (len(edges)-1)*68 + 60, 'sequence: canvas too short for messages')
        require(all(n['y'] <= 52 for n in nodes), 'sequence: participant headers belong above lifelines')
    scenarios = model.get('scenarios'); records(scenarios, 'scenarios')
    identifiers(scenarios, 'scenarios')
    for scenario in scenarios:
        string(scenario.get('label'), 'scenario.label', 50)
        steps = scenario.get('steps'); records(steps, 'scenario.steps')
        for s in steps:
            string(s.get('title'), 'step.title', 100); string(s.get('body'), 'step.body')
            for key, allowed in (('nodes', node_ids), ('edges', edge_ids)):
                require(isinstance(s.get(key), list) and all(isinstance(x, str) and x in allowed for x in s[key])
                        and len(s[key]) == len(set(s[key])), f'step.{key}: unknown or duplicate identifier')
            require(bool(s['nodes']), 'step.nodes: highlight at least one node')
            for e in edges:
                if e['id'] in s['edges']:
                    require(e['from'] in s['nodes'] and e['to'] in s['nodes'], 'step: include highlighted edge endpoints')
    require(isinstance(model.get('assumptions'), list) and model['assumptions'], 'assumptions: state scope explicitly')
    for a in model['assumptions']:
        string(a, 'assumption')
    records(model.get('sources'), 'sources', 0)
    for source in model['sources']:
        string(source.get('label'), 'source.label'); string(source.get('href'), 'source.href')
        parsed = urlsplit(source['href'])
        require(parsed.scheme in {'https', 'http'} and bool(parsed.hostname)
                and parsed.username is None and parsed.password is None, 'source: use credential-free http(s) links')
    records(model.get('legend'), 'legend')
    for item in model['legend']:
        string(item.get('label'), 'legend.label', 100)
        if 'dashed' in item:
            require(isinstance(item['dashed'], bool), 'legend.dashed: expected boolean')
    if kind in {'flowchart', 'state'}:
        children = model.get('subflows', [])
        records(children, 'subflows', 0)
        child_ids = identifiers(children, 'subflows')
        used = set()
        for n in nodes:
            if n['kind'] == 'subprocess' or (kind == 'state' and 'subflow' in n):
                require(n['kind'] == ('state' if kind == 'state' else 'subprocess'), f"node {n['id']}: detail views belong to states or subprocesses")
                require(isinstance(n.get('subflow'), str) and n['subflow'] in child_ids,
                        f"node {n['id']}: detail node must reference a local subflow")
                used.add(n['subflow'])
            else:
                require('subflow' not in n, f"node {n['id']}: only states or subprocesses may reference detail views")
        require(used == child_ids, 'subflows: each child must be referenced by a detail node')
        for child in children:
            try:
                validate(child, expected=kind, _depth=_depth+1)
            except ValueError as error:
                raise ValueError(f"subflow {child['id']}: {error}") from error
        # Load beside this script so standalone installed packages work without path changes.
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location('flow_layout', Path(__file__).with_name('validate_flowchart.py'))
        layout = importlib.util.module_from_spec(spec); spec.loader.exec_module(layout)
        layout.validate_layout(model)
    else:
        require('subflows' not in model and all('subflow' not in n for n in nodes),
                'subflows: supported only in flowcharts and state diagrams')
    return model


def render(model, template=None, expected=None):
    validate(model, expected)
    template = template or Path(__file__).resolve().parents[1] / 'assets/template.html'
    page = template.read_text(encoding='utf-8')
    require(all(page.count(key) == 1 for key in ('__DIAGRAM_DATA__', '__PAGE_TITLE__')) and page.count('__GINYLIL_LOGO__') >= 1,
            'template: expected one title and model placeholder, and at least one logo placeholder')
    # Treat all model text as data. Escape HTML parser delimiters even in a JSON
    # script block. The renderer uses textContent, never model-controlled innerHTML.
    data = json.dumps(model, ensure_ascii=True, separators=(',', ':'), allow_nan=False)
    data = data.replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    logo = 'data:image/png;base64,' + base64.b64encode((Path(__file__).resolve().parents[1] / 'assets/ginylil.png').read_bytes()).decode('ascii')
    # One pass: literal placeholder names inside user data remain untouched.
    return re.sub(r'__PAGE_TITLE__|__DIAGRAM_DATA__|__GINYLIL_LOGO__',
                  lambda match: {'__PAGE_TITLE__': html.escape(model['title']), '__DIAGRAM_DATA__': data, '__GINYLIL_LOGO__': logo}[match[0]], page)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--expect', choices=sorted(KINDS))
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        model = json.loads(args.model.read_text(encoding='utf-8'))
        page = render(model, expected=args.expect)
        if args.check:
            print(f"Valid {model['type']} model: {args.model}")
        else:
            require(args.output is not None, 'provide --output or --check')
            # Exclusive creation preserves existing user artifacts, including links.
            with args.output.open('x', encoding='utf-8', newline='\n') as destination:
                destination.write(page)
            print(args.output.resolve())
    except (ValueError, OSError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
