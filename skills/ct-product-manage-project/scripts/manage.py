#!/usr/bin/env python3
"""Route a project from verified local artifacts; optional read-only GitHub verification."""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

sys.dont_write_bytecode = True


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


workflow = module("ct_manager_workflow", "workflow.py")
definition_contract = workflow.definition
plan_contract = module("ct_manager_plan", "plan_contract.py")
require, fields, text = workflow.require, workflow.fields, workflow.text
load, digest, encoded = workflow.load, workflow.digest, workflow.encoded
CATALOG = Path(__file__).resolve().parents[1] / "assets/catalog.json"


def validate_state(value, base, skills_root):
    fields(value, "schema_version project_id objective intent local_only ledger definition plan tracking "
           "repository receipts task_receipts target_stage done_statuses", "project state")
    definition_contract.version(value["schema_version"])
    definition_contract.identifier(value["project_id"], "project_id")
    text(value["objective"], "objective")
    require(type(value["local_only"]) is bool, "local_only: expected boolean")
    require(value["target_stage"] in ("candidate", "staging", "production"), "target_stage: invalid release milestone")
    definition_contract.strings(value["done_statuses"], "done_statuses", 1)
    catalog = load(CATALOG)
    intents = {x["intent"]: x["skill"] for x in catalog}
    require(value["intent"] == "continue" or value["intent"] in intents, "intent: unknown workflow")
    context = {"ledger": None, "definition": None, "plan": None, "tracking": None, "reports": {},
               "tasks": {}, "intents": intents, "repository": None}
    for key in ("ledger", "definition", "plan", "tracking"):
        if value[key] is not None:
            context[key] = load(workflow.reference(value[key], base))
    if context["ledger"] is not None:
        definition_contract.replay(context["ledger"])
        require(context["ledger"]["input"]["project_id"] == value["project_id"], "manager: ledger scope mismatch")
    if context["definition"] is not None:
        require(context["ledger"] is not None, "manager: definition requires its ledger")
        definition_contract.validate_output(context["ledger"], context["definition"])
        require(context["definition"]["project_id"] == value["project_id"], "manager: definition scope mismatch")
    if context["plan"] is not None:
        require(context["definition"] is not None, "manager: plan requires its definition")
        plan_contract.validate_plan(context["ledger"], context["definition"], context["plan"])
    if context["tracking"] is not None:
        require(context["plan"] is not None, "manager: tracking requires its plan")
        require(context["tracking"].get("plan_sha256") == digest(context["plan"]), "manager: stale tracking plan")
    if value["repository"] is not None:
        fields(value["repository"], "path revision working_tree_sha256", "repository")
        text(value["repository"]["path"], "repository.path")
        text(value["repository"]["revision"], "repository.revision")
        text(value["repository"]["working_tree_sha256"], "repository.working_tree_sha256")
        path = Path(value["repository"]["path"])
        if not path.is_absolute():
            path = base / path
        require(path.is_dir() and workflow.revision(path) == value["repository"]["revision"],
                "manager: repository revision mismatch")
        require(workflow.tree_digest(path) == value["repository"]["working_tree_sha256"],
                "manager: repository working tree changed")
        context["repository"] = path
    known = {x["skill"] for x in catalog}

    def receipt(entry, *, historical=False):
        fields(entry, "skill input output", "receipt")
        require(entry["skill"] in known, "manager: unknown producer skill")
        policy_path = skills_root / entry["skill"] / "assets/contract.json"
        require(policy_path.is_file(), f"manager: receipt validator unavailable for {entry['skill']}")
        policy = load(policy_path)
        require(policy["skill"] == entry["skill"], "manager: mismatched producer policy")
        input_path = workflow.reference(entry["input"], base)
        output_path = workflow.reference(entry["output"], base)
        intake, report = load(input_path), load(output_path)
        require(intake["project_id"] == value["project_id"], "manager: receipt scope mismatch")
        workflow.validate_output(policy, intake, report, input_path.parent, historical=historical)
        if context["ledger"] is not None and intake["ledger"] is not None:
            require(digest(load(workflow.reference(intake["ledger"], input_path.parent))) == digest(context["ledger"]),
                    "manager: receipt uses stale interview")
        if context["definition"] is not None and intake["definition"] is not None:
            require(digest(load(workflow.reference(intake["definition"], input_path.parent))) == digest(context["definition"]),
                    "manager: receipt uses stale definition")
        if context["repository"] is not None and intake["repository"] is not None:
            repo_path = Path(intake["repository"]["path"])
            if not repo_path.is_absolute():
                repo_path = input_path.parent / repo_path
            require(repo_path.resolve() == context["repository"].resolve(), "manager: receipt is for another repository")
        if entry["skill"] in ("ct-rnd-review-code", "ct-qa-test-user-flows", "ct-security-review-project", "ct-devops-release-project"):
            require(context["repository"] is not None and intake["repository"] is not None,
                    "manager: release-gate report requires current repository identity")
            candidate = intake["inputs"].get("candidate_revision")
            require(candidate is None or candidate == value["repository"]["revision"],
                    "manager: release-gate report has a different candidate")
        return intake, report

    definition_contract.records(value["receipts"], "receipts")
    for entry in value["receipts"]:
        require(entry.get("skill") not in context["reports"], "manager: duplicate current skill receipt")
        _, report = receipt(entry)
        context["reports"][entry["skill"]] = report
    definition_contract.records(value["task_receipts"], "task_receipts")
    for entry in value["task_receipts"]:
        fields(entry, "task_id input output", "task receipt")
        require(context["plan"] is not None, "manager: task receipt requires plan")
        tasks = {x["id"]: x for x in context["plan"]["tasks"]}
        require(isinstance(entry["task_id"], str) and entry["task_id"] in tasks, "manager: unknown task receipt")
        require(entry["task_id"] not in context["tasks"], "manager: duplicate task receipt")
        intake, report = receipt({"skill": "ct-rnd-build-feature", "input": entry["input"], "output": entry["output"]},
                                 historical=True)
        require(intake["inputs"]["task_id"] == entry["task_id"], "manager: task receipt identity mismatch")
        requirements = {r for c in tasks[entry["task_id"]]["acceptance"] for r in c["requirement_ids"]}
        require(set(intake["inputs"]["requirement_ids"]) == requirements, "manager: task proof covers different requirements")
        expected = [{"id": c["id"], "requirement_ids": sorted(c["requirement_ids"]),
                     "scenario": c["criterion"], "verification": c["verification"]}
                    for c in tasks[entry["task_id"]]["acceptance"]]
        actual = [dict(c, requirement_ids=sorted(c["requirement_ids"])) for c in intake["inputs"]["acceptance"]]
        require(sorted(actual, key=lambda c: c["id"]) == sorted(expected, key=lambda c: c["id"]),
                "manager: task proof omits or changes planned acceptance")
        context["tasks"][entry["task_id"]] = report
    return context


