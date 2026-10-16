"""Catalog identity, filesystem snapshots and shared installation constants."""
from __future__ import annotations
import hashlib
import json
import re
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = "Ginylil/context-templates"
STATE_FILE = ".context-templates-install.json"
TARGETS = {
    "codex": Path(".agents/skills"),
    "cursor": Path(".cursor/skills"),
    "claude": Path(".claude/skills"),
}
PACKAGE_MANIFEST = "assets/package.json"


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


def selected_names(available: dict, names: list[str]) -> list[str]:
    selected = names or list(available)
    if len(selected) != len(set(selected)) or any(name not in available for name in selected):
        raise ValueError("Select distinct skill names from the catalog")
    return selected
