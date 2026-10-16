"""Test-free manage project fixtures shared by contract suites."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
from assembled_catalog import SKILLS


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


class ManageProjectFixture(unittest.TestCase):
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
