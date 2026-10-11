#!/usr/bin/env python3
"""Validate, package, and safely install the public skill catalog. No dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import stat
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OWNER = "Ginylil/context-templates"
STATE_FILE = ".context-templates-install.json"
TARGETS = {
    "codex": Path(".agents/skills"),
    "cursor": Path(".cursor/skills"),
    "claude": Path(".claude/skills"),
}


def is_link(path: Path) -> bool:
    """Include Windows junctions/reparse points on Python versions before 3.12."""
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except FileNotFoundError:
        return False
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT) or path.is_symlink()


def valid_name(name: str) -> bool:
    reserved = {"synced", "anthropic-skills", "con", "prn", "aux", "nul"}
    reserved.update(f"{prefix}{i}" for prefix in ("com", "lpt") for i in range(1, 10))
    return bool(
        isinstance(name, str)
        and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)
        and len(name) <= 64
        and name not in reserved
    )


def metadata(folder: Path) -> dict[str, str]:
    text = (folder / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n(.+)", text, re.DOTALL)
    if not match:
        raise ValueError(f"{folder}: expected YAML frontmatter and nonempty instructions")
    # Keep public frontmatter deliberately small and unambiguous. JSON strings
    # are valid YAML scalars and can be validated without a YAML dependency.
    result = {}
    for line in match[1].splitlines():
        if not line.strip():
            continue
        field = re.fullmatch(r"(name|description): (.+)", line)
        if not field or field[1] in result:
            raise ValueError(f"{folder}: use only single-line name and description fields")
        value = field[2].strip()
        if value.startswith('"'):
            value = json.loads(value)
        elif not re.fullmatch(r"[a-z0-9-]+", value):
            raise ValueError(f"{folder}: quote {field[1]} as a JSON string")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{folder}: {field[1]} must be a nonempty string")
        result[field[1]] = value
    if set(result) != {"name", "description"}:
        raise ValueError(f"{folder}: name and description are required")
    if not valid_name(result["name"]) or result["name"] != folder.name:
        raise ValueError(f"{folder}: name must match its folder and use lowercase hyphens")
    if len(result["description"]) > 1024:
        raise ValueError(f"{folder}: description exceeds 1024 characters")
    return result


def snapshot(folder: Path) -> dict[str, str]:
    """Detect edits, additions, removals, executable-bit changes, and unsafe links."""
    if is_link(folder) or not folder.is_dir():
        raise ValueError(f"{folder}: expected a real skill directory, not a link or file")
    files = {}
    for path in sorted(folder.rglob("*")):
        if is_link(path):
            raise ValueError(f"{path}: symlinks/junctions are not allowed inside skill packages")
        if path.is_dir():
            files[path.relative_to(folder).as_posix() + "/"] = "directory"
            continue
        if not path.is_file():
            raise ValueError(f"{path}: unsupported file type")
        executable = bool(path.stat().st_mode & 0o111)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        files[path.relative_to(folder).as_posix()] = f"{int(executable)}:{digest}"
    return files


def catalog(root: Path) -> dict[str, Path]:
    skills_root = root / "skills"
    if is_link(skills_root) or not skills_root.is_dir():
        raise ValueError("Expected a real skills/ directory")
    found = {}
    for folder in sorted(skills_root.iterdir()):
        if not folder.is_dir() or is_link(folder):
            raise ValueError(f"{folder}: skills/ must contain only skill folders")
        files = snapshot(folder)
        info = metadata(folder)
        for file in files:
            parts = Path(file).parts
            if any(part.startswith(".") or part == "__pycache__" for part in parts):
                raise ValueError(f"{folder / file}: hidden/generated files cannot be published")
            if file.endswith("/"):
                if parts[0] not in ("agents", "scripts", "references", "assets"):
                    raise ValueError(f"{folder / file}: unsupported skill resource directory")
                continue
            if len(parts) == 1 and file not in ("SKILL.md", "LICENSE", "LICENSE.md"):
                raise ValueError(f"{folder / file}: use agents/, scripts/, references/, or assets/")
            if len(parts) > 1 and parts[0] not in ("agents", "scripts", "references", "assets"):
                raise ValueError(f"{folder / file}: unsupported skill resource directory")
        found[info["name"]] = folder
    if not found:
        raise ValueError("No skills found")
    return found


def read_state(base: Path) -> dict:
    path = base / STATE_FILE
    if is_link(path):
        raise ValueError(f"{path}: refusing a linked ownership manifest")
    if not path.exists():
        return {"schema_version": 1, "owner": OWNER, "skills": {}}
    state = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(state, dict)
        or state.get("schema_version") != 1
        or state.get("owner") != OWNER
        or not isinstance(state.get("skills"), dict)
    ):
        raise ValueError(f"{path}: invalid ownership manifest; nothing was changed")
    for name, hashes in state["skills"].items():
        if not valid_name(name) or not isinstance(hashes, dict):
            raise ValueError(f"{path}: invalid managed skill record")
        if not all(isinstance(k, str) and isinstance(v, str) for k, v in hashes.items()):
            raise ValueError(f"{path}: invalid managed file hashes")
    return state


def install(root: Path, home: Path, agents: list[str], names: list[str], dry_run: bool) -> None:
    available = catalog(root)
    selected = names or list(available)
    if len(selected) != len(set(selected)) or any(name not in available for name in selected):
        raise ValueError("Select distinct skill names from the catalog")
    source_hashes = {name: snapshot(available[name]) for name in selected}
    plans = []
    # Preflight ALL requested destinations before creating or replacing anything.
    for agent in agents:
        base = home / TARGETS[agent]
        if is_link(base.parent) or is_link(base) or (base.exists() and not base.is_dir()):
            raise ValueError(f"{base}: expected a real destination directory")
        state = read_state(base)
        for name in selected:
            destination = base / name
            exists = destination.exists() or is_link(destination)
            previous = state["skills"].get(name)
            if exists and previous is None:
                raise ValueError(f"{destination}: unmanaged conflict; preserve or rename it first")
            if exists and snapshot(destination) != previous:
                raise ValueError(f"{destination}: locally edited; preserve your changes before updating")
            if not exists or previous != source_hashes[name]:
                plans.append((base, name, available[name], source_hashes[name]))
                print(f"{'would install' if dry_run else 'install'} {name} for {agent}: {destination}")
            else:
                print(f"unchanged {name} for {agent}")
    if dry_run:
        return
    for base, name, source, hashes in plans:
        base.mkdir(parents=True, exist_ok=True)
        state = read_state(base)
        destination = base / name
        with tempfile.TemporaryDirectory(prefix=".context-templates-", dir=base) as temporary:
            staged = Path(temporary) / name
            shutil.copytree(source, staged)
            if snapshot(staged) != hashes:
                raise ValueError(f"{source}: source changed while staging; retry after reviewing it")
            # Recheck immediately before replacement. Keep the previous installation
            # until both the new skill and its ownership receipt have been saved.
            exists = destination.exists() or is_link(destination)
            if exists and snapshot(destination) != state["skills"].get(name):
                raise ValueError(f"{destination}: changed since preflight; refusing replacement")
            backup = Path(temporary) / "previous"
            if exists:
                destination.rename(backup)
            try:
                staged.rename(destination)
                state["skills"][name] = hashes
                receipt = Path(temporary) / "receipt.json"
                receipt.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
                receipt.replace(base / STATE_FILE)
            except Exception:
                if destination.exists():
                    shutil.rmtree(destination)
                if backup.exists():
                    backup.rename(destination)
                raise


def build(root: Path, output: Path) -> None:
    available = catalog(root)
    output.mkdir(parents=True, exist_ok=True)
    entries = []
    for name, folder in available.items():
        archive = output / f"{name}.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for file, fingerprint in snapshot(folder).items():
                if fingerprint == "directory":
                    continue
                entry = zipfile.ZipInfo(f"{name}/{file}", date_time=(2020, 1, 1, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                mode = 0o755 if fingerprint.startswith("1:") else 0o644
                entry.external_attr = (0o100000 | mode) << 16
                bundle.writestr(entry, (folder / file).read_bytes())
        entries.append({
            **metadata(folder),
            "archive": archive.name,
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        })
    (output / "catalog.json").write_text(
        json.dumps({"schema_version": 1, "skills": entries}, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Built {len(entries)} skill archive(s) in {output}")


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
    building = sub.add_parser("build", help="Create per-skill ZIPs and a checksummed catalog")
    building.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    try:
        if args.command == "install":
            agents = list(TARGETS) if args.agent == "all" else [args.agent]
            install(ROOT, args.home.expanduser().resolve(), agents, args.skill, args.dry_run)
        elif args.command == "build":
            build(ROOT, args.output)
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
