"""Behavioral proof for the standalone definition contract and interview ledger."""
import contextlib
import copy
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/ct-product-define-project"


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


project = module(SKILL / "scripts/project.py", "ct_project")
installer = module(ROOT / "scripts/skills.py", "ct_project_installer")


def asset(name):
    return json.loads((SKILL / "assets" / name).read_text(encoding="utf-8"))


def decision(key, blocking=True, dependencies=None):
    return {"id": key, "topic": f"Choice about {key}", "depends_on": dependencies or [],
            "blocking": blocking, "resolution": None}


def batch(keys, start=1, event_id="batch-one"):
    return {"id": event_id, "type": "ask", "questions": [
        {"id": f"Q{number}", "decision_id": key, "prompt": f"Choose {key}?",
         "options": ["First choice", "Second choice"], "recommended_option": 0}
        for number, key in enumerate(keys, start)]}


def answers(start=1, count=1, event_id="answers-one"):
    return {"id": event_id, "type": "answer", "answers": [
        {"question_id": f"Q{n}", "answer": "Second choice, with a user qualification.",
         "source": f"Actual test user submission Q{n}"} for n in range(start, start + count)]}


class DefineProjectTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.path = self.work / "ledger.json"

    def start(self, value=None):
        return project.start(value or asset("example-input.json"), self.path)[0]

    def apply(self, event):
        revision = project.replay(project.load(self.path))["revision"]
        return project.apply_event(self.path, event, revision)[0]

    def independent(self, count):
        value = asset("example-input.json")
        value["decisions"] = [decision(f"choice-{n}") for n in range(1, count + 1)]
        self.start(value)
        return [d["id"] for d in value["decisions"]]

    def bind(self, ledger):
        value = asset("example-definition.json")
        value["input_sha256"] = project.digest(ledger["input"])
        value["ledger_sha256"] = project.digest(ledger)
        value["decisions"] = [{"id": d["id"], **d["resolution"]}
                              for d in project.replay(ledger)["decisions"] if d["resolution"] is not None]
        value["assumptions"] = []
        return value

    def assert_rejected_without_write(self, event, message):
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, message):
            self.apply(event)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse(self.path.with_suffix(".json.lock").exists())

    def cli(self, *args, script=None):
        return subprocess.run([sys.executable, str(script or SKILL / "scripts/project.py"), *map(str, args)],
                              cwd=self.work, capture_output=True, text=True)

    def test_complete_examples_are_bound_and_renderable(self):
        ledger, value = asset("example-ledger.json"), asset("example-definition.json")
        self.assertEqual(ledger["input"], asset("example-input.json"))
        self.assertEqual(ledger["events"], [asset("example-batch.json"), asset("example-answers.json")])
        state = project.validate_output(ledger, value)
        self.assertEqual((state["questions_used"], state["batches_used"]), (2, 1))
        self.assertIn("Not selected yet", project.render(ledger, value))
        self.assertIn("Manual entry is enough initially.", project.render(ledger, value))

    def test_ten_questions_in_one_batch_and_no_extra_question(self):
        keys = self.independent(11)
        self.apply(batch(keys[:10]))
        ledger = self.apply(answers(count=10))
        state = project.replay(ledger)
        self.assertEqual((state["questions_used"], state["batches_used"]), (10, 1))
        self.assertEqual(state["remaining_questions"], 0)
        self.assert_rejected_without_write(batch(keys[10:], 11, "batch-two"), "maximum 10")

    def test_two_batches_share_budget_and_third_fails_before_ten_questions(self):
        keys = self.independent(3)
        self.apply(batch(keys[:1]))
        self.apply(answers())
        self.apply(batch(keys[1:2], 2, "batch-two"))
        ledger = self.apply(answers(2, 1, "answers-two"))
        self.assertEqual(project.replay(ledger)["remaining_questions"], 8)
        self.assert_rejected_without_write(batch(keys[2:], 3, "batch-three"), "maximum 2 batches")

    def test_second_batch_cannot_take_total_past_ten(self):
        keys = self.independent(11)
        self.apply(batch(keys[:7]))
        self.apply(answers(count=7))
        self.assert_rejected_without_write(batch(keys[7:], 8, "batch-two"), "maximum 10")
        ledger = self.apply(batch(keys[7:10], 8, "batch-two"))
        self.assertEqual(project.replay(ledger)["questions_used"], 10)

    def test_cli_limit_error_preserves_ledger(self):
        keys = self.independent(11)
        self.apply(batch(keys[:10]))
        self.apply(answers(count=10))
        event = self.work / "eleventh-question.json"
        event.write_text(project.encoded(batch(keys[10:], 11, "batch-two")), encoding="utf-8")
        before = self.path.read_bytes()
        result = self.cli("apply", self.path, event, "--expect-revision", 2)
        self.assertEqual(result.returncode, 1)
        self.assertIn("maximum 10 questions", result.stderr)
        self.assertEqual(self.path.read_bytes(), before)

    def test_dependency_within_same_batch_is_rejected(self):
        value = asset("example-input.json")
        value["decisions"] = [decision("audience"), decision("billing", dependencies=["audience"])]
        self.start(value)
        self.assert_rejected_without_write(batch(["audience", "billing"]), "dependencies must be settled")
        self.apply(batch(["audience"]))
        self.apply(answers())
        ledger = self.apply(batch(["billing"], 2, "batch-two"))
        self.assertEqual(project.replay(ledger)["pending_question_ids"], ["Q2"])

    def test_recommendations_are_not_answers_and_partial_answers_remain_pending(self):
        self.start()
        ledger = self.apply(asset("example-batch.json"))
        self.assertEqual(project.replay(ledger)["pending_question_ids"], ["Q1", "Q2"])
        self.assertIsNone(project.replay(ledger)["decisions"][1]["resolution"])
        ledger = self.apply(answers())
        self.assertEqual(project.replay(ledger)["pending_question_ids"], ["Q2"])
        self.assert_rejected_without_write(batch(["capture"], 3, "batch-two"), "pending batch")
        blank = answers(2, event_id="blank-answer")
        blank["answers"][0]["answer"] = " "
        self.assert_rejected_without_write(blank, "nonempty text")

    def test_exact_retry_and_start_resume_preserve_history(self):
        self.start()
        event = asset("example-batch.json")
        self.apply(event)
        before = self.path.read_bytes()
        ledger, status = project.apply_event(self.path, event, expected_revision=0)
        self.assertEqual(status, "unchanged")
        self.assertEqual(project.replay(ledger)["questions_used"], 2)
        self.assertEqual(project.start(asset("example-input.json"), self.path)[1], "unchanged")
        self.assertEqual(self.path.read_bytes(), before)
        changed = copy.deepcopy(event)
        changed["questions"][0]["prompt"] = "Different question?"
        self.assert_rejected_without_write(changed, "different content")
        other = asset("example-input.json")
        other["idea"] = "A different idea"
        with self.assertRaisesRegex(ValueError, "different input"):
            project.start(other, self.path)
        self.assertEqual(self.path.read_bytes(), before)

    def test_stale_revision_lock_and_replace_failure_preserve_ledger(self):
        self.start()
        event = asset("example-batch.json")
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "stale revision"):
            project.apply_event(self.path, event, 7)
        lock = self.path.with_suffix(".json.lock")
        lock.write_text("another writer", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            self.apply(event)
        self.assertEqual(lock.read_text(), "another writer")
        lock.unlink()
        with patch.object(project.os, "replace", side_effect=OSError("disk failure")):
            with self.assertRaisesRegex(OSError, "disk failure"):
                self.apply(event)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.work.glob("*.tmp")), [])

    def test_adaptive_decisions_and_discovered_facts_do_not_consume_questions(self):
        self.start()
        self.apply(asset("example-batch.json"))
        self.apply(asset("example-answers.json"))
        self.apply({"id": "new-branch", "type": "add-decisions",
                    "decisions": [decision("export", False, ["sharing"])]})
        ledger = self.apply({"id": "read-brief", "type": "resolve", "resolutions": [
            {"decision_id": "export", "answer": "The brief excludes export.", "source": "Supplied brief"}]})
        state = project.replay(ledger)
        self.assertEqual((state["questions_used"], state["batches_used"]), (2, 1))
        self.assertEqual(state["decisions"][-1]["resolution"]["answer"], "The brief excludes export.")
        self.assert_rejected_without_write(batch(["export"], 3, "batch-two"), "already settled")

    def test_cannot_resolve_a_pending_question_as_a_fact_or_reanswer(self):
        self.start()
        self.apply(asset("example-batch.json"))
        event = {"id": "invented-fact", "type": "resolve", "resolutions": [
            {"decision_id": "sharing", "answer": "Assume private", "source": "Agent guess"}]}
        self.assert_rejected_without_write(event, "pending question")
        self.apply(asset("example-answers.json"))
        self.assert_rejected_without_write(answers(event_id="reanswer"), "not pending")

    def test_known_decisions_and_duplicate_prompts_are_not_reasked(self):
        self.start()
        self.assert_rejected_without_write(batch(["audience"]), "already settled")
        event = asset("example-batch.json")
        event["questions"][1]["prompt"] = event["questions"][0]["prompt"].upper() + "  "
        self.assert_rejected_without_write(event, "duplicate prompt")
        event = asset("example-batch.json")
        event["questions"][1]["decision_id"] = "sharing"
        self.assert_rejected_without_write(event, "already asked")

    def test_graph_and_input_contract_reject_invalid_structures(self):
        mutations = [
            lambda v: v.update(schema_version=True),
            lambda v: v["tracking"].update(system="local"),
            lambda v: v["decisions"][1].update(depends_on=["missing"]),
            lambda v: v["decisions"][0].update(depends_on=["sharing"]),
            lambda v: v["decisions"][1].update(blocking="true"),
            lambda v: v["decisions"].append(copy.deepcopy(v["decisions"][0])),
            lambda v: v.update(sources=[]),
            lambda v: v.update(question_limit=11),
        ]
        for mutate in mutations:
            value = asset("example-input.json")
            mutate(value)
            with self.subTest(input=value), self.assertRaises(ValueError):
                project.validate_input(value)

    def test_bad_question_numbers_options_and_event_fields_rejected(self):
        self.start()
        mutations = [
            lambda e: e["questions"][0].update(id="Q2"),
            lambda e: e["questions"][0].update(recommended_option=True),
            lambda e: e["questions"][0].update(recommended_option=4),
            lambda e: e["questions"][0].update(options=["Only option"]),
            lambda e: e.update(questions=[]),
            lambda e: e.update(question_limit=20),
        ]
        for mutate in mutations:
            event = asset("example-batch.json")
            mutate(event)
            with self.subTest(event=event):
                self.assert_rejected_without_write(event, ".")

    def test_forged_counters_and_duplicate_history_fail_replay(self):
        ledger = asset("example-ledger.json")
        ledger["questions_used"] = 0
        with self.assertRaisesRegex(ValueError, "expected fields"):
            project.replay(ledger)
        ledger = asset("example-ledger.json")
        ledger["events"].append(copy.deepcopy(ledger["events"][-1]))
        with self.assertRaisesRegex(ValueError, "duplicate event"):
            project.replay(ledger)

    def test_zero_question_ready_definition_and_optional_assumption(self):
        value = asset("example-input.json")
        value["decisions"] = [decision("export", blocking=False)]
        ledger = self.start(value)
        definition = self.bind(ledger)
        definition["assumptions"] = [{"decision_id": "export", "statement": "Exclude export initially.",
                                      "impact": "Revisit if user research shows demand."}]
        state = project.validate_output(ledger, definition)
        self.assertEqual((state["questions_used"], state["batches_used"]), (0, 0))

    def test_pending_questions_require_actionable_blocked_output(self):
        self.start()
        ledger = self.apply(asset("example-batch.json"))
        definition = self.bind(ledger)
        with self.assertRaisesRegex(ValueError, "every unresolved"):
            project.validate_output(ledger, definition)
        definition["blockers"] = [{"decision_id": key, "reason": "Awaiting submitted choice.",
                                   "next_action": f"Read the user's answer for {key}."}
                                  for key in ("sharing", "capture")]
        with self.assertRaisesRegex(ValueError, "blockers forbid"):
            project.validate_output(ledger, definition)
        definition["status"] = "blocked"
        project.validate_output(ledger, definition)
        before = copy.deepcopy(ledger)
        rendered = project.render(ledger, definition)
        self.assertIn("Does the first version need collaboration?", rendered)
        self.assertIn("Personal use only (Recommended; unanswered)", rendered)
        self.assertEqual(ledger, before)

    def test_output_cannot_call_same_unknown_both_assumption_and_blocker(self):
        value = asset("example-input.json")
        value["decisions"] = [decision("export", blocking=False)]
        ledger = self.start(value)
        definition = self.bind(ledger)
        definition["status"] = "blocked"
        definition["assumptions"] = [{"decision_id": "export", "statement": "Exclude export initially.",
                                      "impact": "May revisit later."}]
        definition["blockers"] = [{"decision_id": "export", "reason": "Need a choice.",
                                   "next_action": "Read user decision."}]
        with self.assertRaisesRegex(ValueError, "conflicting decision"):
            project.validate_output(ledger, definition)

    def test_output_cannot_drop_constraints_invent_answers_or_change_tracking(self):
        ledger = asset("example-ledger.json")
        mutations = [
            lambda v: v.update(project_id="another-project"),
            lambda v: v.update(input_sha256="stale"),
            lambda v: v.update(ledger_sha256="stale"),
            lambda v: v.update(constraints=[]),
            lambda v: v["decisions"][0].update(answer="A different audience"),
            lambda v: v["tracking"].update(repository="other/repo"),
            lambda v: v.update(success_criteria=[]),
            lambda v: v["success_criteria"][0].update(verification=""),
            lambda v: v.update(status="complete"),
            lambda v: v.update(status="blocked"),
        ]
        for mutate in mutations:
            value = asset("example-definition.json")
            mutate(value)
            with self.subTest(value=value), self.assertRaises(ValueError):
                project.validate_output(ledger, value)

    def test_a_new_ledger_revision_invalidates_previous_definition(self):
        self.start()
        self.apply(asset("example-batch.json"))
        ledger = self.apply(asset("example-answers.json"))
        definition = self.bind(ledger)
        project.validate_output(ledger, definition)
        ledger = self.apply({"id": "more-context", "type": "add-decisions", "decisions": [decision("export", False)]})
        with self.assertRaisesRegex(ValueError, "stale ledger"):
            project.validate_output(ledger, definition)

    def test_cli_rejects_duplicate_json_keys_and_nonfinite_numbers_without_traceback(self):
        for raw in ('{"schema_version":1,"schema_version":1}', '{"schema_version":NaN}'):
            path = self.work / "bad.json"
            path.write_text(raw, encoding="utf-8")
            result = self.cli("validate-input", path)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Error:", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_cli_pipeline_runs_from_isolated_installs_for_all_agents(self):
        for agent in installer.TARGETS:
            with self.subTest(agent=agent):
                home = self.work / f"{agent} home"
                with contextlib.redirect_stdout(io.StringIO()):
                    installer.install(ROOT, home, [agent], [SKILL.name], False)
                installed = home / installer.TARGETS[agent] / SKILL.name
                script = installed / "scripts/project.py"
                assets = installed / "assets"
                ledger = self.work / f"{agent}-ledger.json"
                for args in [
                    ("validate-input", assets / "example-input.json"),
                    ("start", assets / "example-input.json", "--ledger", ledger),
                    ("apply", ledger, assets / "example-batch.json", "--expect-revision", 0),
                    ("apply", ledger, assets / "example-answers.json", "--expect-revision", 1),
                    ("validate-output", ledger, assets / "example-definition.json"),
                    ("render", ledger, assets / "example-definition.json", "--output", self.work / f"{agent}.md"),
                ]:
                    result = self.cli(*args, script=script)
                    self.assertEqual(result.returncode, 0, result.stderr)
                result = self.cli("status", ledger, script=script)
                self.assertEqual(json.loads(result.stdout)["questions_used"], 2)
                before = (self.work / f"{agent}.md").read_bytes()
                result = self.cli("render", ledger, assets / "example-definition.json", "--output",
                                  self.work / f"{agent}.md", script=script)
                self.assertEqual(result.returncode, 1)
                self.assertEqual((self.work / f"{agent}.md").read_bytes(), before)

    def test_built_archive_works_without_source_repository(self):
        output = self.work / "dist"
        with contextlib.redirect_stdout(io.StringIO()):
            installer.build(ROOT, output)
        extracted = self.work / "extracted"
        with zipfile.ZipFile(output / f"{SKILL.name}.zip") as archive:
            archive.extractall(extracted)
        package = extracted / SKILL.name
        result = self.cli("validate-output", package / "assets/example-ledger.json",
                          package / "assets/example-definition.json", script=package / "scripts/project.py")
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipIf(os.name == "nt", "Windows symlink creation requires optional privileges")
    def test_ledger_symlink_does_not_modify_target(self):
        target = self.work / "target.json"
        target.write_text(project.encoded(asset("example-ledger.json")), encoding="utf-8")
        self.path.symlink_to(target)
        before = target.read_bytes()
        with self.assertRaisesRegex(ValueError, "symlink"):
            project.start(asset("example-input.json"), self.path)
        self.assertEqual(target.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
