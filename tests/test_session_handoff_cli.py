"""Standalone installed CLI proof, preservation and malformed-artifact controls."""
import contextlib
import io
import json
import os
import unittest

from session_handoff_fixture import HandoffFixture, ROOT, NAME, SKILL, installer


class HandoffCliTests(HandoffFixture):
    def test_all_agent_installs_work_outside_the_checkout(self):
        home = self.base / 'agent home'
        with contextlib.redirect_stdout(io.StringIO()):
            installer.install(ROOT, home, list(installer.TARGETS), [NAME], False)
        self.save()
        other = self.base / 'different cwd'
        other.mkdir()
        for agent, target in installer.TARGETS.items():
            script = home / target / NAME / 'scripts/handoff.py'
            prompt = self.base / f'{agent}-next-session.txt'
            for args in (('validate-input', self.base / 'input.json'),
                         ('hash-input', self.base / 'input.json'),
                         ('validate-output', self.base / 'input.json', self.base / 'output.json'),
                         ('render', self.base / 'input.json', self.base / 'output.json', '--prompt', prompt)):
                result = self.cli(*args, script=script, cwd=other)
                self.assertEqual(result.returncode, 0, result.stderr)
                if args[0] == 'hash-input':
                    self.assertEqual(result.stdout.strip(), self.output['input_sha256'])
            self.assertIn(self.output['objective'], prompt.read_text(encoding='utf-8'))
            self.assertFalse((script.parent / '__pycache__').exists())

    def test_render_is_idempotent_and_preserves_different_existing_output(self):
        self.save()
        prompt = self.base / 'next-session.txt'
        args = ('render', self.base / 'input.json', self.base / 'output.json', '--prompt', prompt)
        self.assertEqual(self.cli(*args).returncode, 0)
        before = (prompt.read_bytes(), prompt.stat().st_mtime_ns)
        result = self.cli(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('unchanged:', result.stdout)
        self.assertEqual((prompt.read_bytes(), prompt.stat().st_mtime_ns), before)
        prompt.write_text('Keep my local notes.', encoding='utf-8')
        result = self.cli(*args)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(prompt.read_text(), 'Keep my local notes.')

    def test_invalid_or_stale_output_never_creates_a_prompt(self):
        self.intake['request'] += ' A changed scope.'
        self.save()
        prompt = self.base / 'must-not-exist.txt'
        result = self.cli('render', self.base / 'input.json', self.base / 'output.json', '--prompt', prompt)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(prompt.exists())

    def test_runtime_artifacts_cannot_be_written_inside_inspected_workspace(self):
        workspace = self.base / 'workspace'
        workspace.mkdir()
        self.intake['scope']['workspace'] = str(workspace)
        self.bind()
        self.save()
        prompt = workspace / 'new-context.txt'
        result = self.cli('render', self.base / 'input.json', self.base / 'output.json', '--prompt', prompt)
        self.assertEqual(result.returncode, 1)
        self.assertIn('outside the inspected workspace', result.stderr)
        self.assertEqual(list(workspace.iterdir()), [])

    def test_render_cannot_write_inside_installed_skill(self):
        self.save()
        prompt = SKILL / 'assets/forbidden-prompt.txt'
        self.assertFalse(prompt.exists())
        result = self.cli('render', self.base / 'input.json', self.base / 'output.json', '--prompt', prompt)
        self.assertEqual(result.returncode, 1)
        self.assertIn('outside the installed skill', result.stderr)
        self.assertFalse(prompt.exists())

    def test_malformed_json_and_credentials_fail_without_raw_excerpts(self):
        for raw in ('{"schema_version":1,"schema_version":1}', '{"schema_version":NaN}',
                    '{"bad":"unterminated', json.dumps({'request':'gh' + 'p_' + 'notavalidcredential0123456789ABCDEFG'})):
            path = self.base / 'malformed.json'
            path.write_text(raw, encoding='utf-8')
            result = self.cli('validate-input', path)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn('Traceback', result.stderr)
            self.assertNotIn('notavalidcredential', result.stderr)
            self.assertNotIn(raw, result.stderr)

    @unittest.skipIf(os.name == 'nt', 'Windows symlink creation requires optional privileges')
    def test_linked_sources_and_outputs_are_not_followed(self):
        source = self.base / 'linked-source.md'
        source.symlink_to(self.base / 'example-source.md')
        self.intake['sources'][0]['reference']['path'] = source.name
        self.save()
        result = self.cli('validate-input', self.base / 'input.json')
        self.assertEqual(result.returncode, 1)
        source.unlink()
        self.intake['sources'][0]['reference']['path'] = 'example-source.md'
        self.bind()
        self.save()
        prompt = self.base / 'linked-output.txt'
        prompt.symlink_to(self.base / 'missing.txt')
        result = self.cli('render', self.base / 'input.json', self.base / 'output.json', '--prompt', prompt)
        self.assertEqual(result.returncode, 1)
        self.assertTrue(prompt.is_symlink())
        self.assertFalse((self.base / 'missing.txt').exists())
        prompt.unlink()
        prompt.symlink_to(prompt.name)
        result = self.cli('render', self.base / 'input.json', self.base / 'output.json', '--prompt', prompt)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn('Traceback', result.stderr)
        self.assertTrue(prompt.is_symlink())
