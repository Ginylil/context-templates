#!/usr/bin/env python3
"""Validate, package, and safely install the public skill catalog. No dependencies."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
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
PACKAGE_MANIFEST = "assets/package.json"

# This is repository tooling, never an imported or executed packaged helper.
_scan_spec = importlib.util.spec_from_file_location("ct_package_secret_scan", Path(__file__).with_name("secret_scan.py"))
_scanner = importlib.util.module_from_spec(_scan_spec)
_scan_spec.loader.exec_module(_scanner)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON property in package manifest")
        result[key] = value
    return result


def safe_script(value: str) -> bool:
    return (isinstance(value, str) and bool(re.fullmatch(r"[a-z][a-z0-9_]*\.py", value))
            and valid_name(value[:-3].replace("_", "-")))


def shared_script(root: Path, value: str) -> Path:
    # Only literal shared/<family>/<script>.py sources, no arbitrary repo paths.
    if not isinstance(value, str) or value.count("/") != 1:
        raise ValueError("Expected shared family/script.py source")
    family, filename = value.split("/")
    if not valid_name(family) or not safe_script(filename):
        raise ValueError("Invalid shared script source")
    path = root / "shared"
    for part in (family, filename):
        if is_link(path) or not path.is_dir():
            raise ValueError("Shared script ancestors must be real directories")
        path /= part
    if is_link(path) or not path.is_file():
        raise ValueError(f"Missing or linked shared script: {value}")
    return path


def package_payload(root: Path, folder: Path) -> dict:
    """Read a complete payload as bytes/modes. No templates, imports or hooks."""
    source = snapshot(folder)
    payload = {}
    for name, fingerprint in source.items():
        if name == PACKAGE_MANIFEST or fingerprint == "directory":
            continue
        payload[name] = ((folder / name).read_bytes(), fingerprint.startswith("1:"))
    manifest = folder / PACKAGE_MANIFEST
    if manifest.is_file():
        config = json.loads(manifest.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        if (not isinstance(config, dict) or set(config) != {"schema_version", "scripts"}
                or type(config["schema_version"]) is not int or config["schema_version"] != 1
                or not isinstance(config["scripts"], dict)):
            raise ValueError(f"{folder.name}: invalid package manifest")
        for filename, shared in config["scripts"].items():
            if not safe_script(filename):
                raise ValueError(f"{folder.name}: invalid script destination")
            name = "scripts/" + filename
            if name in source:
                raise ValueError(f"{folder.name}: script destination collision: {name}")
            path = shared_script(root, shared)
            payload[name] = (path.read_bytes(), bool(path.stat().st_mode & 0o111))
    # Retain truly empty source directories; omit a manifest-only assets folder.
    for name, fingerprint in source.items():
        if fingerprint == "directory" and not any((folder / name).iterdir()):
            payload[name] = None
    for name in list(payload):
        for parent in Path(name).parents:
            if str(parent) != ".":
                payload.setdefault(parent.as_posix() + "/", None)
    seen = set()
    for name, content in sorted(payload.items()):
        identity = name.rstrip("/").casefold()
        if identity in seen:
            raise ValueError(f"{folder.name}: case or file/directory collision: {name}")
        seen.add(identity)
        if content is not None and _scanner.findings(content[0], name):
            raise ValueError(f"{folder.name}: credential/signing-file finding in {name}; contents redacted")
    return dict(sorted(payload.items()))


def payload_snapshot(payload: dict) -> dict[str, str]:
    return {name: "directory" if value is None else
            f"{int(value[1])}:{hashlib.sha256(value[0]).hexdigest()}" for name, value in payload.items()}


def write_package(payload: dict, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    for name, value in payload.items():
        path = destination / name
        if value is None:
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value[0])
            path.chmod(0o755 if value[1] else 0o644)


def selected_names(available: dict, names: list[str]) -> list[str]:
    selected = names or list(available)
    if len(selected) != len(set(selected)) or any(name not in available for name in selected):
        raise ValueError("Select distinct skill names from the catalog")
    return selected


def assemble(root: Path, output: Path, names: list[str]) -> None:
    """Materialize an uninstalled catalog for local execution/review, exclusively."""
    available = catalog(root)
    selected = selected_names(available, names)
    payloads = {name: package_payload(root, available[name]) for name in selected}
    if output.exists() or is_link(output):
        raise ValueError(f"{output}: assembly output must not exist")
    resolved = output.resolve()
    for source in (root / "skills", root / "shared"):
        if resolved == source.resolve() or source.resolve() in resolved.parents:
            raise ValueError("Assembly output cannot be inside source resources")
    output.mkdir(parents=True)
    for name, payload in payloads.items():
        write_package(payload, output / name)
    print(f"Assembled {len(payloads)} skill(s) in {output}")


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
        if (root / "shared").exists() and PACKAGE_MANIFEST not in files:
            raise ValueError(f"{folder.name}: source catalog requires assets/package.json")
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
        package_payload(root, folder)
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
    selected = selected_names(available, names)
    payloads = {name: package_payload(root, available[name]) for name in selected}
    source_hashes = {name: payload_snapshot(payloads[name]) for name in selected}
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
            write_package(payloads[name], staged)
            if snapshot(staged) != hashes or payload_snapshot(package_payload(root, source)) != hashes:
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
    payloads = {name: package_payload(root, folder) for name, folder in available.items()}
    output.mkdir(parents=True, exist_ok=True)
    entries = []
    for name, folder in available.items():
        archive = output / f"{name}.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for file, content in payloads[name].items():
                if content is None:
                    continue
                entry = zipfile.ZipInfo(f"{name}/{file}", date_time=(2020, 1, 1, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                mode = 0o755 if content[1] else 0o644
                entry.external_attr = (0o100000 | mode) << 16
                bundle.writestr(entry, content[0])
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
    assembling = sub.add_parser("assemble", help="Create standalone folders in a new output directory")
    assembling.add_argument("--output", type=Path, required=True)
    assembling.add_argument("--skill", action="append", default=[])
    args = parser.parse_args()
    try:
        if args.command == "install":
            agents = list(TARGETS) if args.agent == "all" else [args.agent]
            install(ROOT, args.home.expanduser().resolve(), agents, args.skill, args.dry_run)
        elif args.command == "build":
            build(ROOT, args.output)
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
