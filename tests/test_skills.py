import contextlib
import hashlib
import importlib.util
import io
import json
import os
import tempfile
import subprocess
from types import SimpleNamespace
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "skills.py"
SPEC = importlib.util.spec_from_file_location("skills", SCRIPT)
skills = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(skills)


class SkillTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "repo"
        self.home = Path(self.temporary.name) / "home"
        self.source = self.add_skill("example")

    def add_skill(self, name):
        folder = self.root / "skills" / name
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text(
            f'---\nname: {name}\ndescription: "A meaningful task"\n---\n# Instructions\n',
            encoding="utf-8",
        )
        (folder / "assets").mkdir()
        (folder / "assets" / "context.txt").write_text("Useful context", encoding="utf-8")
        return folder

    def install(self, agents=None, names=None, dry_run=False):
        with contextlib.redirect_stdout(io.StringIO()):
            skills.install(self.root, self.home, agents or list(skills.TARGETS), names or [], dry_run)

    def destination(self, agent="codex", name="example"):
        return self.home / skills.TARGETS[agent] / name

    def test_install_all_complete_copies_and_idempotence(self):
        self.install()
        for agent in skills.TARGETS:
            destination = self.destination(agent)
            self.assertEqual(skills.snapshot(destination), skills.snapshot(self.source))
            self.assertFalse(destination.is_symlink())
            receipt = destination.parent / skills.STATE_FILE
            before = (receipt.stat().st_mtime_ns, (destination / "SKILL.md").stat().st_mtime_ns)
            self.install([agent])
            self.assertEqual(before, (receipt.stat().st_mtime_ns, (destination / "SKILL.md").stat().st_mtime_ns))

    def test_clean_managed_copy_updates_and_unrelated_skill_survives(self):
        self.install()
        unrelated = self.destination(name="my-own-skill")
        unrelated.mkdir()
        (unrelated / "private.txt").write_text("preserve me", encoding="utf-8")
        (self.source / "assets" / "context.txt").write_text("new upstream context", encoding="utf-8")
        self.install()
        self.assertEqual(skills.snapshot(self.destination()), skills.snapshot(self.source))
        self.assertEqual((unrelated / "private.txt").read_text(), "preserve me")

    def test_local_edit_blocks_every_target_before_updates(self):
        self.install()
        original = skills.snapshot(self.destination())
        edited = self.destination("claude") / "SKILL.md"
        edited.write_text("My edited instructions", encoding="utf-8")
        (self.source / "SKILL.md").write_text(
            (self.source / "SKILL.md").read_text() + "Upstream changed\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "locally edited"):
            self.install()
        self.assertEqual(skills.snapshot(self.destination()), original)
        self.assertEqual(edited.read_text(), "My edited instructions")

    def test_added_and_deleted_local_files_block(self):
        self.install(["codex"])
        added = self.destination() / "notes.txt"
        added.write_text("local notes", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "locally edited"):
            self.install(["codex"])
        added.unlink()
        (self.destination() / "assets" / "context.txt").unlink()
        with self.assertRaisesRegex(ValueError, "locally edited"):
            self.install(["codex"])

    def test_added_empty_directory_is_preserved(self):
        self.install(["codex"])
        notes = self.destination() / "notes"
        notes.mkdir()
        with self.assertRaisesRegex(ValueError, "locally edited"):
            self.install(["codex"])
        self.assertTrue(notes.is_dir())

    @unittest.skipIf(os.name == "nt", "Windows does not retain Unix executable bits")
    def test_local_executable_flag_change_blocks_update(self):
        self.install(["codex"])
        installed = self.destination() / "assets" / "context.txt"
        installed.chmod(0o755)
        with self.assertRaisesRegex(ValueError, "locally edited"):
            self.install(["codex"])
        self.assertTrue(installed.stat().st_mode & 0o111)

    def test_unmanaged_directory_blocks_without_creating_other_targets(self):
        occupied = self.destination("claude")
        occupied.mkdir(parents=True)
        (occupied / "mine.txt").write_text("mine", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unmanaged conflict"):
            self.install()
        self.assertFalse(self.destination().parent.exists())
        self.assertEqual((occupied / "mine.txt").read_text(), "mine")

    def test_file_conflict_is_preserved(self):
        destination = self.destination()
        destination.parent.mkdir(parents=True)
        destination.write_text("not a skill", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unmanaged conflict"):
            self.install(["codex"])
        self.assertEqual(destination.read_text(), "not a skill")

    def test_dry_run_has_no_filesystem_side_effects(self):
        self.install(dry_run=True)
        self.assertFalse(self.home.exists())

    def test_selected_install_and_removed_catalog_entry_is_not_pruned(self):
        self.add_skill("another")
        self.install(["codex"], ["example"])
        self.assertFalse(self.destination(name="another").exists())
        self.source.rename(self.root / "retired-source")
        self.install(["codex"])
        self.assertTrue(self.destination().exists())
        self.assertTrue(self.destination(name="another").exists())

    def test_unknown_skill_does_not_write(self):
        with self.assertRaisesRegex(ValueError, "Select distinct"):
            self.install(names=["../private"])
        self.assertFalse(self.home.exists())

    def test_corrupt_ownership_manifest_is_preserved(self):
        base = self.destination().parent
        base.mkdir(parents=True)
        receipt = base / skills.STATE_FILE
        receipt.write_text('{"owner":"other","skills":{}}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid ownership"):
            self.install(["codex"])
        self.assertFalse(self.destination().exists())
        self.assertEqual(json.loads(receipt.read_text())["owner"], "other")

    def test_receipt_failure_restores_previous_copy(self):
        self.install(["codex"])
        original = skills.snapshot(self.destination())
        before = (self.destination().parent / skills.STATE_FILE).read_bytes()
        (self.source / "assets" / "context.txt").write_text("new context", encoding="utf-8")
        with patch.object(Path, "replace", side_effect=OSError("disk failure")):
            with self.assertRaisesRegex(OSError, "disk failure"):
                self.install(["codex"])
        self.assertEqual(skills.snapshot(self.destination()), original)
        self.assertEqual((self.destination().parent / skills.STATE_FILE).read_bytes(), before)

    def test_build_is_reproducible_complete_and_checksummed(self):
        output = Path(self.temporary.name) / "dist"
        with contextlib.redirect_stdout(io.StringIO()):
            skills.build(self.root, output)
        archive = output / "example.zip"
        original = archive.read_bytes()
        entry = json.loads((output / "catalog.json").read_text())["skills"][0]
        self.assertEqual(entry["sha256"], hashlib.sha256(original).hexdigest())
        with zipfile.ZipFile(archive) as bundle:
            self.assertEqual(set(bundle.namelist()), {"example/SKILL.md", "example/assets/context.txt"})
            self.assertEqual(bundle.read("example/assets/context.txt"), b"Useful context")
        with contextlib.redirect_stdout(io.StringIO()):
            skills.build(self.root, output)
        self.assertEqual(original, archive.read_bytes())

    def test_private_hidden_file_blocks_packaging(self):
        (self.source / ".env").write_text("private", encoding="utf-8")
        output = Path(self.temporary.name) / "dist"
        with self.assertRaisesRegex(ValueError, "hidden/generated"):
            skills.build(self.root, output)
        self.assertFalse(output.exists())

    def test_invalid_names_and_frontmatter_fail(self):
        for name in ("../private", "-bad", "double--dash", "con", "synced"):
            self.assertFalse(skills.valid_name(name))
        (self.source / "SKILL.md").write_text(
            '---\nname: different\ndescription: "Useful"\n---\nInstructions\n', encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "name must match"):
            skills.catalog(self.root)

    def test_windows_reparse_points_are_treated_as_links(self):
        with patch.object(Path, "lstat", return_value=SimpleNamespace(st_file_attributes=0x400)):
            self.assertTrue(skills.is_link(self.source))

    @unittest.skipUnless(os.name == "nt", "Windows junction integration check")
    def test_windows_junction_cannot_publish_external_content(self):
        private = Path(self.temporary.name) / "private-directory"
        private.mkdir()
        (private / "secret.txt").write_text("private", encoding="utf-8")
        junction = self.source / "assets" / "linked-directory"
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(junction), str(private)],
            text=True, capture_output=True,
        )
        if result.returncode:
            self.skipTest("Windows junction creation unavailable: " + result.stderr)
        with self.assertRaisesRegex(ValueError, "junctions"):
            skills.catalog(self.root)

    @unittest.skipIf(os.name == "nt", "Windows symlink creation requires optional privileges")
    def test_source_link_cannot_publish_external_content(self):
        private = Path(self.temporary.name) / "secret"
        private.write_text("private", encoding="utf-8")
        (self.source / "assets" / "leak.txt").symlink_to(private)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            skills.catalog(self.root)

    @unittest.skipIf(os.name == "nt", "Windows symlink creation requires optional privileges")
    def test_broken_destination_link_is_preserved(self):
        destination = self.destination()
        destination.parent.mkdir(parents=True)
        destination.symlink_to(Path(self.temporary.name) / "missing")
        with self.assertRaisesRegex(ValueError, "unmanaged conflict"):
            self.install(["codex"])
        self.assertTrue(destination.is_symlink())


if __name__ == "__main__":
    unittest.main()
