"""Lifecycle evidence validation and readiness rules using facade callbacks."""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path


def timestamp(value, helpers):
    text = helpers["text"]
    require = helpers["require"]
    text(value, "timestamp")
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "timestamp: timezone required")
    require(parsed <= dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5), "timestamp: future evidence")


def evidence_valid(item, base, context, helpers):
    fields = helpers["fields"]
    identifier = helpers["identifier"]
    require = helpers["require"]
    reference = helpers["reference"]
    load = helpers["load"]
    text = helpers["text"]
    timestamp = helpers["timestamp"]
    command = helpers["command"]
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


def rule_valid(rule, result, value, context, helpers):
    require = helpers["require"]
    path_value = helpers["path_value"]
    strings = helpers["strings"]
    interface_module = helpers["interface_module"]
    store_module = helpers["store_module"]
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
    elif kind == "interface-fix":
        interface_module().check_ready(rule, result, value, context, helpers)
    elif kind == "store-release":
        store_module().check_output(rule, result, value, context, helpers)
    else:
        raise ValueError(f"rule: unknown bundled rule {kind}")