def route(value, base, skills_root, verify_tracking=False):
    base, skills_root = Path(base), Path(skills_root)
    context = validate_state(value, base, skills_root)
    selected, status, reason, task_id, milestone = None, "ready", "", None, None
    execution = {"set-up-project", "build-feature", "release-project"}

    def choose(skill, explanation, blocked=False):
        nonlocal selected, status, reason
        selected, reason = skill, explanation
        status = "blocked" if blocked else "ready"

    intent = "continue" if value["intent"] == "manage-project" else value["intent"]
    if intent != "continue" and intent not in execution:
        choose(context["intents"][intent], "Use the explicitly requested specialist; preserve the existing scope and interview ledger.")
    elif context["definition"] is None:
        choose("ct-product-define-project", "A validated project definition and its shared interview ledger are required.")
    elif context["definition"]["status"] != "ready-for-planning":
        choose("ct-product-define-project", "Resolve the recorded scope blockers; do not start another interview budget.", True)
    elif context["plan"] is None:
        choose("ct-rnd-plan-development", "Develop a validated task graph with complete acceptance coverage.")
    elif context["tracking"] is None:
        choose("ct-rnd-plan-development", "Publish and verify GitHub Issues and Project items before task execution.", True)
    elif value["local_only"]:
        choose("ct-rnd-plan-development", "Local-only mode holds the GitHub admission gate; no remote verification was attempted.", True)
    elif not verify_tracking:
        choose("ct-rnd-plan-development", "A stored tracking receipt is not live proof; request read-only verification before execution.", True)
    else:
        live = plan_contract.verify_tracking(context["ledger"], context["definition"], context["plan"],
                                             context["tracking"], require_backlog=False)
        states = {x["task_id"]: x for x in live["tasks"]}
        complete = set()
        for task in context["plan"]["tasks"]:
            item = states[task["id"]]
            report = context["tasks"].get(task["id"])
            closed = item["issue_state"] == "closed" and item["project_status"] in value["done_statuses"]
            if closed and report is not None and report["status"] == "ready":
                complete.add(task["id"])
            elif closed or (report is not None and report["status"] == "ready"):
                choose("ct-rnd-plan-development", "GitHub task completion and validated local proof disagree; reconcile the exact task.", True)
                task_id = task["id"]
                break
        if selected is None:
            if intent in execution:
                choose(context["intents"][intent], "Tracking was read back; perform the requested scoped execution step.")
            elif context["repository"] is None:
                choose("ct-rnd-set-up-project", "Establish the runnable repository and return its revision and real command checks.")
            elif len(complete) < len(context["plan"]["tasks"]):
                frontier = [x for x in context["plan"]["tasks"] if x["id"] not in complete and set(x["depends_on"]) <= complete]
                require(bool(frontier), "manager: no executable frontier despite valid task graph")
                task_id = frontier[0]["id"]
                choose("ct-rnd-build-feature", "Build one admitted complete slice whose dependencies are verified complete.")
            else:
                for gate in ("ct-rnd-review-code", "ct-qa-test-user-flows", "ct-security-review-project"):
                    report = context["reports"].get(gate)
                    if report is None or report["status"] != "ready":
                        choose(gate, "Complete the current-revision release gate and retain its checked evidence.")
                        break
                    if gate == "ct-qa-test-user-flows" and report["result"]["verdict"] != "passed":
                        choose("ct-rnd-fix-bug", "The completed QA assessment did not pass; resolve the failed or blocked flows.", True)
                        break
                    if any(x["severity"] in ("critical", "high") for x in report["result"].get("findings", [])):
                        choose("ct-rnd-fix-bug", "A current review has high or critical findings; resolve and revalidate before release.", True)
                        break
                if selected is None:
                    release = context["reports"].get("ct-devops-release-project")
                    expected = {"candidate": "candidate-prepared", "staging": "staging-deployed", "production": "production-verified"}
                    if release is None or release["status"] != "ready" or release["result"]["outcome"] != expected[value["target_stage"]]:
                        choose("ct-devops-release-project", "Prepare or verify only the requested release milestone, preserving its approval gates.")
                    else:
                        status, reason, milestone = "complete", "The requested release milestone has matching verified task and specialist evidence.", value["target_stage"]
    if selected is not None:
        entry = skills_root / selected / "SKILL.md"
        if not entry.is_file() or entry.is_symlink():
            status, reason = "blocked", f"Required specialist is not installed: {selected}. Install its complete reviewed package before continuing."
    interview = definition_contract.replay(context["ledger"]) if context["ledger"] is not None else None
    return {"schema_version": 1, "project_id": value["project_id"], "input_sha256": digest(value),
            "status": status, "next_skill": selected, "task_id": task_id, "milestone": milestone,
            "reason": reason, "interview_usage": None if interview is None else {
                "questions": interview["questions_used"], "batches": interview["batches_used"],
                "pending": interview["pending_question_ids"]},
            "local_only": value["local_only"], "tracking_checked_live": bool(
                verify_tracking and not value["local_only"] and context["tracking"] is not None and intent in execution | {"continue"})}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("--skills-root", required=True, type=Path)
    parser.add_argument("--verify-tracking", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-output", type=Path, help="Recompute and check a previously emitted route")
    args = parser.parse_args()
    try:
        result = route(load(args.state), args.state.resolve().parent, args.skills_root, args.verify_tracking)
        if args.validate_output is not None:
            require(load(args.validate_output) == result, "manager: stale or modified route output")
        if args.output is not None:
            workflow.write_new(args.output, result)
        print(encoded(result), end="")
        return 0
    except (ValueError, OSError, KeyError, TypeError, RecursionError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
