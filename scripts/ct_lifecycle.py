#!/usr/bin/env python3
"""Synchronize lifecycle guides and synthetic hashes; scripts assemble from manifests."""
from __future__ import annotations

import argparse
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANAGER = ROOT / "skills/ct-product-manage-project"


def outputs():
    catalog = json.loads((MANAGER / "assets/catalog.json").read_text(encoding="utf-8"))
    names = [item["skill"] for item in catalog]
    if len(names) != 20 or len(set(names)) != 20:
        raise ValueError("Expected exactly 20 unique lifecycle skill identities")
    define = ROOT / "skills/ct-product-define-project"
    planner = ROOT / "skills/ct-rnd-plan-development"
    result = {}
    for name in names:
        folder = ROOT / "skills" / name
        if not name.startswith("ct-") or not (folder / "SKILL.md").is_file():
            raise ValueError(f"Missing canonical lifecycle skill: {name}")
        if name != define.name:
            result[folder / "references/definition-contract.md"] = (define / "references/contract.md").read_bytes()
    result[MANAGER / "references/planning-contract.md"] = (planner / "references/contract.md").read_bytes()
    for name in ("ct-devops-release-apple-app", "ct-devops-release-android-app"):
        folder = ROOT / "skills" / name / "assets"
        intake = json.loads((folder / "example-input.json").read_text(encoding="utf-8"))
        report = json.loads((folder / "example-output.json").read_text(encoding="utf-8"))
        report["input_sha256"] = hashlib.sha256(json.dumps(intake, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        result[folder / "example-output.json"] = (json.dumps(report, indent=2) + "\n").encode("utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        expected = outputs()
        drift = [path for path, data in expected.items() if not path.is_file() or path.read_bytes() != data]
        if args.check:
            if drift:
                raise ValueError("Lifecycle support drift: " + ", ".join(str(p.relative_to(ROOT)) for p in drift))
        else:
            for path in drift:
                if path.is_symlink():
                    raise ValueError(f"Refusing generated symlink: {path}")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(expected[path])
        print(f"Lifecycle support {'is current' if args.check else 'synchronized'} ({len(expected)} standalone resources).")
        return 0
    except (ValueError, OSError) as error:
        print(f"Error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
