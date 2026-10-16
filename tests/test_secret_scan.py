"""Synthetic credential detection and redaction, never real credential fixtures."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('public_secret_scan', ROOT / 'scripts/secret_scan.py')
scanner = importlib.util.module_from_spec(spec); spec.loader.exec_module(scanner)


class SecretScanTests(unittest.TestCase):
    def git(self, root, *args):
        return subprocess.run(
            ['git', '-c', 'user.name=Scanner Test', '-c', 'user.email=scanner@example.invalid', *args],
            cwd=root, check=True, capture_output=True)

    def test_synthetic_private_key_and_token_are_detected_without_value_output(self):
        token = b'ghp_' + b'notavalidcredential0123456789ABCDEFG'
        key = b'-----BEGIN ' + b'PRIVATE KEY-----\nsynthetic-only\n'
        for value in (token, key):
            result = scanner.findings(value, 'synthetic.txt')
            self.assertTrue(result)
            self.assertNotIn(value.decode(), json.dumps(result))
            self.assertEqual(set(result[0]), {'path', 'line', 'rule'})

    def test_credential_assignments_are_detected_but_runtime_references_are_allowed(self):
        value = b'api_' + b'key="synthetic0123456789ABCDEFG-value"'
        self.assertTrue(scanner.findings(value, 'configuration.txt'))
        safe = json.dumps({'credential_refs': [{'provider': 'env', 'name': 'EXAMPLE_RELEASE_IDENTITY'}]}).encode()
        self.assertEqual(scanner.findings(safe, 'example.json'), [])

    def test_empty_signing_and_environment_files_are_rejected(self):
        for name in ('credentials.p8', 'upload.jks', 'signing.keystore', '.env.production'):
            self.assertEqual(scanner.findings(b'', name)[0]['rule'], 'credential-file')
        self.assertEqual(scanner.findings(b'', '.env.example'), [])

    def test_scan_includes_untracked_public_files_and_catalog_zip_contents(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(['git', 'init', '-q'], cwd=root, check=True, capture_output=True)
            (root / 'safe.md').write_text('Public instructions.')
            self.assertFalse(scanner.scan(root)['findings'])
            (root / 'upload.p8').write_text('Synthetic; no key material.')
            self.assertTrue(scanner.scan(root)['findings'])
            # Keep the package fixture outside the public working tree.
            packages = root / 'dist'; packages.mkdir()
            (root / '.gitignore').write_text('dist/\n')
            with zipfile.ZipFile(packages / 'example.zip', 'w') as archive:
                archive.writestr('example/secret.txt', b'ghp_' + b'notavalidcredential0123456789ABCDEFG')
            (packages / 'catalog.json').write_text(json.dumps({'skills': [{'archive': 'example.zip'}]}))
            report = scanner.scan(root, packages)
            self.assertTrue(any(x['path'].startswith('example.zip:') for x in report['findings']))

    def test_staged_scan_reads_index_even_after_working_copy_is_cleaned(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.git(root, 'init', '-q')
            token = b'ghp_' + b'notavalidcredential0123456789ABCDEFG'
            target = root / 'configuration.txt'
            target.write_bytes(token)
            self.git(root, 'add', 'configuration.txt')
            target.write_text('Working copy is clean; index is unsafe.')
            self.assertEqual(scanner.scan(root)['findings'], [])
            report = scanner.scan(root, staged=True)
            self.assertTrue(any(x['rule'] == 'github-token' for x in report['findings']))
            self.assertNotIn(token.decode(), json.dumps(report))

    def test_staged_scan_ignores_unstaged_changes_and_deleted_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.git(root, 'init', '-q')
            target = root / 'safe.txt'; target.write_text('Synthetic public content.')
            self.git(root, 'add', 'safe.txt')
            self.git(root, 'commit', '-qm', 'Safe initial content')
            self.git(root, 'rm', 'safe.txt')
            (root / 'untracked.p8').write_text('Synthetic signing-file example.')
            self.assertEqual(scanner.scan(root, staged=True)['findings'], [])

    def test_staged_scan_rejects_force_added_ignored_environment_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.git(root, 'init', '-q')
            (root / '.gitignore').write_text('.env\n')
            (root / '.env').write_text('Synthetic configuration; no key.')
            self.git(root, 'add', '-f', '.env')
            self.assertEqual(scanner.scan(root, staged=True)['findings'], [
                {'path': '.env', 'line': 0, 'rule': 'credential-file'}])

    @unittest.skipIf(os.name == 'nt', 'Symlink creation requires Windows developer mode or elevated permissions')
    def test_staged_scan_rejects_file_replaced_with_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.git(root, 'init', '-q')
            target = root / 'public.txt'; target.write_text('Synthetic public content.')
            self.git(root, 'add', 'public.txt')
            self.git(root, 'commit', '-qm', 'Safe initial content')
            target.unlink()
            target.symlink_to('synthetic-private-file.txt')
            self.git(root, 'add', 'public.txt')
            self.assertEqual(scanner.scan(root, staged=True)['findings'], [
                {'path': 'public.txt', 'line': 0, 'rule': 'public-symlink'}])

    def test_history_retains_deleted_secret_and_root_environment_filename(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.git(root, 'init', '-q')
            token = b'ghp_' + b'notavalidcredential0123456789ABCDEFG'
            (root / 'configuration.txt').write_bytes(token)
            (root / '.env').write_text('Synthetic historical environment configuration.')
            self.git(root, 'add', 'configuration.txt', '.env')
            self.git(root, 'commit', '-qm', 'Synthetic history fixture')
            self.git(root, 'rm', 'configuration.txt', '.env')
            self.git(root, 'commit', '-qm', 'Remove fixture from current tree')
            self.assertEqual(scanner.scan(root)['findings'], [])
            report = scanner.scan(root, history=True)
            self.assertTrue(any(x['rule'] == 'github-token' for x in report['findings']))
            self.assertTrue(any(x['rule'] == 'credential-file' and x['path'].endswith(':.env')
                                for x in report['findings']))
            self.assertNotIn(token.decode(), json.dumps(report))
