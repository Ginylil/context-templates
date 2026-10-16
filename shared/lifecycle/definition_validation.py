"""Project definition schemas and deterministic interview-ledger replay."""
from __future__ import annotations

import copy
import hashlib
import json
import re

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
