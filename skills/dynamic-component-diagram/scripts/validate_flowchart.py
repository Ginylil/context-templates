#!/usr/bin/env python3
"""Check bounded, top-down flowcharts and side-routed loops (JSON or emitted HTML)."""
from __future__ import annotations
import argparse
import importlib.util
import itertools
import json
import re
import sys
from pathlib import Path

MAX_NODES = 7  # Project readability policy, not a UML/ISO limit.
GAP = 16
EPS = 1e-7
PORTS = {'top', 'bottom', 'left', 'right'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def box(n, padding=0):
    w, h = n.get('w', 180), n.get('h', 66)
    return (n['x']-w/2-padding, n['y']-h/2-padding,
            n['x']+w/2+padding, n['y']+h/2+padding)


def port(n, side):
    l, t, r, b = box(n)
    return {'top': (n['x'], t), 'bottom': (n['x'], b),
            'left': (l, n['y']), 'right': (r, n['y'])}[side]


def points(e, nodes):
    return [port(nodes[e['from']], e['fromPort']),
            *[(p['x'], p['y']) for p in e.get('via', [])],
            port(nodes[e['to']], e['toPort'])]


def segments(path):
    return list(zip(path, path[1:]))


def intersection(a, b):
    """Return None, a point, or 'overlap' for two orthogonal segments."""
    (x1, y1), (x2, y2) = a
    (u1, v1), (u2, v2) = b
    ah, bh = abs(y1-y2) < EPS, abs(v1-v2) < EPS
    if ah == bh:
        if abs((y1-v1) if ah else (x1-u1)) > EPS:
            return None
        lo = max(min(x1, x2), min(u1, u2)) if ah else max(min(y1, y2), min(v1, v2))
        hi = min(max(x1, x2), max(u1, u2)) if ah else min(max(y1, y2), max(v1, v2))
        if hi < lo-EPS:
            return None
        if hi > lo+EPS:
            return 'overlap'
        return (lo, y1) if ah else (x1, lo)
    if not ah:
        return intersection(b, a)
    if min(x1, x2)-EPS <= u1 <= max(x1, x2)+EPS and min(v1, v2)-EPS <= y1 <= max(v1, v2)+EPS:
        return (u1, y1)
    return None


def touches_interior(segment, bounds):
    (x1, y1), (x2, y2) = segment
    l, t, r, b = bounds
    if abs(y1-y2) < EPS:
        return t+EPS < y1 < b-EPS and max(min(x1, x2), l) < min(max(x1, x2), r)-EPS
    return l+EPS < x1 < r-EPS and max(min(y1, y2), t) < min(max(y1, y2), b)-EPS


def validate_layout(model):
    """Called after model schema validation; geometry matches explicit viewer ports."""
    require(len(model['nodes']) <= MAX_NODES,
            f"flowchart: {len(model['nodes'])} nodes exceeds {MAX_NODES}; extract a subprocess")
    nodes = {n['id']: n for n in model['nodes']}
    for a, b in itertools.combinations(nodes.values(), 2):
        al, at, ar, ab = box(a, GAP/2)
        bl, bt, br, bb = box(b, GAP/2)
        require(ar <= bl or br <= al or ab <= bt or bb <= at,
                f"nodes {a['id']} / {b['id']}: overlap or less than {GAP}px clearance")
    routes = []
    left = min(box(n)[0] for n in nodes.values())
    right = max(box(n)[2] for n in nodes.values())
    for e in model['edges']:
        prefix = f"edge {e['id']}"
        for key in ('fromPort', 'toPort'):
            require(isinstance(e.get(key), str) and e[key] in PORTS, f'{prefix}.{key}: use top/bottom/left/right')
        require(e.get('route') in ('forward', 'loop'), f'{prefix}.route: use forward or loop')
        p = points(e, nodes); segs = segments(p)
        for (x, y), (u, v) in segs:
            require(abs(x-u) < EPS or abs(y-v) < EPS, f'{prefix}: connector must be orthogonal')
            require(abs(x-u)+abs(y-v) > EPS, f'{prefix}: zero-length segment')
        directions = {'top': (0, -1), 'bottom': (0, 1), 'left': (-1, 0), 'right': (1, 0)}
        for side, a, b in [(e['fromPort'], p[0], p[1]), (e['toPort'], p[-1], p[-2])]:
            dx, dy = directions[side]
            require((b[0]-a[0])*dx+(b[1]-a[1])*dy > EPS, f'{prefix}: arrow must enter/exit the chosen port from outside')
        if e['route'] == 'forward':
            require(nodes[e['to']]['y'] > nodes[e['from']]['y'], f'{prefix}: forward flow must move downward')
            require(all(b[1] >= a[1] for a, b in segs), f'{prefix}: forward connector travels upward')
        else:
            require(nodes[e['to']]['y'] < nodes[e['from']]['y'], f'{prefix}: loop must return to an earlier node')
            require(e['fromPort'] in {'left', 'right'} and e['toPort'] in {'left', 'right'},
                    f'{prefix}: loop must leave and enter side ports')
            rising = [(a, b) for a, b in segs if b[1] < a[1]]
            require(rising and all(a[0] == b[0] and (a[0] <= left-32 or a[0] >= right+32) for a, b in rising),
                    f'{prefix}: upward loop must use an outer side rail, at least 32px beyond nodes')
        for n in nodes.values():
            # Use conservative boxes (also for diamonds) so routes stay clear.
            padding = 0 if n['id'] in {e['from'], e['to']} else 12
            require(not any(touches_interior(s, box(n, padding)) for s in segs),
                    f"{prefix}: connector crosses node {n['id']} or its clearance")
        for i, a in enumerate(segs):
            for j in range(i+1, len(segs)):
                hit = intersection(a, segs[j])
                require(hit is None or (j == i+1 and hit == a[1]), f'{prefix}: self-crossing or overlapping route')
        routes.append((e, p, segs))
    for (a, ap, aseg), (b, bp, bseg) in itertools.combinations(routes, 2):
        allowed = {point for node, point in [(a['from'], ap[0]), (a['to'], ap[-1])]
                   for other, q in [(b['from'], bp[0]), (b['to'], bp[-1])] if node == other and point == q}
        for s, t in itertools.product(aseg, bseg):
            hit = intersection(s, t)
            require(hit is None or (hit != 'overlap' and hit in allowed),
                    f"edges {a['id']} / {b['id']}: crossing or overlapping connectors; reroute or extract a subprocess")
    return model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model', type=Path, help='Flowchart JSON or generated standalone HTML')
    args = parser.parse_args()
    try:
        raw = args.model.read_text(encoding='utf-8')
        if raw.lstrip().startswith('<'):
            match = re.search(r'<script id="diagram-data" type="application/json">(.*?)</script>', raw, re.S)
            require(match is not None, 'HTML: missing embedded diagram model')
            raw = match[1]
        model = json.loads(raw)
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location('flow_renderer', Path(__file__).with_name('render.py'))
        renderer = importlib.util.module_from_spec(spec); spec.loader.exec_module(renderer)
        renderer.validate(model, expected='flowchart')  # Includes nested schema and geometry.
        print(f'Valid top-down flowchart: {args.model} (maximum {MAX_NODES} nodes per view)')
    except (ValueError, OSError, RecursionError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
