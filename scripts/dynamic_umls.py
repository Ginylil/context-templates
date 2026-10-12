#!/usr/bin/env python3
"""Sync standalone skill resources and rebuild review examples from canonical models."""
from __future__ import annotations
import argparse
import base64
import html
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / 'skills/dynamic-umls'
NAMES = {
    'sequence': 'dynamic-sequence-diagram', 'class': 'dynamic-class-diagram',
    'flowchart': 'dynamic-flowchart', 'state': 'dynamic-state-diagram',
    'activity': 'dynamic-activity-diagram', 'component': 'dynamic-component-diagram',
}


def outputs():
    spec = importlib.util.spec_from_file_location('diagram_renderer', CANONICAL / 'scripts/render.py')
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    result = {}
    for kind, name in NAMES.items():
        folder = ROOT / 'skills' / name
        for resource in ('assets/template.html', 'assets/ginylil.png', 'scripts/render.py', 'scripts/validate_flowchart.py', 'scripts/validate_state.py', 'references/authoring.md'):
            result[folder / resource] = (CANONICAL / resource).read_bytes()
        model = CANONICAL / f'assets/examples/{kind}.json'
        result[folder / 'assets/example.json'] = model.read_bytes()
        result[ROOT / f'examples/dynamic-umls/{kind}.html'] = renderer.render(
            json.loads(model.read_text(encoding='utf-8')), expected=kind).encode('utf-8')
    long_model = CANONICAL / 'assets/examples/sequence-long.json'
    result[ROOT / 'skills/dynamic-sequence-diagram/assets/long-example.json'] = long_model.read_bytes()
    result[ROOT / 'examples/dynamic-umls/sequence-long.html'] = renderer.render(
        json.loads(long_model.read_text(encoding='utf-8')), expected='sequence').encode('utf-8')
    cards = []
    descriptions = {'sequence': 'Messages between participants, in time order.',
        'class': 'Ownership, cardinality and specialization.', 'flowchart': 'A vertical decision path, side retry rail and nested repair flow.',
        'state': 'Events, guards and an order lifecycle.', 'activity': 'Concurrent branches with a fork and join.',
        'component': 'Repository boundaries and dependencies.'}
    titles = {'sequence':'The three-party sign-in','class':'An order, made explicit',
        'flowchart':'Is this change ready?','state':'The life of an order',
        'activity':'Two checks, one dispatch','component':'One source, three agents'}
    # Simple inline thumbnails convey the shape of each diagram without fetching
    # images or duplicating the full interactive renderer in this gallery.
    thumbnails = {
        'sequence':'<path d="M50 24v94M120 24v94M190 24v94" stroke-dasharray="3 4"/><path d="M50 45h70m0 24h70m0 24H50"/><circle cx="120" cy="45" r="3"/><circle cx="190" cy="69" r="3"/>',
        'class':'<path d="M25 28h60v64H25zM155 28h60v64h-60zM25 48h60M155 48h60M85 62h70"/><path d="m85 62 7-5 7 5-7 5z" fill="#efa86d"/>',
        'flowchart':'<rect x="70" y="8" width="60" height="22" rx="10"/><path d="M100 30v15m0 0 24 20-24 20-24-20zM100 85v23M124 65h45v15M199 91h22V40H130"/><rect x="70" y="108" width="60" height="22" rx="10"/><rect x="139" y="80" width="60" height="22"/><path d="M146 80v22M192 80v22"/>',
        'state':'<circle cx="22" cy="65" r="6" fill="#a5cdb3"/><path d="M28 65h22M100 65h36M186 65h26"/><rect x="50" y="45" width="50" height="40" rx="9"/><rect x="136" y="45" width="50" height="40" rx="9"/><circle cx="218" cy="65" r="8"/><circle cx="218" cy="65" r="4" fill="#a5cdb3"/>',
        'activity':'<path d="M50 30h140M50 104h140M75 30v22M165 30v22M75 80v24M165 80v24"/><rect x="45" y="52" width="60" height="28" rx="8"/><rect x="135" y="52" width="60" height="28" rx="8"/>',
        'component':'<path d="M94 60h52M120 35v-10H50v35m70-35h70v35" stroke-dasharray="4 4"/><rect x="26" y="60" width="48" height="35"/><rect x="96" y="45" width="48" height="35"/><rect x="166" y="60" width="48" height="35"/>',
    }
    for number,(kind,name) in enumerate(NAMES.items(),1):
        cards.append(f'<a class="card" href="{kind}.html"><span class="meta">0{number} / {kind.upper()}</span><svg viewBox="0 0 240 140" aria-hidden="true" fill="none" stroke="#a5cdb3" stroke-width="2">{thumbnails[kind]}</svg><h2>{html.escape(titles[kind])} <span>↗</span></h2><p>{descriptions[kind]}</p><code>/{name}</code></a>')
    gallery = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Dynamic UMLs — Ginylil</title><style>
