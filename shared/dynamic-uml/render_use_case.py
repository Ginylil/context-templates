"""Validate, render or recover one offline actor-first use-case explorer."""
from __future__ import annotations

import argparse
import base64
import html
import json
import re
import sys
from pathlib import Path

from use_case_model import validate

RUNTIME = ('setup.js', 'layout.js', 'scenario.js', 'render.js', 'events.js')
STYLES = ('styles.css', 'nodes.css', 'support.css')


def read_json(path):
    if path.stat().st_size > 5_000_000:
        raise ValueError('model: exceeds 5 MB')
    return validate(json.loads(path.read_text(encoding='utf-8')))


def embedded_model(page):
    found = re.findall(r'<script id="use-case-model" type="application/json">(.*?)</script>',
                       page, re.S)
    if len(found) != 1:
        raise ValueError('HTML must contain exactly one embedded use-case model')
    return validate(json.loads(found[0]))


def provenance(model):
    escape = html.escape
    assumptions = ''.join(f'<li>{escape(a)}</li>' for a in model['assumptions'])
    sources = []
    for source in model['sources']:
        reference = source['reference']
        label = f"{source['id']}: {source['label']}"
        if reference.startswith(('https://', 'http://')):
            item = f'<a href="{escape(reference, quote=True)}">{escape(label)}</a>'
        else:
            item = f'{escape(label)} — {escape(reference)}'
        sources.append(f'<li>{item}</li>')
    return (f'<h3>Scope &amp; assumptions</h3><p>{escape(model["scope"])}</p>'
            f'<ul>{assumptions}</ul><h3>Inspected sources</h3>'
            f'<ul>{"".join(sources) or "<li>No inspected sources supplied.</li>"}</ul>'
            '<p>Evidence labels describe the author’s assessment; structural validation '
            'does not prove runtime behavior. Trigger arrows are an exploration convention; '
            'scenario actions are separate from UML use-case relationships.</p>')


def render(model, package=None):
    validate(model)
    package = package or Path(__file__).resolve().parents[1]
    assets = package / 'assets/use-case'
    page = (assets / 'template.html').read_text(encoding='utf-8')
    logo = base64.b64encode((package / 'assets/ginylil.png').read_bytes()).decode('ascii')
    values = {
        '__TITLE__': html.escape(model['title']),
        '__SCOPE__': html.escape(model['scope']),
        '__LOGO__': 'data:image/png;base64,' + logo,
        '__STYLES__': '\n'.join((assets / name).read_text(encoding='utf-8') for name in STYLES),
        '__PROVENANCE__': provenance(model),
        '__RUNTIME__': '\n'.join((assets / name).read_text(encoding='utf-8') for name in RUNTIME),
    }
    data = json.dumps(model, ensure_ascii=True).replace('&', '\\u0026')
    data = data.replace('<', '\\u003c').replace('>', '\\u003e')
    values['__MODEL__'] = data
    pattern = '|'.join(re.escape(marker) for marker in values)
    return re.sub(pattern, lambda match: values[match[0]], page)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('validate', 'render', 'extract'):
        command = sub.add_parser(name)
        command.add_argument('input', type=Path)
        if name != 'validate':
            command.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'extract':
            model = embedded_model(args.input.read_text(encoding='utf-8'))
            output = json.dumps(model, indent=2, ensure_ascii=False) + '\n'
        else:
            model = read_json(args.input)
            output = render(model) if args.command == 'render' else None
        if output is not None:
            with args.output.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(output)
            print(args.output)
        else:
            print('Valid use-case model')
    except (ValueError, OSError, TypeError) as error:
        parser.exit(2, f'{error}\n')


if __name__ == '__main__':
    main()
