"""Synthetic credential detection and redaction, never real credential fixtures."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('public_secret_scan', ROOT / 'scripts/secret_scan.py')
scanner = importlib.util.module_from_spec(spec); spec.loader.exec_module(scanner)


class SecretScanTests(unittest.TestCase):
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
