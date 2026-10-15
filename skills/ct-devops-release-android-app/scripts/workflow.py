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


def file_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reference(value, base):
    fields(value, REF_FIELDS, "reference")
    text(value["path"], "reference.path")
    require(isinstance(value["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", value["sha256"]),
            "reference.sha256: expected lowercase SHA-256")
    path = Path(value["path"])
    if not path.is_absolute():
        path = Path(base) / path
    require(not path.is_symlink() and path.is_file(), f"reference: expected regular file {path}")
    require(file_digest(path) == value["sha256"], f"reference: stale or mismatched digest {path}")
    return path


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


def path_value(value, path):
    for part in path.split("."):
        require(isinstance(value, dict) and part in value, f"rule: missing field {path}")
        value = value[part]
    return value


def schema(value, spec, where, context):
    allowed = {"type", "nullable", "enum", "fields", "optional", "items", "min_items", "unique_by", "ref"}
    require(isinstance(spec, dict) and set(spec) <= allowed and "type" in spec, f"{where}: invalid bundled schema")
    if value is None and spec.get("nullable", False):
        return
    types = {"string": lambda x: isinstance(x, str) and bool(x.strip()),
             "number": lambda x: type(x) in (int, float) and abs(x) != float("inf") and x == x,
             "integer": lambda x: type(x) is int, "boolean": lambda x: type(x) is bool,
             "object": lambda x: isinstance(x, dict), "array": lambda x: isinstance(x, list),
             "null": lambda x: x is None}
    kind = spec["type"]
    require(kind in types and types[kind](value), f"{where}: expected {kind}")
    if "enum" in spec:
        require(value in spec["enum"], f"{where}: unsupported value")
    if kind == "object":
        required = set(spec.get("fields", {})) - set(spec.get("optional", []))
        require(required <= set(value) <= set(spec.get("fields", {})), f"{where}: missing or unknown fields")
        for key, item in value.items():
            schema(item, spec["fields"][key], f"{where}.{key}", context)
    elif kind == "array":
        require(len(value) >= spec.get("min_items", 0), f"{where}: too few entries")
        for index, item in enumerate(value):
            schema(item, spec["items"], f"{where}[{index}]", context)
        if "unique_by" in spec:
            identifiers = [item[spec["unique_by"]] for item in value]
            require(len({json.dumps(x, sort_keys=True) for x in identifiers}) == len(identifiers),
                    f"{where}: duplicate {spec['unique_by']}")
    if "ref" in spec:
        require(kind == "string" and spec["ref"] in ("evidence", "source", "requirement"),
                f"{where}: invalid reference type")
        require(value in context[spec["ref"]], f"{where}: unknown {spec['ref']} reference {value}")


def store_module():
    spec = importlib.util.spec_from_file_location("ct_store_release", Path(__file__).with_name("store_release.py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def validate_input(policy, value, base=Path.cwd(), *, historical=False):
    fields(policy, "skill purpose requires_definition inputs result rules", "policy")
    fields(value, "schema_version project_id request repository ledger definition constraints sources inputs", "input")
    definition.version(value["schema_version"])
    identifier(value["project_id"], "project_id")
    text(value["request"], "request")
    strings(value["constraints"], "constraints")
    context = {"evidence": {}, "source": {}, "requirement": set(), "definition": None, "ledger": None,
               "base": Path(base)}
    if value["repository"] is not None:
        fields(value["repository"], "path revision working_tree_sha256", "repository")
        text(value["repository"]["path"], "repository.path")
        text(value["repository"]["revision"], "repository.revision")
        repo = Path(value["repository"]["path"])
        if not repo.is_absolute():
            repo = Path(base) / repo
        require(repo.is_dir(), "repository: directory unavailable")
        if any(r.get("type") == "store-release" for r in policy["rules"]):
            store_module().configuration_module().check_private_paths(repo, globals())
        require(re.fullmatch(r"[0-9a-f]{40,64}", value["repository"]["revision"]) is not None,
                "repository: invalid revision")
        fingerprint = value["repository"]["working_tree_sha256"]
        require(isinstance(fingerprint, str) and re.fullmatch(r"[0-9a-f]{64}", fingerprint),
                "repository: invalid working-tree fingerprint")
        if historical:
            require(policy["skill"] == "ct-rnd-build-feature", "repository: history only supported for task proofs")
            result = command(["git", "merge-base", "--is-ancestor", value["repository"]["revision"], "HEAD"], repo)
            require(result.returncode == 0, "repository: historical task revision is not an ancestor of current HEAD")
        else:
            require(revision(repo) == value["repository"]["revision"], "repository: revision mismatch")
            require(fingerprint == tree_digest(repo), "repository: working tree changed after intake")
        context["repository_binding"] = value["repository"]
        context["repository"] = repo
    if value["ledger"] is not None:
        ledger = load(reference(value["ledger"], base))
        definition.replay(ledger)
        require(ledger["input"]["project_id"] == value["project_id"], "input: ledger scope mismatch")
        context["ledger"] = ledger
    if value["definition"] is not None:
        require(context["ledger"] is not None, "input: definition requires its interview ledger")
        project = load(reference(value["definition"], base))
        definition.validate_output(context["ledger"], project)
        require(project["project_id"] == value["project_id"], "input: definition scope mismatch")
        context["definition"] = project
        context["requirement"] = {x["id"] for x in project["success_criteria"]}
    definition.records(value["sources"], "sources")
    for source in value["sources"]:
        fields(source, "id path sha256", "source")
        identifier(source["id"], "source.id")
        require(source["id"] not in context["source"], "sources: duplicate identifier")
        context["source"][source["id"]] = reference({k: source[k] for k in ("path", "sha256")}, base)
    schema(value["inputs"], policy["inputs"], "inputs", context)
    for rule in policy["rules"]:
        if rule.get("type") == "store-release":
            store_module().check_input(rule, value, context, globals())
    return context


def timestamp(value):
    text(value, "timestamp")
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "timestamp: timezone required")
    require(parsed <= dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5), "timestamp: future evidence")


def evidence_valid(item, base, context):
    fields(item, "id kind reference", "evidence")
    identifier(item["id"], "evidence.id")
    require(item["id"] not in context["evidence"], "evidence: duplicate identifier")
    path = reference(item["reference"], base)
    require(item["kind"] in ("command", "artifact", "observation"), "evidence.kind: unsupported type")
    data = None
    if item["kind"] == "command":
        data = load(path)
        fields(data, "kind argv cwd source_revision working_tree_sha256 started_at exit_code timed_out stdout stderr", "command proof")
        require(data["kind"] == "ct-command-proof.v1", "evidence: wrong command proof kind")
        require(isinstance(data["argv"], list) and bool(data["argv"]), "command.argv: expected nonempty argv")
        for argument in data["argv"]:
            text(argument, "command.argv")
        text(data["cwd"], "command.cwd")
        require(Path(data["cwd"]).is_absolute(), "command.cwd: expected absolute path")
        require(type(data["exit_code"]) is int and type(data["timed_out"]) is bool, "command: invalid completion status")
        require(isinstance(data["stdout"], str) and isinstance(data["stderr"], str), "command: expected captured text")
        for key in ("source_revision", "working_tree_sha256"):
            require(data[key] is None or (isinstance(data[key], str) and re.fullmatch(r"[0-9a-f]{40,64}", data[key])),
                    f"command.{key}: invalid fingerprint")
        timestamp(data["started_at"])
        if "repository" in context:
            require(Path(data["cwd"]).resolve() == context["repository"].resolve(), "command: wrong repository")
            if data["exit_code"] == 0:
                require(data["source_revision"] == context["repository_binding"]["revision"], "command: stale source revision")
                require(data["working_tree_sha256"] == context["repository_binding"]["working_tree_sha256"], "command: working tree changed after check")
            else:
                require(data["source_revision"] is not None, "command: before-proof source revision missing")
                result = command(["git", "cat-file", "-e", data["source_revision"] + "^{commit}"], context["repository"])
                require(result.returncode == 0, "command: before-proof revision is not in this repository")
    elif item["kind"] == "observation":
        data = load(path)
        fields(data, "kind source observed_at statement limitations", "observation")
        require(data["kind"] == "ct-observation.v1", "evidence: wrong observation kind")
        for key in ("source", "statement", "limitations"):
            text(data[key], f"observation.{key}")
        timestamp(data["observed_at"])
    context["evidence"][item["id"]] = {"kind": item["kind"], "data": data, "path": path}


def rule_valid(rule, result, value, context):
    kind = rule.get("type")
    if kind == "coverage":
        require(bool(context["requirement"]), "coverage: validated definition requirements required")
        targets = context["requirement"]
        if "input_field" in rule:
            selected = path_value(value["inputs"], rule["input_field"])
            strings(selected, "coverage.selected_requirements", 1)
            require(set(selected) <= context["requirement"], "coverage: unknown selected requirement")
            targets = set(selected)
        covered = set()
        for item in path_value(result, rule["items"]):
            ids = path_value(item, rule["field"])
            strings(ids, "coverage.requirement_ids")
            require(set(ids) <= context["requirement"], "coverage: unknown requirement")
            covered.update(ids)
        require(covered == targets, "coverage: missing or out-of-scope requirements")
    elif kind == "command":
        key = path_value(result, rule["field"])
        require(isinstance(key, str) and key in context["evidence"], "command rule: missing evidence")
        evidence = context["evidence"][key]
        require(evidence["kind"] == "command", "command rule: expected recorded command")
        proof = evidence["data"]
        require(not proof["timed_out"], "command rule: timed-out execution")
        expected = rule["exit"]
        require(expected in ("zero", "nonzero", "any"), "command rule: invalid exit policy")
        require(expected == "any" or ((proof["exit_code"] == 0) == (expected == "zero")),
                "command rule: unexpected exit code")
        if expected == "zero" and "repository" in context:
            require(proof["working_tree_sha256"] == context["repository_binding"]["working_tree_sha256"],
                    "command rule: working tree changed after check")
    elif kind == "same-command":
        proofs = []
        for name in rule["fields"]:
            key = path_value(result, name)
            require(key in context["evidence"] and context["evidence"][key]["kind"] == "command",
                    "same-command: missing recorded command")
            proofs.append(context["evidence"][key]["data"])
        require(len(proofs) >= 2 and all((p["argv"], p["cwd"]) == (proofs[0]["argv"], proofs[0]["cwd"]) for p in proofs),
                "same-command: before and after must exercise the same command")
    elif kind == "all-status":
        items = path_value(result, rule["items"])
        require(bool(items) and all(path_value(item, rule["field"]) in rule["allowed"] for item in items),
                "all-status: incomplete or unsuccessful items")
    elif kind == "equals-input":
        require(path_value(result, rule["field"]) == path_value(value["inputs"], rule["input_field"]),
                "equals-input: result changed the requested target")
    elif kind == "references":
        targets = [path_value(item, rule["target_field"]) for item in path_value(result, rule["target"])]
        for item in path_value(result, rule["items"]):
            for field in rule["fields"]:
                actual = path_value(item, field)
                actual = actual if isinstance(actual, list) else [actual]
                require(all(x in targets for x in actual), "references: unknown target")
    elif kind == "nonempty":
        require(all(bool(path_value(result, name)) for name in rule["fields"]), "nonempty: missing required result")
    elif kind == "required-when":
        conditions = rule.get("when", [{"input_field": rule.get("input_field"), "equals": rule.get("equals")}])
        if all(path_value(value["inputs"], item["input_field"]) == item["equals"] for item in conditions):
            require(all(bool(path_value(result, name)) for name in rule.get("fields", [])),
                    "required-when: missing conditional proof or authorization source")
            require(all(not path_value(result, name) for name in rule.get("empty_fields", [])),
                    "required-when: unexpected action or publication evidence")
    elif kind == "map-input":
        target = path_value(value["inputs"], rule["input_field"])
        require(target in rule["values"] and path_value(result, rule["field"]) == rule["values"][target],
                "map-input: result does not match requested phase")
    elif kind == "cover-target":
        actual = [path_value(item, rule["field"]) for item in path_value(result, rule["items"])]
        source = result if rule.get("target_result", False) else value["inputs"]
        targets = [path_value(item, rule["target_field"]) for item in path_value(source, rule["target"])]
        require(bool(targets) and set(actual) == set(targets), "cover-target: missing or unknown target coverage")
    elif kind == "command-matches-input":
        key = path_value(result, rule["field"])
        require(key in context["evidence"] and context["evidence"][key]["kind"] == "command",
                "command-matches-input: missing command proof")
        require(context["evidence"][key]["data"]["argv"] == path_value(value["inputs"], rule["input_field"]),
                "command-matches-input: different invocation from requested check")
    elif kind == "aggregate-status":
        statuses = [path_value(item, rule["field"]) for item in path_value(result, rule["items"])]
        require(bool(statuses), "aggregate-status: no scenarios")
        expected = rule["default"]
        for item in rule["priority"]:
            if item["status"] in statuses:
                expected = item["value"]
                break
        require(path_value(result, rule["target"]) == expected, "aggregate-status: verdict contradicts scenario evidence")
    elif kind == "required-values":
        actual = {path_value(item, rule["field"]) for item in path_value(result, rule["items"])}
        require(actual == set(rule["values"]), "required-values: missing or unknown coverage areas")
    elif kind == "repository-revision":
        if rule.get("if_present", False) and "repository" not in context:
            return
        require("repository" in context, "repository-revision: verified repository required")
        require(path_value(result, rule["field"]) == value["repository"]["revision"],
                "repository-revision: result is not the inspected revision")
    elif kind == "command-cwd-input":
        key = path_value(result, rule["field"])
        require(key in context["evidence"] and context["evidence"][key]["kind"] == "command",
                "command-cwd-input: missing command proof")
        target = Path(path_value(value["inputs"], rule["input_field"]))
        if not target.is_absolute():
            target = context["base"] / target
        require(Path(context["evidence"][key]["data"]["cwd"]).resolve() == target.resolve(),
                "command-cwd-input: proof is for a different project")
    elif kind == "scenario-evidence":
        for item in path_value(result, rule["items"]):
            if path_value(item, rule["status_field"]) != "passed":
                continue
            for key in path_value(item, rule["evidence_field"]):
                evidence = context["evidence"][key]
                if evidence["kind"] == "command":
                    require(evidence["data"]["exit_code"] == 0 and not evidence["data"]["timed_out"],
                            "scenario-evidence: passed scenario cites a failing or timed-out check")
    elif kind == "store-release":
        store_module().check_output(rule, result, value, context, globals())
    else:
        raise ValueError(f"rule: unknown bundled rule {kind}")


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
