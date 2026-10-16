"""Source-size and preflight regressions, including source-only new files."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from assembled_catalog import installer
from skill_tools.limits import check_code_length, repository_violations


class CodeSizeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def write(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root)

    def test_physical_limit_counts_comments_blanks_and_partial_final_line(self):
        for ending in (b'\n', b'\r\n'):
            with self.subTest(ending=ending):
                check_code_length((b'# comment' + ending) * 299 + b'last', 'helper.py')
                with self.assertRaisesRegex(ValueError, '301 lines exceeds 300'):
                    check_code_length(ending * 300 + b'last', 'helper.py')

    def test_repository_includes_tracked_and_new_source_but_not_ignored_builds(self):
        self.git('init', '-q')
        self.write('.gitignore', b'dist/\n')
        self.write('tracked.py', b'pass\n')
        self.git('add', '.gitignore', 'tracked.py')
        self.write('tracked.py', b'# comment\n' * 301)
        self.write('new.cjs', b'// comment\n' * 301)
        self.write('dist/output.py', b'# generated\n' * 500)
        before = self.git('status', '--porcelain')
        violations = repository_violations(self.root)
        self.assertEqual(len(violations), 2, violations)
        self.assertTrue(any('tracked.py: 301' in item for item in violations))
        self.assertTrue(any('new.cjs: 301' in item for item in violations))
        self.assertEqual(self.git('status', '--porcelain'), before)

    def test_generated_html_exemption_does_not_exempt_maintained_templates(self):
        self.git('init', '-q')
        for name in ('examples/dynamic-umls/sequence.html',
                     'skills/ct-dynamic-uml/assets/template.html',
                     'examples/dynamic-umls/new-source.html'):
            self.write(name, b'<p>line</p>\n' * 301)
        violations = repository_violations(self.root)
        self.assertEqual(len(violations), 2, violations)
        self.assertTrue(any('template.html' in item for item in violations))
        self.assertTrue(any('new-source.html' in item for item in violations))

    def test_non_ascii_source_filename_is_not_skipped(self):
        self.git('init', '-q')
        self.write('café.py', b'# synthetic\n' * 301)
        violations = repository_violations(self.root)
        self.assertEqual(len(violations), 1, violations)
        self.assertIn('café.py: 301 lines', violations[0])

    def test_configuration_and_prose_are_not_coding_files(self):
        for name in ('contract.json', 'SKILL.md', 'openai.yaml'):
            check_code_length(b'\n' * 301, name)
        for name in ('Makefile', 'helper.py', 'controls.js', 'styles.css', 'view.html'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                check_code_length(b'\n' * 301, name)

    def test_oversized_packaged_code_rejected_before_any_output(self):
        self.write('skills/example/SKILL.md',
                   b'---\nname: example\ndescription: "Synthetic size check"\n---\nUse the helper.\n')
        manifest = self.write('skills/example/assets/package.json', b'{}')
        for shared in (False, True):
            with self.subTest(shared=shared):
                helper = 'shared/runtime/helper.py' if shared else 'skills/example/scripts/helper.py'
                path = self.write(helper, b'# synthetic\n' * 301)
                config = {'schema_version': 1,
                          'scripts': {'helper.py': 'runtime/helper.py'} if shared else {}}
                manifest.write_text(json.dumps(config), encoding='utf-8')
                output = self.root / 'output'
                home = self.root / 'home'
                with contextlib.redirect_stdout(io.StringIO()):
                    actions = (
                        lambda: installer.build(self.root, output),
                        lambda: installer.assemble(self.root, output, []),
                        lambda: installer.install(self.root, home, ['codex'], [], False),
                    )
                    for action in actions:
                        with self.assertRaisesRegex(ValueError, '301 lines exceeds 300'):
                            action()
                        self.assertFalse(output.exists())
                        self.assertFalse(home.exists())
                path.unlink()


if __name__ == '__main__':
    unittest.main()
