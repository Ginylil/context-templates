"""Preflight, stage and atomically update owned skill installations."""
from __future__ import annotations
import json
import shutil
import tempfile
from pathlib import Path
from .common import OWNER, STATE_FILE, TARGETS, is_link, snapshot, valid_name, selected_names
from .packages import catalog, package_payload, payload_snapshot, write_package


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
