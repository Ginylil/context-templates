"""Validate manifests and assemble deterministic standalone skill payloads."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import re
import zipfile
from pathlib import Path
from .common import PACKAGE_MANIFEST, is_link, valid_name, metadata, snapshot, selected_names
from .limits import check_code_length

# Import repository scanning code, never a selected packaged helper.
_scan_spec = importlib.util.spec_from_file_location(
    "ct_package_secret_scan", Path(__file__).resolve().parents[1] / "secret_scan.py")
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
    if not isinstance(value, str) or value.count("/") != 2 or not value.startswith("shared/"):
        raise ValueError("Expected shared/<family>/<script>.py source")
    _, family, filename = value.split("/")
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
                or type(config["schema_version"]) is not int or config["schema_version"] != 2
                or not isinstance(config["scripts"], list)):
            raise ValueError(f"{folder.name}: invalid package manifest")
        destinations = set()
        for entry in config["scripts"]:
            if not isinstance(entry, dict) or set(entry) != {"source", "destination"}:
                raise ValueError(f"{folder.name}: expected source and destination fields")
            name = entry["destination"]
            if (not isinstance(name, str) or not name.startswith("scripts/")
                    or not safe_script(name[len("scripts/"):])):
                raise ValueError(f"{folder.name}: invalid script destination")
            if name in source or name in destinations:
                raise ValueError(f"{folder.name}: script destination collision: {name}")
            destinations.add(name)
            path = shared_script(root, entry["source"])
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
        if content is not None:
            check_code_length(content[0], name)
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
