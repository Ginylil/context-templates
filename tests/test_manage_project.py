"""Project definition/planning/routing integration, with no external operations."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


manager = module(SKILLS / "ct-product-manage-project/scripts/manage.py", "ct_manager_test")
workflow = manager.workflow
resources = module(ROOT / "scripts/ct_lifecycle.py", "ct_resources_test")
installer = module(ROOT / "scripts/skills.py", "ct_lifecycle_installer")
engineering = module(ROOT / "tests/test_engineering_lifecycle.py", "ct_manager_engineering_fixture")


def asset(name, filename):
    return json.loads((SKILLS / name / "assets" / filename).read_text(encoding="utf-8"))


class ManageProjectTests(unittest.TestCase):
    def setUp(self):
        self.fixture = engineering.EngineeringLifecycleTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.base = self.fixture.base
        self.state = asset("ct-product-manage-project", "example-state.json")
        self.ledger = self.fixture.ledger
        self.definition = self.fixture.definition
        self.plan = asset("ct-rnd-plan-development", "example-plan.json")
        self.state.update(ledger=self.fixture.ledger_ref, definition=self.fixture.definition_ref,
                          plan=self.write("plan.json", self.plan))

    def write(self, name, value):
        return self.fixture.write(name, value)

    def route(self, verify=False):
        return manager.route(self.state, self.base, SKILLS, verify)

    def tracking(self):
        payload = manager.plan_contract.prepare(self.ledger, self.definition, self.plan)
        value = {key: payload[key] for key in ("schema_version", "project_id", "plan_id", "plan_sha256")}
        value["issues"] = [{"task_id": task["id"], "url": f"https://github.com/example/follow-up-notes/issues/{n}"}
                           for n, task in enumerate(self.plan["tasks"], 1)]
        self.state["tracking"] = self.write("tracking.json", value)
        return value

    def live(self, closed=()):
        return {"tasks": [{"task_id": task["id"], "issue_state": "closed" if task["id"] in closed else "open",
                           "project_status": "Done" if task["id"] in closed else "Backlog"}
                          for task in self.plan["tasks"]]}

    def feature_receipt(self, task):
        policy, intake, report = self.fixture.ready("ct-rnd-build-feature")
        requirements = sorted({x for c in task["acceptance"] for x in c["requirement_ids"]})
        intake["inputs"].update(task_id=task["id"], requirement_ids=requirements,
            acceptance=[{"id": c["id"], "requirement_ids": c["requirement_ids"],
                         "scenario": c["criterion"], "verification": c["verification"]} for c in task["acceptance"]])
        report["result"]["task_id"] = task["id"]
        report["result"]["scenarios"] = [{"id": c["id"], "requirement_ids": c["requirement_ids"],
            "status": "passed", "evidence_ids": ["after"]} for c in task["acceptance"]]
        report["input_sha256"] = workflow.digest(intake)
        workflow.validate_output(policy, intake, report, self.base)
        entry = {"task_id": task["id"], "input": self.write(task["id"] + "-input.json", intake),
                 "output": self.write(task["id"] + "-output.json", report)}
        self.state["task_receipts"].append(entry)
        return intake, report, entry

    def gate_receipt(self, name):
        if name == "ct-rnd-review-code":
            policy, intake, report = self.fixture.ready(name)
        else:
            policy, intake, report = [asset(name, x) for x in ("contract.json", "example-input.json", "example-output.json")]
            intake.update(repository={"path": "repository", "revision": self.fixture.revision,
                                      "working_tree_sha256": workflow.tree_digest(self.fixture.repository)},
                          ledger=self.fixture.ledger_ref, definition=self.fixture.definition_ref,
                          sources=[{"id": "source", **self.fixture.source_ref}])
            report.update(status="ready", blockers=[], summary="Synthetic integration assessment; no live release.",
                          constraints=list(dict.fromkeys(intake["constraints"] + self.definition["constraints"])),
                          evidence=copy.deepcopy(self.fixture.evidence))
            requirements = [x["id"] for x in self.definition["success_criteria"]]
            if name == "ct-qa-test-user-flows":
                intake["inputs"].update(candidate_revision=self.fixture.revision,
                    journeys=[{"id": "notes", "actor": "Owner", "goal": "Manage notes", "requirement_ids": requirements}])
                report["result"].update(candidate_revision=self.fixture.revision, verdict="passed", scenarios=[{
                    "id": "all-flows", "journey_id": "notes", "requirement_ids": requirements,
                    "steps": ["Exercise synthetic fixture"], "expected": "Owner-only records", "actual": "Fixture checked",
                    "status": "passed", "evidence_ids": ["after"]}])
            elif name == "ct-security-review-project":
                report["result"]["assessed_areas"] = [{"id": "privacy", "area": "Record isolation", "status": "limited",
                    "evidence_ids": ["deliverable"], "limitations": ["Synthetic integration fixture, not live security proof."]}]
            elif name == "ct-devops-release-project":
                intake["inputs"]["candidate_revision"] = self.fixture.revision
                report["result"].update(candidate_revision=self.fixture.revision, build_check="check",
                    checks=[{"id": "build", "name": "Compile fixture", "status": "passed", "evidence_ids": ["check"]}],
                    outcome="candidate-prepared")
            report["input_sha256"] = workflow.digest(intake)
        workflow.validate_output(policy, intake, report, self.base)
        entry = {"skill": name, "input": self.write(name + "-input.json", intake),
                 "output": self.write(name + "-output.json", report)}
        self.state["receipts"].append(entry)
        return intake, report, entry

    def complete_tasks(self):
        self.tracking()
        self.state["local_only"] = False
        self.state["repository"] = {"path": "repository", "revision": self.fixture.revision,
                                    "working_tree_sha256": workflow.tree_digest(self.fixture.repository)}
        for task in self.plan["tasks"]:
            self.feature_receipt(task)
        return self.live([x["id"] for x in self.plan["tasks"]])

    def test_define_plan_and_tracking_handoffs_reuse_scope(self):
        self.state.update(ledger=None, definition=None, plan=None)
        self.assertEqual(self.route()["next_skill"], "ct-product-define-project")
        self.state.update(ledger=self.fixture.ledger_ref, definition=self.fixture.definition_ref)
        result = self.route()
        self.assertEqual(result["next_skill"], "ct-rnd-plan-development")
        self.assertEqual(result["interview_usage"], {"questions": 2, "batches": 1, "pending": []})
        self.state["plan"] = self.write("plan.json", self.plan)
        result = self.route()
        self.assertEqual(result["status"], "blocked")
        self.assertIn("Publish and verify", result["reason"])

    def test_local_only_prevents_live_read_even_with_flag(self):
        self.tracking()
        with patch.object(manager.plan_contract, "verify_tracking", side_effect=AssertionError("network forbidden")):
            result = self.route(verify=True)
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["tracking_checked_live"])

    def test_stored_tracking_is_not_treated_as_live_proof(self):
        self.tracking()
        self.state["local_only"] = False
        with patch.object(manager.plan_contract, "verify_tracking", side_effect=AssertionError("not requested")):
            result = self.route()
        self.assertIn("stored tracking receipt", result["reason"])

    def test_missing_specialist_is_explicitly_blocked(self):
        self.state.update(ledger=None, definition=None, plan=None)
        result = manager.route(self.state, self.base, self.base / "empty-skills")
        self.assertEqual(result["status"], "blocked")
        self.assertIn("not installed", result["reason"])

    def test_explicit_specialist_does_not_force_full_project_pipeline(self):
        self.state.update(intent="research-market", ledger=None, definition=None, plan=None)
        result = self.route()
        self.assertEqual((result["status"], result["next_skill"]), ("ready", "ct-marketing-research-market"))

    def test_manager_intent_never_routes_back_to_itself(self):
        self.state.update(intent="manage-project", plan=None)
        self.assertEqual(self.route()["next_skill"], "ct-rnd-plan-development")

    def test_live_tracking_admits_setup_then_dependency_frontier(self):
        self.tracking()
        self.state["local_only"] = False
        with patch.object(manager.plan_contract, "verify_tracking", return_value=self.live()) as verified:
            result = self.route(True)
            self.assertEqual(result["next_skill"], "ct-rnd-set-up-project")
            self.assertFalse(verified.call_args.kwargs["require_backlog"])
            self.state["repository"] = {"path": "repository", "revision": self.fixture.revision,
                                        "working_tree_sha256": workflow.tree_digest(self.fixture.repository)}
            result = self.route(True)
            self.assertEqual((result["next_skill"], result["task_id"]), ("ct-rnd-build-feature", "save-private-note"))
        self.feature_receipt(self.plan["tasks"][0])
        with patch.object(manager.plan_contract, "verify_tracking", return_value=self.live(["save-private-note"])):
            result = self.route(True)
        self.assertEqual(result["task_id"], "list-follow-ups")

    def test_remote_done_without_local_proof_is_not_completed(self):
        self.tracking()
        self.state["local_only"] = False
        with patch.object(manager.plan_contract, "verify_tracking", return_value=self.live(["save-private-note"])):
            result = self.route(True)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["task_id"], "save-private-note")
        self.assertIn("disagree", result["reason"])

    def test_task_receipt_must_match_identity_and_requirements(self):
        _, _, entry = self.feature_receipt(self.plan["tasks"][0])
        entry["task_id"] = "list-follow-ups"
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            self.route()

    def test_non_git_directory_cannot_skip_repository_setup(self):
        (self.base / "not-git").mkdir()
        self.state["repository"] = {"path": "not-git", "revision": None, "working_tree_sha256": None}
        with self.assertRaisesRegex(ValueError, "repository.revision"):
            self.route()

    def test_task_receipt_cannot_change_planned_acceptance(self):
        intake, report, entry = self.feature_receipt(self.plan["tasks"][0])
        intake["inputs"]["acceptance"][0]["scenario"] = "A weaker replacement criterion."
        report["input_sha256"] = workflow.digest(intake)
        entry.update(input=self.write("changed-input.json", intake), output=self.write("changed-output.json", report))
        with self.assertRaisesRegex(ValueError, "changes planned acceptance"):
            self.route()

    def test_completed_task_proof_survives_later_source_changes(self):
        self.tracking()
        self.state["local_only"] = False
        self.feature_receipt(self.plan["tasks"][0])
        self.gate_receipt("ct-rnd-review-code")
        repo = self.fixture.repository
        (repo / "next-feature.py").write_text('print("next task")\n')
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                        "commit", "-qm", "Next feature"], cwd=repo, check=True, capture_output=True)
        self.state["repository"] = {"path": "repository", "revision": workflow.revision(repo),
                                    "working_tree_sha256": workflow.tree_digest(repo)}
        # Historical task proof remains valid; a current review gate must be refreshed.
        with self.assertRaisesRegex(ValueError, "repository: revision mismatch"):
            self.route()
        self.state["receipts"] = []
        with patch.object(manager.plan_contract, "verify_tracking", return_value=self.live(["save-private-note"])):
            result = self.route(True)
        self.assertEqual(result["task_id"], "list-follow-ups")

    def test_historical_task_revision_must_belong_to_current_history(self):
        intake, report, entry = self.feature_receipt(self.plan["tasks"][0])
        intake["repository"]["revision"] = "0" * 40
        report["input_sha256"] = workflow.digest(intake)
        entry.update(input=self.write("wrong-history-input.json", intake), output=self.write("wrong-history-output.json", report))
        with self.assertRaisesRegex(ValueError, "not an ancestor"):
            self.route()

    def test_historical_task_cannot_use_proof_for_another_source_snapshot(self):
        intake, report, entry = self.feature_receipt(self.plan["tasks"][0])
        intake["repository"]["working_tree_sha256"] = "0" * 64
        report["input_sha256"] = workflow.digest(intake)
        entry.update(input=self.write("wrong-tree-input.json", intake), output=self.write("wrong-tree-output.json", report))
        with self.assertRaisesRegex(ValueError, "working tree changed after check"):
            self.route()

    def test_task_ready_proof_without_github_closure_is_not_done(self):
        self.tracking()
        self.state["local_only"] = False
        self.feature_receipt(self.plan["tasks"][0])
        with patch.object(manager.plan_contract, "verify_tracking", return_value=self.live()):
            result = self.route(True)
        self.assertEqual(result["status"], "blocked")

    def test_cross_scope_and_stale_inputs_fail(self):
        self.state["project_id"] = "other-project"
        with self.assertRaisesRegex(ValueError, "scope mismatch"):
            self.route()
        self.state["project_id"] = "follow-up-notes"
        self.state["plan"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "stale or mismatched"):
            self.route()

    def test_all_tasks_done_routes_to_review_without_claiming_release(self):
        self.tracking()
        self.state["local_only"] = False
        self.state["repository"] = {"path": "repository", "revision": self.fixture.revision,
                                    "working_tree_sha256": workflow.tree_digest(self.fixture.repository)}
        for task in self.plan["tasks"]:
            self.feature_receipt(task)
        with patch.object(manager.plan_contract, "verify_tracking", return_value=self.live([x["id"] for x in self.plan["tasks"]])):
            result = self.route(True)
        self.assertEqual((result["status"], result["next_skill"]), ("ready", "ct-rnd-review-code"))
        self.assertIsNone(result["milestone"])

    def test_integrated_candidate_completion_does_not_claim_staging(self):
        live = self.complete_tasks()
        for name in ("ct-rnd-review-code", "ct-qa-test-user-flows", "ct-security-review-project", "ct-devops-release-project"):
            self.gate_receipt(name)
        with patch.object(manager.plan_contract, "verify_tracking", return_value=live):
            self.state["target_stage"] = "candidate"
            result = self.route(True)
            self.assertEqual((result["status"], result["milestone"]), ("complete", "candidate"))
            self.state["target_stage"] = "staging"
            result = self.route(True)
            self.assertEqual((result["status"], result["next_skill"]), ("ready", "ct-devops-release-project"))
            self.assertIsNone(result["milestone"])

    def test_completed_failed_qa_is_not_a_passing_gate(self):
        live = self.complete_tasks()
        self.gate_receipt("ct-rnd-review-code")
        _, report, entry = self.gate_receipt("ct-qa-test-user-flows")
        report["result"]["scenarios"][0].update(status="failed", evidence_ids=["before"])
        report["result"]["verdict"] = "failed"
        entry["output"] = self.write("failed-qa.json", report)
        with patch.object(manager.plan_contract, "verify_tracking", return_value=live):
            result = self.route(True)
        self.assertEqual((result["status"], result["next_skill"]), ("blocked", "ct-rnd-fix-bug"))

    def test_ready_review_with_high_finding_blocks_release(self):
        live = self.complete_tasks()
        _, report, entry = self.gate_receipt("ct-rnd-review-code")
        report["result"]["findings"] = [{"id": "privacy", "severity": "high", "path": "check.py", "line": 1,
            "problem": "Synthetic demonstrated cross-user access", "trigger": "Second user requests owner record",
            "impact": "Record disclosure", "recommended_fix": "Enforce owner isolation", "evidence_ids": ["before"]}]
        entry["output"] = self.write("high-review.json", report)
        with patch.object(manager.plan_contract, "verify_tracking", return_value=live):
            result = self.route(True)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("high or critical", result["reason"])

    def test_modified_route_output_is_rejected(self):
        state = self.base / "state.json"
        state.write_text(json.dumps(self.state), encoding="utf-8")
        output = self.base / "route.json"
        script = SKILLS / "ct-product-manage-project/scripts/manage.py"
        result = subprocess.run([sys.executable, str(script), str(state), "--skills-root", str(SKILLS),
                                 "--output", str(output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(output.read_text(encoding="utf-8"))
        value["next_skill"] = "ct-devops-release-project"
        output.write_text(json.dumps(value), encoding="utf-8")
        result = subprocess.run([sys.executable, str(script), str(state), "--skills-root", str(SKILLS),
                                 "--validate-output", str(output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("modified route", result.stderr)


class StandaloneLifecycleTests(unittest.TestCase):
    def test_fingerprint_disambiguates_untracked_file_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                            "commit", "--allow-empty", "-qm", "fixture"], cwd=root, check=True, capture_output=True)
            (root / "a").write_bytes(b"b\0payload")
            first = workflow.tree_digest(root)
            (root / "a").write_bytes(b"")
            (root / "b").write_bytes(b"payload")
            self.assertNotEqual(first, workflow.tree_digest(root))
    def test_generated_copies_have_no_source_drift(self):
        for path, expected in resources.outputs().items():
            with self.subTest(path=path):
                self.assertEqual(path.read_bytes(), expected)

    def test_all_domains_validate_from_each_isolated_agent_install(self):
        names = [x["skill"] for x in json.loads((SKILLS / "ct-product-manage-project/assets/catalog.json").read_text(encoding="utf-8"))]
        domains = [name for name in names if (SKILLS / name / "assets/contract.json").is_file()]
        self.assertEqual(len(domains), 17)
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "isolated home"
            for agent in installer.TARGETS:
                with contextlib.redirect_stdout(io.StringIO()):
                    installer.install(ROOT, home, [agent], names, False)
                base = home / installer.TARGETS[agent]
                for name in domains:
                    folder = base / name
                    result = subprocess.run([sys.executable, str(folder / "scripts/workflow.py"), "validate-output",
                        str(folder / "assets/example-input.json"), str(folder / "assets/example-output.json")],
                        cwd=directory, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, f"{agent}/{name}: {result.stderr}")
                manager_folder = base / "ct-product-manage-project"
                result = subprocess.run([sys.executable, str(manager_folder / "scripts/manage.py"),
                    str(manager_folder / "assets/example-state.json"), "--skills-root", str(base)],
                    cwd=directory, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["next_skill"], "ct-product-define-project")

    def test_command_capture_refuses_existing_output_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            cwd = Path(directory)
            marker = cwd / "side-effect"
            output = cwd / "proof.json"
            output.write_text("existing user artifact", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                workflow.record([sys.executable, "-c", "from pathlib import Path; Path('side-effect').touch()"], cwd, output)
            self.assertFalse(marker.exists())
            self.assertEqual(output.read_text(encoding="utf-8"), "existing user artifact")

    def test_duplicate_command_arguments_are_valid_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            path = base / "proof.json"
            workflow.record([sys.executable, "-c", "import sys; assert sys.argv[1:] == ['same','same']", "same", "same"], base, path)
            item = {"id": "check", "kind": "command", "reference": {"path": path.name, "sha256": workflow.file_digest(path)}}
            context = {"evidence": {}}
            workflow.evidence_valid(item, base, context)
            self.assertEqual(context["evidence"]["check"]["data"]["exit_code"], 0)


if __name__ == "__main__":
    unittest.main()
