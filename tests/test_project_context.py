"""Project profiles preserve provider choices without executing or publishing them."""
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

from assembled_catalog import installer

ROOT = Path(__file__).resolve().parents[1]
NAME = 'ct-product-configure-project'


class ProjectContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.base = Path(cls.temporary.name)
        cls.assembled = cls.base / 'assembled'
        with contextlib.redirect_stdout(io.StringIO()):
            installer.assemble(ROOT, cls.assembled, [NAME])
        cls.script = cls.assembled / NAME / 'scripts/project_context.py'
        sys.path.insert(0, str(cls.script.parent))
        try:
            spec = importlib.util.spec_from_file_location('ct_project_context_test', cls.script)
            cls.helper = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.helper)
        finally:
            sys.path.pop(0)
        cls.example = json.loads((cls.assembled / NAME / 'assets/example-project.json').read_text())

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.profile = copy.deepcopy(self.example)

    def test_different_providers_and_multiple_docs_are_preserved(self):
        self.profile['documentation'].append({'provider': 'notion', 'location': 'https://example.com/spec',
                                              'purpose': 'Product notes', 'primary': False})
        before = copy.deepcopy(self.profile)
        self.assertEqual(self.helper.validate(self.profile), [])
        self.assertEqual(self.profile, before)
        self.assertEqual(self.profile['source_control']['provider'], 'github')
        self.assertEqual(self.profile['work_tracking'][0]['provider'], 'jira')

    def test_explicit_none_and_undecided_do_not_invent_services(self):
        self.profile['source_control'] = {'provider': 'none', 'location': None}
        self.profile['work_tracking'] = [{'provider': 'undecided', 'location': None,
                                         'purpose': 'User deferred tracker selection', 'primary': True}]
        self.assertEqual(self.helper.validate(self.profile), ['work_tracking'])
        self.profile['source_control']['location'] = 'example/repo'
        with self.assertRaisesRegex(ValueError, 'cannot declare a location'):
            self.helper.validate(self.profile)

    def test_duplicate_and_conflicting_canonical_locations_fail(self):
        self.profile['documentation'].append(copy.deepcopy(self.profile['documentation'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.helper.validate(self.profile)
        self.profile = copy.deepcopy(self.example)
        self.profile['documentation'][1]['primary'] = True
        with self.assertRaisesRegex(ValueError, 'exactly one primary'):
            self.helper.validate(self.profile)

    def test_schema_rejects_wrong_types_missing_and_unknown_fields(self):
        for mutate in (lambda p: p.update(schema_version=True),
                       lambda p: p.pop('documentation'),
                       lambda p: p.update(unrecognized='value'),
                       lambda p: p['work_tracking'][0].update(primary='yes'),
                       lambda p: p['source_control'].update(provider='GitHub')):
            profile = copy.deepcopy(self.example)
            mutate(profile)
            with self.subTest(profile=profile), self.assertRaises(ValueError):
                self.helper.validate(profile)

    def test_secret_values_and_access_bearing_links_are_rejected_without_echo(self):
        candidates = ['https://example.com/?access_token=private-value',
                      'https://user:private-value@example.com/docs',
                      'https://example.com/#token=private-value',
                      'gh' + 'p_' + 'AbCd0123456789' * 4]
        for index, value in enumerate(candidates):
            self.profile['documentation'][0]['location'] = value
            with self.subTest(case=index), self.assertRaises(ValueError) as caught:
                self.helper.validate(self.profile)
            self.assertNotIn('private-value', str(caught.exception))
            self.assertNotIn(value, str(caught.exception))

    def test_malformed_unicode_url_never_leaks_its_netloc_in_cli_errors(self):
        value = 'https://private-account\uff0fexample.com/docs'
        self.profile['documentation'][0]['location'] = value
        path = self.base / 'malformed-url.json'
        path.write_text(json.dumps(self.profile))
        result = subprocess.run([sys.executable, str(self.script), 'validate', str(path)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('Malformed reference URL', result.stderr)
        self.assertNotIn('private-account', result.stderr)
        self.assertEqual(result.stdout, '')

    def test_validate_never_executes_declared_commands(self):
        sentinel = self.base / 'must-not-exist'
        self.profile['validation']['checks'] = [f'touch {sentinel}']
        self.helper.validate(self.profile)
        self.assertFalse(sentinel.exists())

    def test_json_loader_rejects_duplicates_nonfinite_and_oversize_files(self):
        path = self.base / 'invalid.json'
        for content in ('{"schema_version":1,"schema_version":2}', '{"value":NaN}',
                        ' ' * (self.helper.MAX_BYTES + 1)):
            path.write_text(content)
            with self.assertRaises(ValueError):
                self.helper.load(path)

    def test_installed_cli_for_all_agents_renders_without_writing_a_profile(self):
        home = self.base / 'home'
        with contextlib.redirect_stdout(io.StringIO()):
            installer.install(ROOT, home, list(installer.TARGETS), [NAME], False)
        for agent, destination in installer.TARGETS.items():
            skill = home / destination / NAME
            script = skill / 'scripts/project_context.py'
            before = installer.snapshot(skill)
            source = skill / 'assets/example-project.json'
            result = subprocess.run([sys.executable, str(script), 'validate', str(source)],
                                    capture_output=True, text=True, check=True)
            self.assertFalse(json.loads(result.stdout)['provider_access_verified'])
            result = subprocess.run([sys.executable, str(script), 'render', str(source)],
                                    capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(result.stdout), self.example)
            self.assertEqual(installer.snapshot(skill), before, agent)


if __name__ == '__main__':
    unittest.main()
