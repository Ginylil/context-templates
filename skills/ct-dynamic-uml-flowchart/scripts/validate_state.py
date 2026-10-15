#!/usr/bin/env python3
"""Verify bounded state views, explicit transition routes and labels on arrows."""
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model', type=Path, help='State JSON or generated standalone HTML')
    args = parser.parse_args()
    try:
        raw = args.model.read_text(encoding='utf-8')
        if raw.lstrip().startswith('<'):
            match = re.search(r'<script id="diagram-data" type="application/json">(.*?)</script>', raw, re.S)
            if match is None:
                raise ValueError('HTML: missing embedded diagram model')
            raw = match[1]
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location('state_renderer', Path(__file__).with_name('render.py'))
        renderer = importlib.util.module_from_spec(spec); spec.loader.exec_module(renderer)
        renderer.validate(json.loads(raw), expected='state')
        print(f'Valid state diagram: {args.model} (maximum seven nodes per view; labels on arrows)')
    except (ValueError, OSError, RecursionError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
