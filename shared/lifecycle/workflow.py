#!/usr/bin/env python3
"""Portable lifecycle artifact checks and explicit command evidence. Standard library only."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location("ct_workflow_definition", Path(__file__).with_name("definition.py"))
definition = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(definition)

digest = definition.digest
load = definition.load
require = definition.require
fields = definition.fields
text = definition.text
strings = definition.strings
identifier = definition.identifier
encoded = definition.encoded
REF_FIELDS = "path sha256"


def _helper_module(name):
    spec = importlib.util.spec_from_file_location("ct_" + name, Path(__file__).with_name(name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


_input_checks = _helper_module("workflow_input")
_rule_checks = _helper_module("workflow_rules")


def reference(value, base):
    return _input_checks.reference(value, base, helpers=globals())


def path_value(value, path):
    return _input_checks.path_value(value, path, helpers=globals())


def schema(value, spec, where, context):
    return _input_checks.schema(value, spec, where, context, helpers=globals())


def validate_input(policy, value, base=Path.cwd(), *, historical=False):
    return _input_checks.validate_input(policy, value, base, historical=historical, helpers=globals())


def timestamp(value):
    return _rule_checks.timestamp(value, helpers=globals())


def evidence_valid(item, base, context):
    return _rule_checks.evidence_valid(item, base, context, helpers=globals())


def rule_valid(rule, result, value, context):
    return _rule_checks.rule_valid(rule, result, value, context, helpers=globals())


def file_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(argv, cwd):
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=10, check=False)


def revision(cwd):
    try:
        result = command(["git", "rev-parse", "HEAD"], cwd)
    except FileNotFoundError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def tree_digest(cwd):
    if revision(cwd) is None:
        return None
    # Tracked changes plus the content of nonignored untracked files. No private
    # contents are emitted; only the digest is retained in the command proof.
    diff = subprocess.run(["git", "diff", "--binary", "HEAD", "--"], cwd=cwd,
                          capture_output=True, timeout=10, check=True).stdout
    files = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=cwd,
                           capture_output=True, timeout=10, check=True).stdout
    entries = []
    for raw in sorted(files.split(b"\0")):
        if not raw:
            continue
        path = Path(cwd) / raw.decode("utf-8", errors="surrogateescape")
        require(not path.is_symlink() and path.is_file(), "record: untracked links cannot bind a working tree")
        entries.append({"path_bytes": raw.hex(), "content_sha256": file_digest(path),
                        "executable": bool(path.stat().st_mode & 0o111)})
    return digest({"tracked_diff_sha256": hashlib.sha256(diff).hexdigest(), "untracked_files": entries})


def store_module():
    spec = importlib.util.spec_from_file_location("ct_store_release", Path(__file__).with_name("store_release.py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def interface_module():
    spec = importlib.util.spec_from_file_location("ct_interface_fix", Path(__file__).with_name("interface.py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def validate_output(policy, value, output, base=Path.cwd(), *, historical=False):
    context = validate_input(policy, value, base, historical=historical)
    fields(output, "schema_version project_id skill input_sha256 status summary constraints evidence blockers result", "output")
    definition.version(output["schema_version"])
    require(output["project_id"] == value["project_id"] and output["skill"] == policy["skill"], "output: scope or skill mismatch")
    require(output["input_sha256"] == digest(value), "output: stale input digest")
    require(output["status"] in ("ready", "blocked"), "output.status: expected ready or blocked")
    text(output["summary"], "summary")
    strings(output["constraints"], "output.constraints")
    constraints = set(value["constraints"])
    if context["definition"] is not None:
        constraints.update(context["definition"]["constraints"])
    require(constraints <= set(output["constraints"]), "output: cannot drop constraints")
    definition.records(output["evidence"], "evidence")
    for item in output["evidence"]:
        evidence_valid(item, base, context)
    definition.records(output["blockers"], "blockers")
    for blocker in output["blockers"]:
        fields(blocker, "reason next_action", "blocker")
        text(blocker["reason"], "blocker.reason")
        text(blocker["next_action"], "blocker.next_action")
    require((output["status"] == "blocked") == bool(output["blockers"]), "output: blockers and status disagree")
    schema(output["result"], policy["result"], "result", context)
    for rule in policy["rules"]:
        if rule.get("type") == "store-release":
            store_module().check_report(rule, output["result"], value, context, globals())
        elif rule.get("type") == "interface-fix":
            interface_module().check_report(rule, output["result"], value, context, globals())
    if output["status"] == "ready":
        if policy["requires_definition"]:
            require(context["definition"] is not None and context["definition"]["status"] == "ready-for-planning",
                    "output: ready project definition required")
        if context["ledger"] is not None:
            require(not definition.replay(context["ledger"])["pending_question_ids"], "output: unanswered interview questions")
        for rule in policy["rules"]:
            rule_valid(rule, output["result"], value, context)
    return context


def write_new(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(encoded(value))


def record(argv, cwd, output, timeout=30):
    require(1 <= timeout <= 60, "record: timeout must be 1-60 seconds")
    require(bool(argv) and all(isinstance(x, str) and x for x in argv), "record: explicit command argv required")
    require(cwd.is_dir(), "record: working directory unavailable")
    # Reserve output BEFORE executing so a retry cannot rerun potentially paid or
    # externally mutating work just because its proof destination already exists.
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        proof = {"kind": "ct-command-proof.v1", "argv": argv, "cwd": str(cwd.resolve()),
                 "source_revision": revision(cwd), "working_tree_sha256": tree_digest(cwd),
                 "started_at": dt.datetime.now(dt.timezone.utc).isoformat()}
        try:
            result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                                    errors="replace", timeout=timeout, check=False)
            proof.update(exit_code=result.returncode, timed_out=False, stdout=result.stdout, stderr=result.stderr)
        except subprocess.TimeoutExpired as error:
            def decoded(value):
                return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""
            proof.update(exit_code=124, timed_out=True, stdout=decoded(error.stdout), stderr=decoded(error.stderr))
        except OSError as error:
            proof.update(exit_code=127, timed_out=False, stdout="", stderr=str(error))
        stream.write(encoded(proof))
    return proof


def render(policy, value, output, base):
    validate_output(policy, value, output, base)
    lines = [f"# {policy['purpose']}", "", f"Project: {value['project_id']}", "",
             f"Status: {output['status']}", "", output["summary"], "", "## Result", "",
             "```json", encoded(output["result"]).rstrip(), "```", "", "## Constraints", ""]
    lines.extend(f"- {x}" for x in output["constraints"])
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {x['reason']} Next: {x['next_action']}" for x in output["blockers"])
    if not output["blockers"]:
        lines.append("None.")
    lines.extend(["", "## Evidence", ""])
    lines.extend(f"- {x['id']} ({x['kind']}): {x['reference']['path']} SHA-256 {x['reference']['sha256']}"
                 for x in output["evidence"])
    lines.extend(["", "Artifact validity does not establish customer acceptance, authorization, or live availability.", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    sub = commands.add_parser("inspect-repository", help="Read HEAD and a working-tree fingerprint for intake binding")
    sub.add_argument("path", type=Path)
    sub = commands.add_parser("record", help="Execute explicitly supplied argv and preserve its real result")
    sub.add_argument("--cwd", required=True, type=Path)
    sub.add_argument("--output", required=True, type=Path)
    sub.add_argument("--timeout", type=int, default=30)
    sub.add_argument("argv", nargs=argparse.REMAINDER)
    for name in ("validate-input", "hash-input"):
        sub = commands.add_parser(name)
        sub.add_argument("input", type=Path)
    for name in ("validate-output", "render"):
        sub = commands.add_parser(name)
        sub.add_argument("input", type=Path)
        sub.add_argument("output", type=Path)
        if name == "render":
            sub.add_argument("--output", dest="rendered", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command in ("inspect-repository", "record"):
            policy_path = Path(__file__).resolve().parents[1] / "assets/contract.json"
            if policy_path.is_file() and any(r.get("type") == "store-release" for r in load(policy_path)["rules"]):
                store_module().configuration_module().check_private_paths(args.path if args.command == "inspect-repository" else args.cwd, globals())
        if args.command == "inspect-repository":
            head = revision(args.path)
            require(head is not None, "inspect-repository: Git checkout required")
            result = {"path": str(args.path.resolve()), "revision": head, "working_tree_sha256": tree_digest(args.path)}
        elif args.command == "record":
            argv = args.argv[1:] if args.argv and args.argv[0] == "--" else args.argv
            proof = record(argv, args.cwd, args.output, args.timeout)
            result = {"status": "recorded", "exit_code": proof["exit_code"], "timed_out": proof["timed_out"]}
        else:
            policy = load(Path(__file__).resolve().parents[1] / "assets/contract.json")
            value = load(args.input)
            base = args.input.resolve().parent
            if args.command in ("validate-input", "hash-input"):
                validate_input(policy, value, base)
            else:
                output = load(args.output)
                validate_output(policy, value, output, base)
                if args.command == "render":
                    with args.rendered.open("x", encoding="utf-8", newline="\n") as stream:
                        stream.write(render(policy, value, output, base))
            result = {"input_sha256": digest(value)} if args.command == "hash-input" else {"status": "valid"}
        print(encoded(result), end="")
        return 0
    except (ValueError, OSError, KeyError, TypeError, RecursionError, subprocess.SubprocessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
