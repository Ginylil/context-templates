"""Exercise supported installation entrypoints in disposable agent homes."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from assembled_catalog import ROOT, installer


class InstallCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='ct-install-cli-')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.available = installer.catalog(ROOT)
        self.name = 'ct-rnd-fix-bug'

    def run_command(self, argv, cwd=ROOT, expected=0):
        result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def python(self, *args, **kwargs):
        return self.run_command([sys.executable, str(ROOT / 'scripts/skills.py'), *args], **kwargs)

    def verify_installed(self, home, names, agents):
        for agent in agents:
            base = home / installer.TARGETS[agent]
            receipt = json.loads((base / installer.STATE_FILE).read_text(encoding='utf-8'))
            self.assertEqual(set(receipt['skills']), set(names))
            for name in names:
                payload = installer.package_payload(ROOT, self.available[name])
                expected = installer.payload_snapshot(payload)
                self.assertEqual(installer.snapshot(base / name), expected)
                self.assertEqual(receipt['skills'][name], expected)

    def test_python_single_selection_dry_run_and_repeat_from_outside_checkout(self):
        for agent in installer.TARGETS:
            with self.subTest(agent=agent):
                home = self.base / agent
                args = ('install', '--agent', agent, '--skill', self.name, '--home', str(home))
                self.python(*args, '--dry-run', cwd=self.base)
                self.assertFalse(home.exists())
                self.python(*args, cwd=self.base)
                self.verify_installed(home, [self.name], [agent])
                receipt = home / installer.TARGETS[agent] / installer.STATE_FILE
                before = (receipt.read_bytes(), receipt.stat().st_mtime_ns)
                self.assertIn('unchanged ', self.python(*args, cwd=self.base).stdout)
                self.assertEqual((receipt.read_bytes(), receipt.stat().st_mtime_ns), before)
                self.assertEqual(set(home.iterdir()), {home / installer.TARGETS[agent].parts[0]})

    def test_python_full_catalog_for_all_agents_is_standalone_and_idempotent(self):
        home = self.base / 'all-agents'
        args = ('install', '--agent', 'all', '--home', str(home))
        self.python(*args, '--dry-run')
        self.assertFalse(home.exists())
        self.python(*args)
        self.verify_installed(home, self.available, installer.TARGETS)
        result = self.python(*args)
        self.assertEqual(result.stdout.count('unchanged '), len(self.available) * len(installer.TARGETS))
        for agent, target in installer.TARGETS.items():
            folder = home / target / self.name
            self.run_command([sys.executable, '-I', '-B', str(folder / 'scripts/definition.py'),
                              '--help'], cwd=self.base)
        self.assertFalse((home / 'dist').exists())

    def test_make_selected_and_aggregate_installers(self):
        make = shutil.which('make')
        if make is None:
            self.skipTest('Make is optional; Python entrypoints are tested on every OS')
        for agent in (*installer.TARGETS, 'all'):
            with self.subTest(agent=agent):
                home = self.base / f'make-{agent}'
                target = 'install' if agent == 'all' else f'install-{agent}'
                args = [make, target, f'PYTHON="{sys.executable}"', f'SKILL={self.name}']
                # INSTALL_ARGS is interpreted by the Make recipe, so quote paths with spaces.
                self.run_command([*args, f'INSTALL_ARGS=--home "{home}" --dry-run'])
                self.assertFalse(home.exists())
                self.run_command([*args, f'INSTALL_ARGS=--home "{home}"'])
                agents = installer.TARGETS if agent == 'all' else [agent]
                self.verify_installed(home, [self.name], agents)

    def test_removed_build_command_creates_no_output(self):
        output = self.base / 'old-build'
        result = self.python('build', '--output', str(output), expected=2)
        self.assertIn('invalid choice', result.stderr)
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
