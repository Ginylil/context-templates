"""Execute the ledger command advertised by each generated standalone guide."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / 'skills'
spec = importlib.util.spec_from_file_location('definition_guide_installer', ROOT / 'scripts/skills.py')
installer = importlib.util.module_from_spec(spec); spec.loader.exec_module(installer)


class DefinitionGuideTests(unittest.TestCase):
    def run_documented_status(self, folder, ledger):
        guide = folder / 'references' / ('contract.md' if folder.name == 'ct-product-define-project' else 'definition-contract.md')
        documented = re.search(r'python3 <skill>/scripts/([^\s/]+\.py) status ledger\.json', guide.read_text(encoding='utf-8'))
        self.assertIsNotNone(documented, f'No documented ledger status command in {guide}')
        result = subprocess.run([sys.executable, str(folder / 'scripts' / documented.group(1)), 'status', str(ledger)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f'{folder.name}: {result.stderr}')
        status = json.loads(result.stdout)
        self.assertEqual(status['status'], 'valid')
        self.assertEqual((status['questions_used'], status['batches_used']), (2, 1))

    def test_documented_status_command_runs_in_every_lifecycle_package(self):
        ledger = SKILLS / 'ct-product-define-project/assets/example-ledger.json'
        catalog = json.loads((SKILLS / 'ct-product-manage-project/assets/catalog.json').read_text(encoding='utf-8'))
        for item in catalog:
            with self.subTest(skill=item['skill']):
                self.run_documented_status(SKILLS / item['skill'], ledger)

    def test_documented_command_runs_from_isolated_agent_and_zip_copies(self):
        name = 'ct-rnd-fix-bug'
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            ledger = base / 'ledger.json'
            ledger.write_bytes((SKILLS / 'ct-product-define-project/assets/example-ledger.json').read_bytes())
            with contextlib.redirect_stdout(io.StringIO()):
                installer.install(ROOT, base / 'home', list(installer.TARGETS), [name], False)
                installer.build(ROOT, base / 'packages')
            folders = [base / 'home' / target / name for target in installer.TARGETS.values()]
            with zipfile.ZipFile(base / 'packages' / (name + '.zip')) as archive:
                archive.extractall(base / 'zip')
            folders.append(base / 'zip' / name)
            for folder in folders:
                with self.subTest(folder=folder):
                    self.run_documented_status(folder, ledger)


if __name__ == '__main__':
    unittest.main()
