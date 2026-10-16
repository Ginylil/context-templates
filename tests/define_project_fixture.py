"""Test-free define project fixtures shared by contract suites."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
from assembled_catalog import SKILLS
SKILL = SKILLS / "ct-product-define-project"


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


class DefineProjectFixture(unittest.TestCase):
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
