"""Shared Markdown stays canonical, isolated and protected by installer ownership."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from assembled_catalog import installer

ROOT = Path(__file__).resolve().parents[1]


class SharedReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / 'source'
        self.home = self.base / 'home'
        self.skill = self.root / 'skills/example'
        (self.skill / 'assets').mkdir(parents=True)
        (self.skill / 'SKILL.md').write_text('---\nname: example\ndescription: "Synthetic task"\n---\n# Example\n')
        self.reference = self.root / 'shared/instructions/common.md'
        self.reference.parent.mkdir(parents=True)
        self.reference.write_text('# Shared guide\nA single canonical reference.\n')
        self.reference.chmod(0o755)
        self.entry = {'source': 'shared/instructions/common.md', 'destination': 'references/common.md'}
        self.manifest([self.entry])

    def manifest(self, entries):
        (self.skill / 'assets/package.json').write_text(json.dumps(
            {'schema_version': 2, 'scripts': [], 'references': entries}))

    def install(self):
        with contextlib.redirect_stdout(io.StringIO()):
            installer.install(self.root, self.home, list(installer.TARGETS), [], False)

    def test_same_reference_bytes_in_assembly_and_each_agent_without_executable_mode(self):
        assembled = self.base / 'assembled'
        with contextlib.redirect_stdout(io.StringIO()):
            installer.assemble(self.root, assembled, [])
        self.install()
        expected = installer.snapshot(assembled / 'example')
        self.assertTrue(expected['references/common.md'].startswith('0:'))
        for destination in installer.TARGETS.values():
            folder = self.home / destination / 'example'
            self.assertEqual(installer.snapshot(folder), expected)
            self.assertEqual((folder / 'references/common.md').read_bytes(), self.reference.read_bytes())

    def test_canonical_update_propagates_and_local_reference_edits_are_preserved(self):
        self.install()
        self.reference.write_text('# Revised guide\nUpdated canonical behavior.\n')
        self.install()
        for destination in installer.TARGETS.values():
            path = self.home / destination / 'example/references/common.md'
            self.assertEqual(path.read_bytes(), self.reference.read_bytes())
        edited = self.home / installer.TARGETS['claude'] / 'example/references/common.md'
        edited.write_text('User edits\n')
        before = {agent: installer.snapshot(self.home / target / 'example')
                  for agent, target in installer.TARGETS.items()}
        self.reference.write_text('Another upstream change\n')
        with self.assertRaisesRegex(ValueError, 'locally edited'):
            self.install()
        for agent, destination in installer.TARGETS.items():
            self.assertEqual(installer.snapshot(self.home / destination / 'example'), before[agent])

    def test_invalid_reference_selection_fails_before_creating_any_output(self):
        cases = [None, {}, [None], [{'source': self.entry['source']}], [self.entry, self.entry]]
        for source in ('../escape.md', '/private.md', 'shared/instructions/../common.md',
                       'shared/instructions/common.py', 'shared/.hidden/common.md',
                       'shared/instructions/missing.md', 'shared/instructions/Common.md'):
            cases.append([{**self.entry, 'source': source}])
        for target in ('../escape.md', 'references/../common.md', 'scripts/common.md',
                       'references/common.py', 'references/nested/common.md', 'references/Common.md'):
            cases.append([{**self.entry, 'destination': target}])
        for entries in cases:
            with self.subTest(entries=entries):
                self.manifest(entries)
                with self.assertRaises(ValueError):
                    installer.assemble(self.root, self.base / 'output', [])
                self.assertFalse((self.base / 'output').exists())
                self.assertFalse(self.home.exists())

    def test_local_reference_collision_is_rejected(self):
        (self.skill / 'references').mkdir()
        (self.skill / 'references/common.md').write_text('Skill-local ownership\n')
        with self.assertRaisesRegex(ValueError, 'destination collision'):
            installer.catalog(self.root)

    def test_every_catalog_skill_delivers_the_same_optional_entry_and_focused_guide(self):
        for name, folder in installer.catalog(ROOT).items():
            with self.subTest(skill=name):
                payload = installer.package_payload(ROOT, folder)
                self.assertIn('references/optional-addons.md',
                              (folder / 'SKILL.md').read_text(encoding='utf-8'))
                for filename in ('optional-addons.md', 'project-context.md'):
                    content, executable = payload['references/' + filename]
                    self.assertEqual(content, (ROOT / 'shared/instructions' / filename).read_bytes())
                    self.assertFalse(executable)
                for filename in ('project_context.py', 'project_context_discovery.py', 'public_content.py'):
                    self.assertIn('scripts/' + filename, payload)


if __name__ == '__main__':
    unittest.main()
