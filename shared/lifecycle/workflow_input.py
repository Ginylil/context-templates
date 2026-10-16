"""Lifecycle intake, schema and referenced-artifact validation.

The facade supplies its live helper mapping so package callbacks keep the same
repository, evidence and monkeypatch behavior as the public workflow module.
"""
from __future__ import annotations

import json
import re
from pathlib import Path


def reference(value, base, helpers):
    fields = helpers["fields"]
    text = helpers["text"]
    require = helpers["require"]
    file_digest = helpers["file_digest"]
    REF_FIELDS = helpers["REF_FIELDS"]
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


def path_value(value, path, helpers):
    require = helpers["require"]
    for part in path.split("."):
        require(isinstance(value, dict) and part in value, f"rule: missing field {path}")
        value = value[part]
    return value


def schema(value, spec, where, context, helpers):
    require = helpers["require"]
    schema = helpers["schema"]
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


def validate_input(policy, value, base=Path.cwd(), *, historical=False, helpers):
    fields = helpers["fields"]
    definition = helpers["definition"]
    identifier = helpers["identifier"]
    text = helpers["text"]
    strings = helpers["strings"]
    require = helpers["require"]
    store_module = helpers["store_module"]
    command = helpers["command"]
    revision = helpers["revision"]
    tree_digest = helpers["tree_digest"]
    load = helpers["load"]
    reference = helpers["reference"]
    schema = helpers["schema"]
    interface_module = helpers["interface_module"]
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
            store_module().configuration_module().check_private_paths(repo, helpers)
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
            store_module().check_input(rule, value, context, helpers)
        elif rule.get("type") == "interface-fix":
            interface_module().check_input(rule, value, context, helpers)
    return context