*{box-sizing:border-box}body{margin:0;background:#191b19;color:#eeeade;font:16px/1.5 system-ui,-apple-system,sans-serif}main{max-width:1180px;margin:auto;padding:28px 40px 48px}header{display:flex;justify-content:space-between;border-bottom:1px solid #465046;padding-bottom:20px;font-size:13px}a{color:inherit}.brand{display:flex;align-items:center;gap:9px;font-weight:650;font-size:19px;text-decoration:none}.brand img{width:40px;height:40px;object-fit:contain;opacity:.8}.eyebrow,.meta,code{font:11px ui-monospace,Consolas,monospace;letter-spacing:1px;color:#a5cdb3}.eyebrow{margin-top:45px}h1{font:400 clamp(36px,5vw,64px)/1.1 Georgia,serif;letter-spacing:-2px;margin:12px 0 18px}.lede{max-width:730px;color:#afbaad;margin:0 0 35px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.card{display:block;border:1px solid #465046;text-decoration:none;padding:22px;background:#202420}.card:hover{border-color:#efa86d}.card:focus-visible{outline:3px solid #efa86d;outline-offset:4px}.card svg{display:block;width:100%;height:125px;margin:14px 0}.card h2{font:400 23px/1.2 Georgia,serif;margin:14px 0}.card h2 span{color:#efa86d}.card p{font-size:13px;color:#afbaad;min-height:40px}.card code{font-size:10px;letter-spacing:0;overflow-wrap:anywhere}.note{font-size:12px;color:#afbaad;border-top:1px solid #465046;margin-top:30px;padding-top:20px}@media(max-width:850px){.grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:560px){main{padding:20px}.grid{grid-template-columns:1fr}header{align-items:center;gap:12px}h1{letter-spacing:-1px}.eyebrow{margin-top:32px}}</style></head><body><main><header><a class="brand" href="https://contexttemplates.com"><img src="__GINYLIL_LOGO__" alt="Ginylil — Brewing Brilliant Code"></a><span>Context Templates / Example collection</span></header><p class="eyebrow">DYNAMIC UMLs / SIX WAYS TO SEE A SYSTEM</p><h1>Understand it.<br>One step at a time.</h1><p class="lede">Choose a diagram to explore. Each example is a standalone HTML file with playback, an element inspector, and visible assumptions. Open it locally — everything works offline.</p><div class="grid">''' + ''.join(cards) + '''</div><p class="note"><a href="sequence-long.html">Long sequence: 32 messages across six participants ↗</a></p><p class="note">Examples for template review. The sequence, class, flowchart, state and activity examples are illustrative; the component view follows the local repository. Flowcharts are general process notation rather than a formal UML diagram type. These pages explain systems; they do not execute them.</p></main></body></html>
'''
    gallery = gallery.replace('__GINYLIL_LOGO__', 'data:image/png;base64,' + base64.b64encode((CANONICAL / 'assets/ginylil.png').read_bytes()).decode('ascii'))
    result[ROOT / 'examples/dynamic-umls/index.html'] = gallery.encode('utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if generated resources/examples have drifted')
    args = parser.parse_args()
    stale = []
    for path, content in outputs().items():
        if path.exists() and path.read_bytes() == content:
            continue
        if args.check:
            stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    if stale:
        parser.exit(1, 'Generated resources drifted; run python scripts/dynamic_umls.py:\n' + '\n'.join(stale) + '\n')
    print('Dynamic UML resources and seven examples are current.' if args.check else 'Updated Dynamic UML resources and seven examples.')


if __name__ == '__main__':
    main()
