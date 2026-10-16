#!/usr/bin/env python3
"""Validate project definitions and maintain a bounded interview. Python 3.10+, no dependencies."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location(
    "ct_definition_validation", Path(__file__).with_name("definition_validation.py"))
_validation = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_validation)

MAX_QUESTIONS = _validation.MAX_QUESTIONS
MAX_BATCHES = _validation.MAX_BATCHES
ID = _validation.ID
require = _validation.require
fields = _validation.fields
text = _validation.text
identifier = _validation.identifier
strings = _validation.strings
records = _validation.records
version = _validation.version
resolution = _validation.resolution
decisions_valid = _validation.decisions_valid
tracking_valid = _validation.tracking_valid
validate_input = _validation.validate_input
digest = _validation.digest
replay = _validation.replay
validate_output = _validation.validate_output


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
