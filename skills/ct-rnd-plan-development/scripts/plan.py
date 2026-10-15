#!/usr/bin/env python3
"""Check development graphs and read back GitHub tracking. Python 3.10+, stdlib only."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location("ct_plan_definition", Path(__file__).with_name("definition.py"))
definition_contract = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(definition_contract)
digest = definition_contract.digest
require = definition_contract.require
fields = definition_contract.fields
text = definition_contract.text
strings = definition_contract.strings
identifier = definition_contract.identifier
load = definition_contract.load

REPOSITORY = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
PROJECT = re.compile(r"https://github\.com/(orgs|users)/([A-Za-z0-9][A-Za-z0-9-]*)/projects/([1-9][0-9]*)\Z")


def validate_plan(ledger, definition, plan):
    """Validate authoritative scope and a complete DAG; return plan, never mutate inputs."""
    definition_contract.validate_output(ledger, definition)
    require(definition["status"] == "ready-for-planning", "definition: blocked; planning cannot proceed")
    fields(plan, "schema_version project_id plan_id definition_sha256 ledger_sha256 tracking tasks", "plan")
    definition_contract.version(plan["schema_version"])
    require(plan["project_id"] == definition["project_id"], "plan: wrong project_id")
    identifier(plan["plan_id"], "plan_id")
    require(plan["definition_sha256"] == digest(definition), "plan: stale definition digest")
    require(plan["ledger_sha256"] == digest(ledger), "plan: stale ledger digest")
    target = plan["tracking"]
    fields(target, "system repository project", "tracking")
    require(target["system"] == "github", "tracking: GitHub Issues and Projects required")
    require(isinstance(target["repository"], str) and REPOSITORY.fullmatch(target["repository"]),
            "tracking.repository: expected owner/repo")
    require(isinstance(target["project"], str) and PROJECT.fullmatch(target["project"]),
            "tracking.project: expected canonical GitHub user/organization Project URL")
    for key in ("repository", "project"):
        source = definition["tracking"][key]
        require(source is None or source == target[key], f"tracking.{key}: cannot replace definition target")
    definition_contract.records(plan["tasks"], "tasks")
    require(bool(plan["tasks"]), "tasks: expected at least one complete slice")
    task_ids, criterion_ids, covered = set(), set(), set()
    requirements = {item["id"] for item in definition["success_criteria"]}
    by_id = {}
    for task in plan["tasks"]:
        fields(task, "id title outcome depends_on acceptance status", "task")
        identifier(task["id"], "task.id")
        require(task["id"] not in task_ids, "tasks: duplicate identifier")
        task_ids.add(task["id"])
        by_id[task["id"]] = task
        text(task["title"], "task.title")
        text(task["outcome"], "task.outcome")
        require(task["status"] == "backlog", "task.status: new tasks must start in backlog")
        strings(task["depends_on"], "task.depends_on")
        definition_contract.records(task["acceptance"], "task.acceptance")
        require(bool(task["acceptance"]), "task.acceptance: expected observable criteria")
        for criterion in task["acceptance"]:
            fields(criterion, "id requirement_ids criterion verification", "acceptance criterion")
            identifier(criterion["id"], "acceptance.id")
            require(criterion["id"] not in criterion_ids, "acceptance: duplicate identifier")
            criterion_ids.add(criterion["id"])
            strings(criterion["requirement_ids"], "acceptance.requirement_ids", 1)
            require(set(criterion["requirement_ids"]) <= requirements, "acceptance: unknown requirement")
            covered.update(criterion["requirement_ids"])
            text(criterion["criterion"], "acceptance.criterion")
            text(criterion["verification"], "acceptance.verification")
    require(covered == requirements, "plan: missing success criterion coverage")
    visited, active = set(), set()

    def visit(key):
        require(key in by_id, f"tasks: unknown dependency {key}")
        require(key not in active, "tasks: cyclic dependencies")
        if key in visited:
            return
        active.add(key)
        for dependency in by_id[key]["depends_on"]:
            visit(dependency)
        active.remove(key)
        visited.add(key)

    for key in task_ids:
        visit(key)
    return plan


def marker_prefix(plan):
    return f"<!-- ct-plan:{plan['project_id']}:{plan['plan_id']}:"


def prepare(ledger, definition, plan):
    validate_plan(ledger, definition, plan)
    plan_hash = digest(plan)
    result = {"schema_version": 1, "project_id": plan["project_id"], "plan_id": plan["plan_id"],
              "plan_sha256": plan_hash, "tracking": plan["tracking"], "tasks": []}
    for task in plan["tasks"]:
        marker = f"{marker_prefix(plan)}{task['id']} -->"
        lines = [marker, f"<!-- ct-plan-sha256:{plan_hash} -->", "", "## Outcome", task["outcome"],
                 "", "## Acceptance and proof"]
        for criterion in task["acceptance"]:
            lines.extend([f"- [ ] {criterion['id']}: {criterion['criterion']}",
                          f"  - Requirements: {', '.join(criterion['requirement_ids'])}",
                          f"  - Verification: {criterion['verification']}"])
        lines.extend(["", "## Dependencies", ", ".join(task["depends_on"]) or "None", "",
                      "## Authoritative project scope", definition["problem"], definition["desired_outcome"],
                      "", "### In scope", *[f"- {x}" for x in definition["in_scope"]], "",
                      "### Exclusions", *[f"- {x}" for x in definition["out_of_scope"]], "",
                      "### Constraints", *[f"- {x}" for x in definition["constraints"]], "",
                      "### Decisions", *[f"- {x['id']}: {x['answer']} (source: {x['source']})" for x in definition["decisions"]],
                      "", "### Assumptions", *[f"- {x['statement']} Impact: {x['impact']}" for x in definition["assumptions"]],
                      "", "## Handoff", f"Project: {plan['tracking']['project']}",
                      f"Definition SHA-256: {plan['definition_sha256']}", f"Ledger SHA-256: {plan['ledger_sha256']}",
                      "Start in Backlog. Dependencies must be complete before execution."])
        result["tasks"].append({"id": task["id"], "title": task["title"], "marker": marker,
                                "body": "\n".join(lines) + "\n"})
    return result


def gh(arguments):
    """Only callers with fixed read operations are exposed; never invokes a shell."""
    try:
        response = subprocess.run(["gh", *arguments], capture_output=True, text=True, timeout=45, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError(f"GitHub readback unavailable: {error}") from error
    require(response.returncode == 0, f"GitHub readback failed: {response.stderr.strip()}")
    try:
        value = json.loads(response.stdout)
    except ValueError as error:
        raise ValueError("GitHub readback: invalid JSON response") from error
    require(not (isinstance(value, dict) and value.get("errors")), "GitHub GraphQL readback returned errors")
    return value


def read_project(url):
    match = PROJECT.fullmatch(url)
    owner_kind = "organization" if match[1] == "orgs" else "user"
    query = ("query($owner:String!,$number:Int!,$endCursor:String){" + owner_kind +
             "(login:$owner){projectV2(number:$number){url closed items(first:100,after:$endCursor){"
             "pageInfo{hasNextPage endCursor} nodes{id isArchived content{... on Issue{url}} "
             'fieldValueByName(name:"Status"){... on ProjectV2ItemFieldSingleSelectValue{name}}}}}}}')
    pages = gh(["api", "graphql", "--paginate", "--slurp", "-f", f"query={query}",
                "-f", f"owner={match[2]}", "-F", f"number={match[3]}"])
    require(isinstance(pages, list) and bool(pages), "Project readback: missing pages")
    items = []
    for index, page in enumerate(pages):
        require(isinstance(page, dict) and not page.get("errors"), "Project readback: API errors")
        try:
            project = page["data"][owner_kind]["projectV2"]
            require(project["url"] == url and project["closed"] is False, "Project readback: wrong or closed Project")
            connection = project["items"]
            require(connection["pageInfo"]["hasNextPage"] is (index < len(pages) - 1),
                    "Project readback: incomplete pagination")
            require(isinstance(connection["nodes"], list), "Project readback: invalid items")
            items.extend(connection["nodes"])
        except (TypeError, KeyError) as error:
            raise ValueError("Project readback: unavailable or malformed Project") from error
    return items


def verify_tracking(ledger, definition, plan, tracking, *, require_backlog=True):
    payload = prepare(ledger, definition, plan)
    fields(tracking, "schema_version project_id plan_id plan_sha256 issues", "tracking receipt")
    definition_contract.version(tracking["schema_version"])
    for key in ("project_id", "plan_id", "plan_sha256"):
        require(tracking[key] == payload[key], f"tracking receipt: stale or wrong {key}")
    definition_contract.records(tracking["issues"], "tracking receipt.issues")
    require(len(tracking["issues"]) == len(payload["tasks"]), "tracking receipt: wrong issue count")
    receipts, urls = {}, set()
    repo = plan["tracking"]["repository"]
    for entry in tracking["issues"]:
        fields(entry, "task_id url", "tracking issue")
        identifier(entry["task_id"], "tracking task_id")
        require(entry["task_id"] not in receipts, "tracking receipt: duplicate task")
        require(isinstance(entry["url"], str) and re.fullmatch(
            r"https://github\.com/" + re.escape(repo) + r"/issues/[1-9][0-9]*", entry["url"]),
            "tracking receipt: issue URL has wrong repository or format")
        require(entry["url"] not in urls, "tracking receipt: duplicate issue URL")
        urls.add(entry["url"])
        receipts[entry["task_id"]] = entry["url"]
    require(set(receipts) == {t["id"] for t in payload["tasks"]}, "tracking receipt: unknown/missing task")
    pages = gh(["api", f"repos/{repo}/issues?state=all&per_page=100", "--method", "GET", "--paginate", "--slurp"])
    require(isinstance(pages, list) and bool(pages) and all(isinstance(p, list) for p in pages),
            "Issue readback: missing or malformed pages")
    issues = [issue for page in pages for issue in page]
    require(all(isinstance(issue, dict) for issue in issues), "Issue readback: malformed issues")
    require(all(issue.get("body") is None or isinstance(issue.get("body"), str) for issue in issues),
            "Issue readback: malformed issue body")
    relevant = [issue for issue in issues if marker_prefix(plan) in (issue.get("body") or "")]
    require(len(relevant) == len(payload["tasks"]), "Issue readback: duplicate, missing, or stale plan issues")
    project_items = read_project(plan["tracking"]["project"])
    require(all(isinstance(item, dict) for item in project_items), "Project readback: malformed item")
    task_states = []
    for task in payload["tasks"]:
        matches = [issue for issue in relevant if task["marker"] in issue.get("body", "")]
        require(len(matches) == 1, f"Issue readback: missing/duplicate marker for {task['id']}")
        issue = matches[0]
        require(issue.get("html_url") == receipts[task["id"]], "Issue readback: URL mismatch")
        require("pull_request" not in issue and issue.get("state") in ("open", "closed"),
                "Issue readback: must be an issue with known state")
        if require_backlog:
            require(issue["state"] == "open", "Issue readback: new task must be an open issue")
        actual_body = issue.get("body")
        if not require_backlog and isinstance(actual_body, str):
            actual_body = re.sub(r"(?m)^- \[[xX]\] ", "- [ ] ", actual_body)
        require(issue.get("title") == task["title"] and actual_body == task["body"],
                "Issue readback: changed title/body or stale plan digest")
        items = [item for item in project_items if isinstance(item.get("content"), dict)
                 and item["content"].get("url") == issue["html_url"]]
        require(len(items) == 1, "Project readback: missing or duplicate issue membership")
        require(items[0].get("isArchived") is False, "Project readback: item is archived")
        status_value = items[0].get("fieldValueByName")
        require(isinstance(status_value, dict) and set(status_value) == {"name"},
                "Project readback: missing or malformed Status")
        text(status_value["name"], "Project readback.Status")
        if require_backlog:
            require(status_value["name"] == "Backlog", "Project readback: new task status must be Backlog")
        task_states.append({"task_id": task["id"], "issue_url": issue["html_url"],
                            "issue_state": issue["state"], "project_status": status_value["name"]})
    return {"status": "verified", "project_id": plan["project_id"], "plan_id": plan["plan_id"],
            "plan_sha256": digest(plan), "issue_count": len(payload["tasks"]),
            "tracking": plan["tracking"], "evidence": "live GitHub API readback", "tasks": task_states}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "prepare", "verify-tracking"):
        command_parser = sub.add_parser(command)
        for name in ("ledger", "definition", "plan"):
            command_parser.add_argument(name, type=Path)
        if command == "prepare":
            command_parser.add_argument("--output", required=True, type=Path)
        if command == "verify-tracking":
            command_parser.add_argument("tracking", type=Path)
    args = parser.parse_args()
    try:
        values = [load(getattr(args, name)) for name in ("ledger", "definition", "plan")]
        if args.command == "validate":
            validate_plan(*values)
            result = {"status": "valid-local-plan", "plan_sha256": digest(values[2]),
                      "tracking_verified": False}
        elif args.command == "prepare":
            result = prepare(*values)
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(definition_contract.encoded(result))
            result = {"status": "prepared", "output": str(args.output), "tracking_verified": False}
        else:
            result = verify_tracking(*values, load(args.tracking))
        print(definition_contract.encoded(result), end="")
        return 0
    except (ValueError, OSError) as error:
        print(f"Blocked: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
