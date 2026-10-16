"""Composition, upgrade compatibility and malicious-manifest controls."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from assembled_catalog import installer


class PackageAssemblyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / 'source'
        self.home = self.base / 'home'
        self.skill = self.root / 'skills/example'
        (self.skill / 'assets').mkdir(parents=True)
        (self.skill / 'SKILL.md').write_text('---\nname: example\ndescription: "Synthetic packaging task"\n---\nUse scripts/helper.py.\n')
        self.helper = self.root / 'shared/runtime/helper.py'
        self.helper.parent.mkdir(parents=True)
        self.helper.write_text('print("standalone helper")\n')
        self.entry = {'source': 'shared/runtime/helper.py', 'destination': 'scripts/helper.py'}
        self.manifest([self.entry])

    def manifest(self, scripts):
        (self.skill / 'assets/package.json').write_text(json.dumps({'schema_version': 2, 'scripts': scripts}))

    def install(self, agents=None):
        with contextlib.redirect_stdout(io.StringIO()):
            installer.install(self.root, self.home, agents or list(installer.TARGETS), [], False)

    def reject_before_output(self):
        output = self.base / 'dist'
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises((ValueError, OSError)):
                installer.install(self.root, self.home, list(installer.TARGETS), [], False)
            with self.assertRaises((ValueError, OSError)):
                installer.build(self.root, output)
            with self.assertRaises((ValueError, OSError)):
                installer.assemble(self.root, output, [])
        self.assertFalse(self.home.exists())
        self.assertFalse(output.exists())

    def test_same_payload_for_assembly_all_installers_and_zip(self):
        assembled = self.base / 'assembled'
        with contextlib.redirect_stdout(io.StringIO()):
            installer.assemble(self.root, assembled, [])
            self.install()
            installer.build(self.root, self.base / 'dist')
        expected = installer.snapshot(assembled / 'example')
        self.assertNotIn('assets/package.json', expected)
        self.assertNotIn('assets/', expected)  # Manifest-only folder is source metadata.
        for destination in installer.TARGETS.values():
            folder = self.home / destination / 'example'
            self.assertEqual(installer.snapshot(folder), expected)
            receipt = json.loads((folder.parent / installer.STATE_FILE).read_text())
            self.assertEqual(receipt['skills']['example'], expected)
            result = subprocess.run([sys.executable, str(folder / 'scripts/helper.py')], capture_output=True, text=True, cwd=self.base)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), 'standalone helper')
        with zipfile.ZipFile(self.base / 'dist/example.zip') as bundle:
            for name, value in installer.package_payload(self.root, self.skill).items():
                if value is not None:
                    self.assertEqual(bundle.read('example/' + name), value[0])
            self.assertNotIn('example/assets/package.json', bundle.namelist())
        before = (self.base / 'dist/example.zip').read_bytes()
        with contextlib.redirect_stdout(io.StringIO()):
            installer.build(self.root, self.base / 'dist')
        self.assertEqual((self.base / 'dist/example.zip').read_bytes(), before)
        catalog = json.loads((self.base / 'dist/catalog.json').read_text())
        self.assertEqual(catalog['skills'][0]['sha256'], hashlib.sha256(before).hexdigest())

    def test_unmodified_v1_receipt_remains_valid_and_shared_updates_propagate(self):
        # Simulate the old complete-folder source layout and existing v1 receipt.
        legacy = self.base / 'legacy/skills/example'
        (legacy / 'scripts').mkdir(parents=True)
        (legacy / 'SKILL.md').write_bytes((self.skill / 'SKILL.md').read_bytes())
        (legacy / 'scripts/helper.py').write_bytes(self.helper.read_bytes())
        with contextlib.redirect_stdout(io.StringIO()):
            installer.install(self.base / 'legacy', self.home, list(installer.TARGETS), [], False)
        receipts = {agent: (self.home / path / installer.STATE_FILE).read_bytes() for agent, path in installer.TARGETS.items()}
        self.install()
        for agent, destination in installer.TARGETS.items():
            self.assertEqual((self.home / destination / installer.STATE_FILE).read_bytes(), receipts[agent])
        self.helper.write_text('print("new shared revision")\n')
        self.install()
        for destination in installer.TARGETS.values():
            self.assertEqual((self.home / destination / 'example/scripts/helper.py').read_bytes(), self.helper.read_bytes())

    def test_shared_installed_edit_blocks_all_targets(self):
        self.install()
        edited = self.home / installer.TARGETS['claude'] / 'example/scripts/helper.py'
        edited.write_text('my changes\n')
        before = installer.snapshot(self.home / installer.TARGETS['codex'] / 'example')
        self.helper.write_text('print("upstream")\n')
        with self.assertRaisesRegex(ValueError, 'locally edited'):
            self.install()
        self.assertEqual(installer.snapshot(self.home / installer.TARGETS['codex'] / 'example'), before)
        self.assertEqual(edited.read_text(), 'my changes\n')

    def test_assembly_never_imports_or_executes_scripts(self):
        marker = self.base / 'should-not-exist'
        self.helper.write_text('from pathlib import Path\nPath(' + repr(str(marker)) + ').touch()\nraise RuntimeError("not safe to execute")\n')
        self.install()
        with contextlib.redirect_stdout(io.StringIO()):
            installer.build(self.root, self.base / 'dist')
            installer.assemble(self.root, self.base / 'assembled', [])
        self.assertFalse(marker.exists())

    def test_dry_run_never_writes(self):
        with contextlib.redirect_stdout(io.StringIO()):
            installer.install(self.root, self.home, list(installer.TARGETS), [], True)
        self.assertFalse(self.home.exists())

    def test_invalid_manifests_and_paths_fail_before_any_mutation(self):
        cases = [
            {'schema_version': True, 'scripts': []}, {'schema_version': 1, 'scripts': []},
            {'schema_version': 3, 'scripts': []}, {'schema_version': 2, 'scripts': {}},
            {'schema_version': 1, 'scripts': {'helper.py': 'runtime/helper.py'}},
            {'schema_version': 2, 'scripts': [], 'run': 'bad'},
        ]
        for entry in (None, [], 'helper.py', {}, {'source': self.entry['source']},
                      {'destination': self.entry['destination']}, {**self.entry, 'run': 'bad'}):
            cases.append({'schema_version': 2, 'scripts': [entry]})
        for source in [None, False, [], '../private.py', '/tmp/private.py', 'C:/private.py',
                       'runtime/helper.py', 'shared/runtime/../private.py', 'shared/runtime\\private.py',
                       '//server/private.py', 'shared/.hidden/helper.py', 'shared/runtime/.secret.py',
                       'shared/runtime/missing.py', 'shared/runtime/helper.py/extra',
                       'shared/runtime//helper.py', 'shared/runtime/Helper.py']:
            cases.append({'schema_version': 2, 'scripts': [{**self.entry, 'source': source}]})
        for destination in [None, False, [], 'helper.py', '../escape.py', '/scripts/helper.py',
                            'C:/scripts/helper.py', 'scripts\\helper.py', 'scripts/../helper.py',
                            'scripts/con.py', 'scripts/Helper.py', 'scripts/helper.py/extra',
                            'scripts/.secret.py', 'assets/helper.py', 'scripts//helper.py']:
            cases.append({'schema_version': 2, 'scripts': [{**self.entry, 'destination': destination}]})
        for config in cases:
            with self.subTest(config=config):
                (self.skill / 'assets/package.json').write_text(json.dumps(config))
                self.reject_before_output()
        (self.skill / 'assets/package.json').write_text(
            '{"schema_version":2,"scripts":[{"source":"shared/runtime/helper.py",'
            '"destination":"scripts/helper.py","destination":"scripts/other.py"}]}')
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON property'):
            installer.catalog(self.root)
        self.reject_before_output()

    def test_duplicate_destinations_are_rejected_before_any_output(self):
        self.manifest([self.entry, self.entry])
        with self.assertRaisesRegex(ValueError, 'destination collision'):
            installer.catalog(self.root)
        self.reject_before_output()

    def test_same_source_can_have_distinct_explicit_destinations(self):
        self.manifest([self.entry, {**self.entry, 'destination': 'scripts/alias.py'}])
        self.install()
        for destination in installer.TARGETS.values():
            folder = self.home / destination / 'example/scripts'
            self.assertEqual((folder / 'alias.py').read_bytes(), self.helper.read_bytes())
            self.assertEqual((folder / 'helper.py').read_bytes(), self.helper.read_bytes())

    def test_empty_scripts_list_installs_only_skill_local_files(self):
        self.manifest([])
        self.install()
        for destination in installer.TARGETS.values():
            self.assertEqual(set(installer.snapshot(self.home / destination / 'example')), {'SKILL.md'})

    def test_missing_source_manifest_is_rejected(self):
        (self.skill / 'assets/package.json').unlink()
        self.reject_before_output()

    def test_local_file_or_directory_cannot_shadow_shared_destination(self):
        path = self.skill / 'scripts/helper.py'
        path.parent.mkdir()
        path.write_text('local copy\n')
        self.reject_before_output()
        path.unlink(); path.mkdir()
        self.reject_before_output()

    def test_case_collisions_are_rejected(self):
        path = self.skill / 'scripts'
        path.mkdir(); (path / 'Helper.py').write_text('other\n')
        self.reject_before_output()

    @unittest.skipIf(os.name == 'nt', 'Windows symlinks require optional privileges')
    def test_links_in_shared_source_or_ancestors_are_rejected(self):
        private = self.base / 'private.py'; private.write_text('private\n')
        self.helper.unlink(); self.helper.symlink_to(private)
        self.reject_before_output()
        self.helper.unlink(); self.helper.parent.rmdir()
        self.helper.parent.symlink_to(self.base, target_is_directory=True)
        self.reject_before_output()
        self.helper.parent.unlink(); self.helper.parent.parent.rmdir()
        (self.root / 'shared').symlink_to(self.base, target_is_directory=True)
        self.reject_before_output()

    def test_detected_credentials_in_shared_script_are_redacted_and_blocked(self):
        credential = 'gh' + 'p_' + 'A1b2C3d4E5f6G7h8I9j0' * 2
        self.helper.write_text('value = ' + repr(credential) + '\n')
        with self.assertRaisesRegex(ValueError, 'redacted') as error:
            installer.catalog(self.root)
        self.assertNotIn(credential, str(error.exception))
        self.reject_before_output()

    def test_shared_change_during_staging_does_not_replace_installation(self):
        self.install(['codex'])
        folder = self.home / installer.TARGETS['codex'] / 'example'
        before = installer.snapshot(folder)
        self.helper.write_text('print("candidate")\n')
        original = installer.write_package
        def mutate(*args):
            original(*args)
            self.helper.write_text('print("changed during staging")\n')
        with patch.object(installer.installation, 'write_package', side_effect=mutate):
            with self.assertRaisesRegex(ValueError, 'source changed'):
                self.install(['codex'])
        self.assertEqual(installer.snapshot(folder), before)

    def test_receipt_failure_rolls_back_shared_upgrade(self):
        self.install(['codex'])
        folder = self.home / installer.TARGETS['codex'] / 'example'
        before = installer.snapshot(folder)
        self.helper.write_text('print("candidate")\n')
        with patch.object(Path, 'replace', side_effect=OSError('synthetic disk failure')):
            with self.assertRaisesRegex(OSError, 'disk failure'):
                self.install(['codex'])
        self.assertEqual(installer.snapshot(folder), before)

    def test_exclusive_assembly_preserves_existing_output(self):
        output = self.base / 'assembled'; output.mkdir()
        (output / 'keep.txt').write_text('user content\n')
        with self.assertRaisesRegex(ValueError, 'must not exist'):
            installer.assemble(self.root, output, [])
        self.assertEqual((output / 'keep.txt').read_text(), 'user content\n')

    def test_assembly_refuses_source_directory_as_output(self):
        with self.assertRaisesRegex(ValueError, 'inside source'):
            installer.assemble(self.root, self.root / 'shared/new-output', [])
        self.assertFalse((self.root / 'shared/new-output').exists())


if __name__ == '__main__':
    unittest.main()
