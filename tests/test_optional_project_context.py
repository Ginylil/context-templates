"""Optional context discovery has bounded roots and no workspace side effects."""
import json
import contextlib
import io
import importlib.util
from pathlib import Path
import subprocess
import stat
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from assembled_catalog import SKILLS, installer

NAME = 'ct-product-configure-project'


class OptionalContextTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.project = self.base / 'project'
        self.project.mkdir()
        self.script = SKILLS / NAME / 'scripts/project_context.py'
        self.profile = json.loads((SKILLS / NAME / 'assets/example-project.json').read_text())

    def run_cli(self, script=None, profile=None):
        argv = [sys.executable, str(script or self.script), 'discover', '--root', str(self.project)]
        if profile is not None:
            argv.extend(['--profile', str(profile)])
        return subprocess.run(argv, capture_output=True, text=True)

    def save(self, value=None, path=None):
        path = path or self.project / 'context-templates/project.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value or self.profile))
        return path

    def test_missing_context_is_optional_and_does_not_search_parent_projects(self):
        self.save(path=self.base / 'context-templates/project.json')
        before = installer.snapshot(self.project)
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'absent')
        self.assertEqual(installer.snapshot(self.project), before)

    def test_detected_profile_preserves_mixed_providers_docs_and_execution_location(self):
        self.save()
        before = installer.snapshot(self.project)
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value['status'], 'present')
        self.assertEqual(value['selection'], 'repository')
        self.assertEqual(value['profile'], self.profile)
        self.assertFalse(value['provider_access_verified'])
        self.assertEqual(installer.snapshot(self.project), before)

    def test_invalid_or_credential_bearing_context_fails_without_fallback_or_echo(self):
        path = self.save()
        for content in ('{invalid', '{"schema_version":1}', json.dumps({**self.profile, 'password': 'private-value'})):
            path.write_text(content)
            result = self.run_cli()
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, '')
            self.assertNotIn('private-value', result.stderr)

    def test_private_profile_is_explicit_and_does_not_rebase_relative_documentation(self):
        private = self.save(path=self.base / 'private-profile.json')
        self.save({'schema_version': 999})
        result = self.run_cli(profile=private)
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value['selection'], 'explicit')
        self.assertEqual(value['project_root'], str(self.project.resolve()))
        self.assertEqual(value['profile']['documentation'][0]['location'], 'docs/')
        missing = self.run_cli(profile=self.base / 'missing-profile.json')
        self.assertEqual(missing.returncode, 1)
        self.assertEqual(missing.stdout, '')

    def test_undecided_context_remains_undecided_without_starting_an_interview(self):
        self.profile['source_control'] = {'provider': 'undecided', 'location': None}
        self.save()
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['undecided'], ['source_control'])

    def test_linked_repository_context_is_not_followed(self):
        outside = self.save(path=self.base / 'outside.json')
        parent = self.project / 'context-templates'
        parent.mkdir()
        try:
            (parent / 'project.json').symlink_to(outside)
        except OSError:
            self.skipTest('Symlink creation unavailable on this runner')
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, '')

    def test_context_directory_cannot_redirect_discovery_or_be_a_regular_file(self):
        parent = self.project / 'context-templates'
        parent.write_text('Not a context directory')
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        parent.unlink()
        outside = self.base / 'other-project'
        outside.mkdir()
        try:
            parent.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('Directory symlinks unavailable on this runner')
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, '')

    def test_windows_reparse_points_are_rejected_on_older_supported_python(self):
        source = SKILLS / NAME / 'scripts/project_context_discovery.py'
        spec = importlib.util.spec_from_file_location('ct_context_discovery_test', source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.save()
        root = self.project.resolve()
        real_lstat = Path.lstat
        for relative in ('context-templates', 'context-templates/project.json'):
            target = root / relative

            def metadata(path):
                if path == target:
                    return SimpleNamespace(st_mode=stat.S_IFDIR,
                                           st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT)
                return real_lstat(path)

            with patch.object(Path, 'lstat', metadata), self.assertRaises(module.DiscoveryError):
                module.discover(root, None, lambda _: self.profile, lambda _: [])

    def test_unreadable_metadata_is_not_reported_as_absent(self):
        source = SKILLS / NAME / 'scripts/project_context_discovery.py'
        spec = importlib.util.spec_from_file_location('ct_context_permissions_test', source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.save()
        root = self.project.resolve()
        target = root / 'context-templates/project.json'
        real_lstat = Path.lstat

        def metadata(path):
            if path == target:
                raise PermissionError('Unreadable synthetic profile')
            return real_lstat(path)

        with patch.object(Path, 'lstat', metadata), self.assertRaises(PermissionError):
            module.discover(root, None, lambda _: self.profile, lambda _: [])

    def test_single_skill_installs_are_self_contained_for_all_agent_targets(self):
        home = self.base / 'home'
        names = ['ct-rnd-build-feature', 'ct-dynamic-uml', 'ct-rnd-prepare-next-session']
        root = Path(__file__).resolve().parents[1]
        with contextlib.redirect_stdout(io.StringIO()):
            installer.install(root, home, list(installer.TARGETS), names, False)
        self.save()
        for target in installer.TARGETS.values():
            for name in names:
                folder = home / target / name
                before = installer.snapshot(folder)
                result = self.run_cli(script=folder / 'scripts/project_context.py')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)['status'], 'present')
                self.assertTrue((folder / 'references/optional-addons.md').is_file())
                self.assertEqual(installer.snapshot(folder), before)


if __name__ == '__main__':
    unittest.main()
