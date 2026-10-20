#!/usr/bin/env python3
"""Assemble the review-only class-camera prototype into one offline HTML file."""
import argparse
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'prototypes/class-camera'


def build():
    page = (SOURCE / 'template.html').read_text(encoding='utf-8')
    fragments = {'STYLES': 'styles.css', 'MODEL': 'model.js', 'LAYOUT': 'layout.js',
                 'ROUTING': 'routing.js', 'VIEW': 'view.js', 'CAMERA': 'camera.js',
                 'INPUT': 'input.js', 'TOUR': 'tour.js'}
    for key, filename in fragments.items():
        marker = f'__{key}__\n'
        if page.count(marker) != 1:
            raise ValueError(f'Expected one standalone {marker.strip()} marker')
        page = page.replace(marker, (SOURCE / filename).read_text(encoding='utf-8'))
    logo = (ROOT / 'skills/ct-dynamic-uml/assets/ginylil.png').read_bytes()
    return page.replace('__LOGO__', 'data:image/png;base64,' + base64.b64encode(logo).decode('ascii'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8', newline='\n') as destination:
        destination.write(build())
    print(args.output.resolve())


if __name__ == '__main__':
    main()
