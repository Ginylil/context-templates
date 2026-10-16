#!/usr/bin/env python3
"""Validate project definitions and maintain a bounded interview. Python 3.10+, no dependencies."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

MAX_QUESTIONS = 10
MAX_BATCHES = 2
ID = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(value, required, where):
    require(isinstance(value, dict), f"{where}: expected object")
    require(set(value) == set(required.split()), f"{where}: expected fields {required}")


def text(value, where):
    require(isinstance(value, str) and bool(value.strip()), f"{where}: expected nonempty text")


def identifier(value, where):
    require(isinstance(value, str) and ID.fullmatch(value), f"{where}: expected lowercase hyphenated identifier")


def strings(value, where, minimum=0):
    require(isinstance(value, list) and len(value) >= minimum, f"{where}: expected list (minimum {minimum})")
    for item in value:
        text(item, where)
    require(len(value) == len(set(value)), f"{where}: duplicate entries")


def records(value, where):
    require(isinstance(value, list) and all(isinstance(x, dict) for x in value), f"{where}: expected object list")


def version(value):
    require(type(value) is int and value == 1, "schema_version: expected integer 1")


def resolution(value, where):
    fields(value, "answer source", where)
    text(value["answer"], f"{where}.answer")
    text(value["source"], f"{where}.source")


def decisions_valid(decisions):
    records(decisions, "decisions")
    by_id = {}
    for decision in decisions:
        fields(decision, "id topic depends_on blocking resolution", "decision")
        identifier(decision["id"], "decision.id")
        require(decision["id"] not in by_id, "decisions: duplicate identifier")
        text(decision["topic"], "decision.topic")
        strings(decision["depends_on"], "decision.depends_on")
        require(type(decision["blocking"]) is bool, "decision.blocking: expected boolean")
        if decision["resolution"] is not None:
            resolution(decision["resolution"], "decision.resolution")
        by_id[decision["id"]] = decision
    visited, active = set(), set()

    def visit(key):
        require(key in by_id, f"decisions: unknown dependency {key}")
        require(key not in active, "decisions: cyclic dependencies")
        if key in visited:
            return
        active.add(key)
        for dependency in by_id[key]["depends_on"]:
            visit(dependency)
            if by_id[key]["resolution"] is not None:
                require(by_id[dependency]["resolution"] is not None,
                        "decisions: resolved decision has unresolved dependency")
        active.remove(key)
        visited.add(key)

    for key in by_id:
        visit(key)
    return by_id


def tracking_valid(value):
    fields(value, "system repository project", "tracking")
    require(value["system"] == "github", "tracking.system: GitHub Issues and Projects are required")
    for key in ("repository", "project"):
        if value[key] is not None:
            text(value[key], f"tracking.{key}")


def validate_input(value):
    fields(value, "schema_version project_id idea sources constraints decisions tracking", "input")
    version(value["schema_version"])
    identifier(value["project_id"], "project_id")
    text(value["idea"], "idea")
    records(value["sources"], "sources")
    require(bool(value["sources"]), "sources: include at least the user's request")
    source_ids = set()
    for source in value["sources"]:
        fields(source, "id reference summary", "source")
        identifier(source["id"], "source.id")
        require(source["id"] not in source_ids, "sources: duplicate identifier")
        source_ids.add(source["id"])
        text(source["reference"], "source.reference")
        text(source["summary"], "source.summary")
    strings(value["constraints"], "constraints")
    decisions_valid(value["decisions"])
    tracking_valid(value["tracking"])


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def replay(ledger):
    """Derive counters and decisions from history; never trust supplied counters."""
    fields(ledger, "schema_version input events", "ledger")
    version(ledger["schema_version"])
    validate_input(ledger["input"])
    records(ledger["events"], "events")
    decisions = copy.deepcopy(ledger["input"]["decisions"])
    by_id = decisions_valid(decisions)
    event_ids, questions, prompts = set(), {}, set()
    pending = {}
    batches = 0
    for event in ledger["events"]:
        identifier(event.get("id"), "event.id")
        require(event["id"] not in event_ids, "events: duplicate event identifier")
        event_ids.add(event["id"])
        kind = event.get("type")
        if kind == "add-decisions":
            fields(event, "id type decisions", "event")
            records(event["decisions"], "event.decisions")
            require(bool(event["decisions"]), "add-decisions: empty event")
            decisions.extend(copy.deepcopy(event["decisions"]))
            by_id = decisions_valid(decisions)
        elif kind == "resolve":
            fields(event, "id type resolutions", "event")
            records(event["resolutions"], "resolutions")
            require(bool(event["resolutions"]), "resolve: empty event")
            # Facts may settle only unasked decisions. Human answers use answer events.
            for item in event["resolutions"]:
                fields(item, "decision_id answer source", "resolution")
                key = item["decision_id"]
                require(isinstance(key, str) and key in by_id, "resolve: unknown decision")
                require(key not in pending.values(), "resolve: record the user's answer to the pending question")
                require(by_id[key]["resolution"] is None, "resolve: decision already settled")
                resolution({"answer": item["answer"], "source": item["source"]}, "resolution")
                by_id[key]["resolution"] = {"answer": item["answer"], "source": item["source"]}
            by_id = decisions_valid(decisions)
        elif kind == "ask":
            fields(event, "id type questions", "event")
            records(event["questions"], "questions")
            require(bool(event["questions"]), "ask: a batch must contain at least one question")
            require(not pending, "ask: answer the pending batch before asking another")
            batches += 1
            require(batches <= MAX_BATCHES, "ask: maximum 2 batches exceeded")
            require(len(questions) + len(event["questions"]) <= MAX_QUESTIONS,
                    "ask: maximum 10 questions exceeded")
            for question in event["questions"]:
                fields(question, "id decision_id prompt options recommended_option", "question")
                require(question["id"] == f"Q{len(questions) + 1}", "question.id: expected next sequential Q number")
                key = question["decision_id"]
                require(isinstance(key, str) and key in by_id, "question: unknown decision")
                decision = by_id[key]
                require(decision["resolution"] is None, "question: decision already settled")
                require(key not in (q["decision_id"] for q in questions.values()), "question: decision already asked")
                require(all(by_id[d]["resolution"] is not None for d in decision["depends_on"]),
                        "question: dependencies must be settled before this batch")
                text(question["prompt"], "question.prompt")
                normalized = " ".join(question["prompt"].casefold().split())
                require(normalized not in prompts, "question: duplicate prompt")
                prompts.add(normalized)
                strings(question["options"], "question.options")
                require(len(question["options"]) in (0, 2, 3, 4), "question.options: use zero or 2-4 options")
                recommended = question["recommended_option"]
                require(recommended is None or (type(recommended) is int and
                        0 <= recommended < len(question["options"])), "question.recommended_option: invalid index")
                questions[question["id"]] = question
                pending[question["id"]] = key
        elif kind == "answer":
            fields(event, "id type answers", "event")
            records(event["answers"], "answers")
            require(bool(event["answers"]), "answer: empty event")
            for answer in event["answers"]:
                fields(answer, "question_id answer source", "answer")
                key = answer["question_id"]
                require(isinstance(key, str) and key in pending, "answer: question is not pending")
                resolution({"answer": answer["answer"], "source": answer["source"]}, "answer")
                decision_id = pending.pop(key)
                by_id[decision_id]["resolution"] = {"answer": answer["answer"], "source": answer["source"]}
        else:
            raise ValueError("event.type: expected add-decisions, resolve, ask, or answer")
    return {
        "revision": len(ledger["events"]), "questions_used": len(questions), "batches_used": batches,
        "remaining_questions": MAX_QUESTIONS - len(questions), "remaining_batches": MAX_BATCHES - batches,
        "pending_question_ids": list(pending), "pending_decision_ids": list(pending.values()),
        "ready_decision_ids": [key for key, d in by_id.items() if d["resolution"] is None
                               and key not in pending.values()
                               and all(by_id[x]["resolution"] is not None for x in d["depends_on"])],
        "decisions": decisions,
    }


def validate_output(ledger, value):
    state = replay(ledger)
    fields(value, "schema_version project_id input_sha256 ledger_sha256 status title users problem "
           "desired_outcome in_scope out_of_scope success_criteria constraints decisions assumptions "
           "blockers tracking next_action", "output")
    version(value["schema_version"])
    require(value["project_id"] == ledger["input"]["project_id"], "output: wrong project_id")
    require(value["input_sha256"] == digest(ledger["input"]), "output: stale input digest")
    require(value["ledger_sha256"] == digest(ledger), "output: stale ledger digest")
    require(value["status"] in ("ready-for-planning", "blocked"), "output.status: invalid state")
    for key in ("title", "problem", "desired_outcome", "next_action"):
        text(value[key], f"output.{key}")
    for key in ("users", "in_scope", "out_of_scope"):
        strings(value[key], f"output.{key}", minimum=1)
    strings(value["constraints"], "output.constraints")
    require(set(ledger["input"]["constraints"]) <= set(value["constraints"]),
            "output.constraints: cannot drop input constraints")
    tracking_valid(value["tracking"])
    require(value["tracking"] == ledger["input"]["tracking"], "output.tracking: must preserve input targets")
    records(value["success_criteria"], "success_criteria")
    require(bool(value["success_criteria"]), "success_criteria: include observable success and verification")
    success_ids = set()
    for criterion in value["success_criteria"]:
        fields(criterion, "id criterion verification", "success criterion")
        identifier(criterion["id"], "success criterion.id")
        require(criterion["id"] not in success_ids, "success_criteria: duplicate identifier")
        success_ids.add(criterion["id"])
        text(criterion["criterion"], "success criterion.criterion")
        text(criterion["verification"], "success criterion.verification")
    expected = [{"id": d["id"], **d["resolution"]} for d in state["decisions"] if d["resolution"] is not None]
    require(value["decisions"] == expected, "output.decisions: must match settled decisions and their sources")
    unresolved = {d["id"]: d for d in state["decisions"] if d["resolution"] is None}
    covered, blocking = set(), set()
    for key, required in (("assumptions", "decision_id statement impact"),
                          ("blockers", "decision_id reason next_action")):
        records(value[key], key)
        seen = set()
        for entry in value[key]:
            fields(entry, required, key)
            decision_id = entry["decision_id"]
            require(decision_id is None or (isinstance(decision_id, str) and decision_id in unresolved),
                    f"{key}: reference an unresolved decision or null")
            for field in required.split()[1:]:
                text(entry[field], f"{key}.{field}")
            if decision_id is not None:
                require(decision_id not in seen and decision_id not in covered,
                        f"{key}: duplicate or conflicting decision reference")
                seen.add(decision_id)
                covered.add(decision_id)
                if key == "blockers":
                    blocking.add(decision_id)
                else:
                    require(not unresolved[decision_id]["blocking"], "assumptions: blocking decision needs a blocker")
    require(covered == set(unresolved), "output: every unresolved decision needs an assumption or blocker")
    require(all(not d["blocking"] or key in blocking for key, d in unresolved.items()),
            "output: unresolved blocking decisions need blockers")
    require(set(state["pending_decision_ids"]) <= blocking, "output: unanswered questions need blockers")
    require(not value["blockers"] or value["status"] == "blocked", "output: blockers forbid ready-for-planning")
    if value["status"] == "blocked":
        require(bool(value["blockers"]), "output: blocked status needs an actionable blocker")
    return state


def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"JSON: duplicate key {key}")
            result[key] = value
        return result

    def constant(value):
        raise ValueError(f"JSON: invalid constant {value}")

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=constant)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


@contextmanager
def locked(path):
    lock = path.with_name(path.name + ".lock")
    # An interrupted writer leaves a visible lock. Never silently break it.
    with lock.open("x", encoding="utf-8") as handle:
        handle.write("Project interview update in progress. Inspect the writer before removing this lock.\n")
    try:
        require(not path.is_symlink(), "ledger: refusing symlink")
        yield
    finally:
        lock.unlink()


def start(value, path):
    validate_input(value)
    with locked(path):
        if path.exists():
            existing = load(path)
            replay(existing)
            require(existing["input"] == value, "start: existing ledger belongs to a different input; preserve it")
            return existing, "unchanged"
        ledger = {"schema_version": 1, "input": copy.deepcopy(value), "events": []}
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(encoded(ledger))
        return ledger, "created"


def apply_event(path, event, expected_revision):
    with locked(path):
        before = path.read_bytes()
        ledger = load(path)
        state = replay(ledger)
        require(isinstance(event, dict), "event: expected object")
        for previous in ledger["events"]:
            if previous["id"] == event.get("id"):
                require(previous == event, "event: existing identifier has different content")
                return ledger, "unchanged"
        require(state["revision"] == expected_revision, "ledger: stale revision; read current status before retrying")
        ledger["events"].append(event)
        replay(ledger)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent,
                                             prefix=path.name + ".", suffix=".tmp", delete=False) as handle:
                temporary_path = Path(handle.name)
                handle.write(encoded(ledger))
            require(not path.is_symlink() and path.read_bytes() == before, "ledger: changed during update")
            os.replace(temporary_path, path)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()
        return ledger, "updated"


def render(ledger, value):
    state = validate_output(ledger, value)
    lines = [f"# {value['title']}", "", f"Status: {value['status']}", "",
             f"Project: {value['project_id']}", "", f"Problem: {value['problem']}", "",
             f"Desired outcome: {value['desired_outcome']}"]
    for key, title in (("users", "Users"), ("in_scope", "In scope"),
                       ("out_of_scope", "Out of scope"), ("constraints", "Constraints")):
        lines.extend(["", f"## {title}", ""] + [f"- {x}" for x in value[key]])
    lines.extend(["", "## Success criteria", ""])
    for criterion in value["success_criteria"]:
        lines.extend([f"- {criterion['id']}: {criterion['criterion']}", f"  Verification: {criterion['verification']}"])
    lines.extend(["", "## Decisions", ""])
    for decision in value["decisions"]:
        lines.append(f"- {decision['id']}: {decision['answer']} (Source: {decision['source']})")
    for key, title, main, detail in (("assumptions", "Assumptions", "statement", "impact"),
                                    ("blockers", "Blockers", "reason", "next_action")):
        lines.extend(["", f"## {title}", ""])
        lines.extend(f"- {entry[main]} — {entry[detail]}" for entry in value[key])
        if not value[key]:
            lines.append("None.")
    lines.extend(["", "## Sources", ""])
    lines.extend(f"- {s['id']}: {s['reference']} — {s['summary']}" for s in ledger["input"]["sources"])
    tracking = value["tracking"]
    lines.extend(["", "## Handoff", "", "Executable tasks require GitHub Issues and Projects.", "",
                  f"Repository: {tracking['repository'] or 'Not selected yet'}",
                  f"Project: {tracking['project'] or 'Not selected yet'}", "",
                  "Tracking references are declarations; this skill does not verify or publish GitHub tasks.", "",
                  f"Next action: {value['next_action']}", "", "## Interview record", "",
                  f"{state['questions_used']}/10 questions; {state['batches_used']}/2 batches."])
    if state["pending_question_ids"]:
        lines.extend(["", "### Pending questions", ""])
        for event in ledger["events"]:
            if event["type"] != "ask":
                continue
            for question in event["questions"]:
                if question["id"] not in state["pending_question_ids"]:
                    continue
                lines.append(f"- {question['id']}: {question['prompt']}")
                for index, option in enumerate(question["options"]):
                    label = " (Recommended; unanswered)" if index == question["recommended_option"] else ""
                    lines.append(f"  - {option}{label}")
                lines.append("  Free text and qualifications are welcome. No answer has been recorded.")
    lines.extend(["", f"Input SHA-256: {value['input_sha256']}",
                  f"Ledger SHA-256: {value['ledger_sha256']}", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("validate-input", help="Validate agent-prepared intake JSON")
    command.add_argument("input", type=Path)
    command = commands.add_parser("start", help="Create or safely resume a ledger without resetting its budget")
    command.add_argument("input", type=Path)
    command.add_argument("--ledger", required=True, type=Path)
    command = commands.add_parser("status", help="Validate ledger and derive counters, frontier, and binding digests")
    command.add_argument("ledger", type=Path)
    command = commands.add_parser("apply", help="Validate and atomically append an event; exact retries are no-ops")
    command.add_argument("ledger", type=Path)
    command.add_argument("event", type=Path)
    command.add_argument("--expect-revision", required=True, type=int)
    for name in ("validate-output", "render"):
        command = commands.add_parser(name)
        command.add_argument("ledger", type=Path)
        command.add_argument("definition", type=Path)
        if name == "render":
            command.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "validate-input":
            validate_input(load(args.input))
            result = {"status": "valid"}
        elif args.command in ("start", "apply", "status"):
            if args.command == "start":
                ledger, status = start(load(args.input), args.ledger)
            elif args.command == "apply":
                ledger, status = apply_event(args.ledger, load(args.event), args.expect_revision)
            else:
                ledger, status = load(args.ledger), "valid"
            result = {"status": status, **replay(ledger), "input_sha256": digest(ledger["input"]),
                      "ledger_sha256": digest(ledger)}
        else:
            ledger, definition = load(args.ledger), load(args.definition)
            validate_output(ledger, definition)
            if args.command == "render":
                with args.output.open("x", encoding="utf-8", newline="\n") as handle:
                    handle.write(render(ledger, definition))
            result = {"status": "valid", "definition_status": definition["status"]}
        print(encoded(result), end="")
        return 0
    except (ValueError, OSError, RecursionError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
