#!/usr/bin/env python3
"""Assemble the standalone class skill and render its canonical review example."""
import argparse
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build():
    cli = load(ROOT / 'scripts/skills.py', 'class_demo_assembler')
    with tempfile.TemporaryDirectory(prefix='ct-class-review-') as temporary:
        destination = Path(temporary) / 'skills'
        cli.assemble(ROOT, destination, ['ct-dynamic-uml-class'])
        package = destination / 'ct-dynamic-uml-class'
        renderer = load(package / 'scripts/render.py', 'class_demo_renderer')
        model = json.loads((package / 'assets/example.json').read_text(encoding='utf-8'))
        return renderer.render(model, expected='class')


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
