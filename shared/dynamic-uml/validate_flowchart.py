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
    w, h = (24, 24) if n.get('kind') in {'initial', 'final'} else (n.get('w', 180), n.get('h', 66))
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


def label_geometry(e, path):
    value = e.get('labelOn')
    require(isinstance(value, dict), f"edge {e['id']}.labelOn: select an arrow segment")
    segment, at = value.get('segment'), value.get('at', 0.5)
    require(isinstance(segment, int) and not isinstance(segment, bool) and 0 <= segment < len(path)-1,
            f"edge {e['id']}.labelOn.segment: invalid segment")
    require(isinstance(at, (int, float)) and not isinstance(at, bool) and 0 <= at <= 1,
            f"edge {e['id']}.labelOn.at: expected a fraction between 0 and 1")
    a, b = path[segment], path[segment+1]
    length = abs(b[0]-a[0])+abs(b[1]-a[1])
    # Conservative estimate for the viewer's 11px monospace text plus its backing.
    half = len(e['label'])*7/2+8
    require(min(at*length, (1-at)*length) >= half+12,
            f"edge {e['id']}: label does not fit its arrow segment; lengthen the route or shorten the label")
    x, y = a[0]+(b[0]-a[0])*at, a[1]+(b[1]-a[1])*at
    return (x-half, y-10, x+half, y+10) if a[1] == b[1] else (x-10, y-half, x+10, y+half)


def validate_layout(model):
    """Called after model schema validation; geometry matches explicit viewer ports."""
    kind = model.get('type', 'flowchart')
    horizontal = kind == 'state' and model.get('orientation', 'horizontal') == 'horizontal'
    axis = 0 if horizontal else 1
    require(kind != 'state' or model.get('orientation', 'horizontal') in ('horizontal', 'vertical'), 'state.orientation: use horizontal or vertical')
    require(len(model['nodes']) <= MAX_NODES,
            f"{kind}: {len(model['nodes'])} nodes exceeds {MAX_NODES}; extract a detail view")
    nodes = {n['id']: n for n in model['nodes']}
    for a, b in itertools.combinations(nodes.values(), 2):
        al, at, ar, ab = box(a, GAP/2)
        bl, bt, br, bb = box(b, GAP/2)
        require(ar <= bl or br <= al or ab <= bt or bb <= at,
                f"nodes {a['id']} / {b['id']}: overlap or less than {GAP}px clearance")
    routes = []
    left = min(box(n)[0] for n in nodes.values())
    right = max(box(n)[2] for n in nodes.values())
    top = min(box(n)[1] for n in nodes.values())
    bottom = max(box(n)[3] for n in nodes.values())
    labels = []
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
        source, target = nodes[e['from']], nodes[e['to']]
        key = 'x' if horizontal else 'y'
        if e['route'] == 'forward':
            direction = 'rightward' if horizontal else 'downward'
            require(target[key] > source[key], f'{prefix}: forward flow must move {direction}')
            require(all(b[axis] >= a[axis] for a, b in segs), f'{prefix}: forward connector travels backward')
        else:
            require(target[key] < source[key] or (kind == 'state' and e['from'] == e['to']),
                    f'{prefix}: loop must return to an earlier node or state self-transition')
            sides = {'top', 'bottom'} if horizontal else {'left', 'right'}
            require(e['fromPort'] in sides and e['toPort'] in sides,
                    f'{prefix}: loop must leave and enter outer side ports')
            returning = [(a, b) for a, b in segs if b[axis] < a[axis]]
            def outer(a, b):
                return (a[1] == b[1] and (a[1] <= top-32 or a[1] >= bottom+32)) if horizontal else (a[0] == b[0] and (a[0] <= left-32 or a[0] >= right+32))
            require(returning and all(outer(a, b) for a, b in returning),
                    f'{prefix}: return loop must use an outer side rail, at least 32px beyond nodes')
        if kind == 'state':
            require('labelAt' not in e, f'{prefix}: state labels must use labelOn, not floating labelAt')
            labels.append((e, label_geometry(e, p)))
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
    for e, bounds in labels:
        l, t, r, b = bounds
        for n in nodes.values():
            nl, nt, nr, nb = box(n, 4)
            require(r <= nl or nr <= l or b <= nt or nb <= t,
                    f"edge {e['id']}: transition label collides with node {n['id']}")
        for other, _, segs in routes:
            if other['id'] != e['id']:
                require(not any(touches_interior(segment, bounds) for segment in segs),
                        f"edge {e['id']}: label covers another transition {other['id']}")
    for (a, (al, at, ar, ab)), (b, (bl, bt, br, bb)) in itertools.combinations(labels, 2):
        require(ar <= bl or br <= al or ab <= bt or bb <= at,
                f"edges {a['id']} / {b['id']}: overlapping transition labels")
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
