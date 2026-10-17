#!/usr/bin/env python3
"""Validate, assemble and safely install the public skill catalog."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
# Also support importlib-based callers whose sys.path does not include scripts/.
SCRIPT_DIR = str(Path(__file__).resolve().parent)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from skill_tools import installation
from skill_tools.common import (
    ROOT, OWNER, STATE_FILE, TARGETS, PACKAGE_MANIFEST,
    is_link, valid_name, metadata, snapshot, selected_names,
)
from skill_tools.packages import (
    unique_object, safe_script, shared_script, package_payload, payload_snapshot,
    write_package, catalog, assemble,
)
from skill_tools.installation import read_state, install


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    listing = sub.add_parser("list", help="Show installable skills")
    listing.add_argument("--json", action="store_true")
    sub.add_parser("check", help="Validate skill names, metadata, and package boundaries")
    installing = sub.add_parser("install", help="Install copies; refuse conflicts and local edits")
    installing.add_argument("--agent", choices=[*TARGETS, "all"], required=True)
    installing.add_argument("--skill", action="append", default=[])
    installing.add_argument("--home", type=Path, default=Path.home())
    installing.add_argument("--dry-run", action="store_true")
    assembling = sub.add_parser("assemble", help="Create standalone folders in a new output directory")
    assembling.add_argument("--output", type=Path, required=True)
    assembling.add_argument("--skill", action="append", default=[])
    args = parser.parse_args()
    try:
        if args.command == "install":
            agents = list(TARGETS) if args.agent == "all" else [args.agent]
            install(ROOT, args.home.expanduser().resolve(), agents, args.skill, args.dry_run)
        elif args.command == "assemble":
            assemble(ROOT, args.output, args.skill)
        else:
            available = catalog(ROOT)
            if args.command == "check":
                print(f"Validated {len(available)} skill(s)")
            elif args.json:
                print(json.dumps([metadata(folder) for folder in available.values()], indent=2))
            else:
                for name, folder in available.items():
                    print(f"{name}: {metadata(folder)['description']}")
    except (ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
