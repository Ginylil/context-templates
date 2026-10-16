"""Definition CLI contracts and isolated installed-package proof."""
import contextlib
import io
import json
import unittest
import zipfile

from define_project_fixture import (
    DefineProjectFixture,
    ROOT,
    SKILLS,
    SKILL,
    module,
    asset,
    decision,
    batch,
    answers,
    project,
    installer,
)


class DefineProjectCliTests(DefineProjectFixture):
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

    def test_cli_rejects_duplicate_json_keys_and_nonfinite_numbers_without_traceback(self):
        for raw in ('{"schema_version":1,"schema_version":1}', '{"schema_version":NaN}'):
            path = self.work / "bad.json"
            path.write_text(raw, encoding="utf-8")
            result = self.cli("validate-input", path)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Error:", result.stderr)
            self.assertNotIn("Traceback", result.stderr)



if __name__ == "__main__":
    unittest.main()
