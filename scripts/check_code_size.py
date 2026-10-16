#!/usr/bin/env python3
"""Reject maintained source code over 300 physical lines; no dependencies."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from skill_tools.limits import repository_violations


def main():
    root = Path(__file__).resolve().parents[1]
    try:
        violations = repository_violations(root)
        if violations:
            print('\n'.join(violations), file=sys.stderr)
            return 1
    except (OSError, ValueError) as error:
        print(f'Code size check failed: {error}', file=sys.stderr)
        return 1
    print('Maintained code is at most 300 lines; generated standalone HTML is exempt.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
