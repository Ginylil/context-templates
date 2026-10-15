"""Synthetic configuration/wrapper checks; no native toolchain or store access."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('release_store_fixture', Path(__file__).with_name('test_store_releases.py'))
fixtures = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixtures)
workflow = fixtures.workflow
ROOT = fixtures.ROOT


class ReleaseConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.store = fixtures.StoreReleaseTests(); self.store.setUp()
        self.addCleanup(self.store.doCleanups)
        self.repo = self.store.f.repository
        self.cfg = workflow.store_module().configuration_module()

    def file(self, name, content):
        path = self.repo / name; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8'); return path

    def refresh(self, values):
        proof = self.store.base / 'refreshed-command.json'
        if proof.exists(): proof.unlink()
        workflow.record([sys.executable, 'check.py'], self.repo, proof)
        values[2]['evidence'] = [e for e in values[2]['evidence'] if e['id'] not in ('after', 'check')]
        values[2]['evidence'] += [{'id': name, 'kind': 'command', 'reference': {'path': proof.name, 'sha256': workflow.file_digest(proof)}} for name in ('after', 'check')]
        values[1]['repository']['working_tree_sha256'] = workflow.tree_digest(self.repo)
        values[1]['inputs']['discovery'] = self.store.f.write('refreshed-discovery.json', self.cfg.discover(self.repo, values[0]['rules'][-1]['platform'], vars(workflow)))
        self.store.rebind(values)

    def wrapped(self, platform):
        self.file('www/index.html', '<!doctype html><title>Synthetic offline wrapper</title>')
        self.file('capacitor.config.ts', 'export default {appId:"com.example.notes",webDir:"www"};')
        values = self.store.case(platform, 'configure')
        values[1]['inputs']['setup_mode'] = 'wrap-web'
        values[2]['result']['wrapper'].update(mode='capacitor', source_kind='static', delivery='bundled',
            config_files=['capacitor.config.ts'] + values[2]['result']['wrapper']['config_files'],
            web_output_dir='www', sync_check='after', smoke_check='check')
        self.refresh(values)
        return values

    def test_discovery_reports_names_locations_and_stack_without_reading_private_values(self):
        self.file('.gitignore', '.env.local\nsigning.p8\n')
        private = {self.file('.env.local', 'SYNTHETIC_ONLY=never-print-this-inert-fixture'),
                   self.file('signing.p8', 'inert fixture; not a private key')}
        self.file('package.json', json.dumps({'dependencies': {'vite': '0.0.0', '@capacitor/core': '0.0.0'}}))
        self.file('src/app.ts', 'console.log(import.meta.env.VITE_API_URL, process.env["SERVER_TOKEN"]);')
        original = Path.read_bytes
        def guard(path):
            if path in private: raise AssertionError('private file read')
            return original(path)
        with patch.object(Path, 'read_bytes', guard):
            snapshot = self.cfg.discover(self.repo, 'apple', vars(workflow))
        serialized = json.dumps(snapshot)
        self.assertNotIn('never-print-this-inert-fixture', serialized)
        self.assertNotIn(hashlib.sha256(b'SYNTHETIC_ONLY=never-print-this-inert-fixture').hexdigest(), serialized)
        self.assertEqual(snapshot['detected_dependencies'], ['@capacitor/core', 'vite'])
        self.assertIn({'name': 'VITE_API_URL', 'paths': ['src/app.ts']}, snapshot['environment_references'])
        self.assertIn({'path': '.env.local', 'ignored': True}, snapshot['environment_files'])

    def test_unignored_or_tracked_private_files_block_before_fingerprinting(self):
        for name in ('.env.local', 'release.keystore'):
            with self.subTest(name=name):
                path = self.file(name, 'inert fixture')
                with patch.dict(vars(workflow), {'tree_digest': lambda _: self.fail('private file fingerprinted')}):
                    with self.assertRaisesRegex(ValueError, 'private environment/signing file'):
                        self.cfg.discover(self.repo, 'android', vars(workflow))
                path.unlink()
        self.file('.gitignore', '.env.local\n')
        path = self.file('.env.local', 'inert fixture')
        subprocess.run(['git', 'add', '-f', '.env.local'], cwd=self.repo, check=True, capture_output=True)
        with self.assertRaisesRegex(ValueError, 'private environment/signing file'):
            self.cfg.discover(self.repo, 'apple', vars(workflow))

    def test_public_environment_template_remains_supported(self):
        self.file('.env.example', 'VITE_API_URL=<public-api-url>\n')
        self.assertIn({'path': '.env.example', 'ignored': False}, self.cfg.discover(self.repo, 'apple', vars(workflow))['environment_files'])

    def test_discovery_cli_is_read_only_and_refuses_output_overwrite(self):
        self.file('package.json', '{"scripts":{"postinstall":"do-not-execute"}}')
        output = self.store.base / 'cli-discovery.json'
        argv = [sys.executable, str(ROOT / 'skills/ct-devops-release-apple-app/scripts/configuration.py'), '--repository', str(self.repo), '--platform', 'apple', '--output', str(output)]
        first = subprocess.run(argv, capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        before = output.read_bytes()
        second = subprocess.run(argv, capture_output=True, text=True)
        self.assertNotEqual(second.returncode, 0)
        self.assertEqual(before, output.read_bytes())
        self.assertNotIn('do-not-execute', output.read_text())

    def test_stale_or_modified_discovery_is_rejected(self):
        values = self.store.case('apple', 'discover')
        snapshot = workflow.load(self.store.base / values[1]['inputs']['discovery']['path'])
        snapshot['detected_dependencies'] = ['expo']
        values[1]['inputs']['discovery'] = self.store.f.write('tampered-discovery.json', snapshot)
        self.store.rebind(values)
        self.store.reject(values, 'stale or modified discovery')

    def test_ready_discovery_explains_missing_settings_then_configuration_stays_blocked(self):
        for platform in ('apple', 'android'):
            values = self.store.case(platform, 'discover')
            row = values[2]['result']['configuration'][0]
            row.update(status='missing', evidence_ids=[], setup_action='Set bundle/package ID in discovered native project.')
            values[2]['result']['setup_plan'] = [{'configuration_id': row['id'], 'action': row['setup_action'],
                'where': row['location'], 'verification': 'Inspect effective native identifier.', 'owner': 'agent',
                'status': 'pending', 'evidence_ids': []}]
            self.store.validate(values)
            values[1]['inputs']['target_stage'] = 'configure'; values[2]['result']['outcome'] = 'configure'
            self.store.rebind(values)
            self.store.reject(values, 'unresolved required configuration')
            values[2]['result']['setup_plan'] = []
            self.store.reject(values, 'missing actionable setup step')

    def test_required_areas_and_requested_capabilities_cannot_be_omitted(self):
        values = self.store.case('android', 'discover')
        values[2]['result']['configuration'].pop()
        self.store.reject(values, 'missing required configuration area')
        values = self.store.case('apple', 'discover')
        values[1]['inputs']['requested_capabilities'] = ['camera']; self.store.rebind(values)
        self.store.reject(values, 'missing required configuration area')

    def test_discovered_runtime_variables_must_be_in_inventory(self):
        self.file('src/config.ts', 'export const api = import.meta.env.VITE_API_URL;')
        values = self.store.case('apple', 'discover')
        self.refresh(values)
        self.store.reject(values, 'environment reference omitted')

    def test_secrets_cannot_be_bundled_or_use_public_prefixes_even_in_blocked_reports(self):
        for change, reason in (({'sensitive': True, 'bundled': True}, 'never be bundled'),
                               ({'sensitive': True, 'storage': 'ci-secret', 'name': 'VITE_PRIVATE_TOKEN'}, 'client-exposed'),
                               ({'sensitive': True, 'storage': 'public-config'}, 'unsafe secret storage')):
            values = self.store.case('android', 'discover')
            values[2].update(status='blocked', blockers=[{'reason': 'Fixture blocker.', 'next_action': 'Resolve fixture.'}])
            values[2]['result']['configuration'][0].update(change)
            self.store.reject(values, reason)

    def test_local_secret_file_needs_real_loader_and_ignore_rule(self):
        values = self.store.case('apple', 'discover')
        row = values[2]['result']['configuration'][0]
        row.update(sensitive=True, storage='local-env', location='.env.local')
        self.store.reject(values, 'local secret file must exist and be ignored')
        values[2]['result']['environment_loader'] = 'unknown'
        self.store.reject(values, 'actual environment loader')
        self.file('.gitignore', '.env.local\n'); self.file('.env.local', 'FIXTURE_ONLY=<set-in-secret-store>')
        values[2]['result']['environment_loader'] = 'Synthetic explicitly implemented loader.'
        self.refresh(values)
        self.store.validate(values)

    def test_configured_fields_and_done_steps_require_evidence(self):
        values = self.store.case('apple', 'discover')
        values[2]['result']['configuration'][0]['evidence_ids'] = []
        self.store.reject(values, 'lacks verification evidence')
        values = self.store.case('apple', 'discover')
        row = values[2]['result']['configuration'][0]
        values[2]['result']['setup_plan'] = [{'configuration_id': row['id'], 'action': 'Synthetic action.', 'where': row['location'],
            'verification': 'Synthetic verification.', 'owner': 'agent', 'status': 'done', 'evidence_ids': []}]
        self.store.reject(values, 'done step lacks')

    def test_both_bundled_wrapper_setup_paths_pass_with_real_fixture_files_and_command_proof(self):
        for platform in ('apple', 'android'):
            self.store.validate(self.wrapped(platform))

    def test_missing_web_output_and_missing_native_configuration_are_rejected(self):
        values = self.wrapped('apple')
        values[2]['result']['wrapper']['web_output_dir'] = 'missing'
        self.store.reject(values, 'web output index.html missing')
        values[2]['result']['wrapper']['web_output_dir'] = 'www'
        values[2]['result']['wrapper']['config_files'] = ['nonexistent.xcconfig']
        self.store.reject(values, 'native configuration file does not exist')

    def test_ssr_requires_backend_plan_and_native_sync_smoke_must_pass(self):
        values = self.wrapped('android')
        values[2]['result']['wrapper']['source_kind'] = 'ssr'
        self.store.reject(values, 'SSR requires')
        values[2]['result']['wrapper']['backend_plan'] = 'Retain existing HTTPS backend; native client uses public API endpoint.'
        values[2]['result']['wrapper']['sync_check'] = 'before'
        self.store.reject(values, 'command.*(pass|fail|exit)')

    def test_hosted_route_rejects_development_capacitor_url_and_unsafe_urls(self):
        values = self.wrapped('apple'); wrapper = values[2]['result']['wrapper']
        wrapper.update(delivery='hosted', runtime_url='https://example.org')
        self.store.reject(values, 'development facility')
        wrapper['mode'] = 'custom'
        for url in ('http://example.org', 'https://localhost', 'https://user:pass@example.org', 'https://example.org/?credential=fixture'):
            wrapper['runtime_url'] = url
            self.store.reject(values, 'safe production HTTPS URL')

    def test_web_setup_cannot_claim_existing_native_route_or_wrong_platform(self):
        values = self.wrapped('android')
        values[2]['result']['wrapper']['mode'] = 'existing-native'
        self.store.reject(values, 'web wrapping cannot claim')
        values[2]['result']['wrapper'].update(mode='capacitor', native_targets=['ios'])
        self.store.reject(values, 'native wrapper target is not ready')

    def test_existing_native_setup_requires_passing_native_smoke_evidence(self):
        for platform in ('apple', 'android'):
            values = self.store.case(platform, 'configure')
            values[2]['result']['wrapper']['smoke_check'] = None
            self.store.reject(values, 'command')

    def test_capacitor_cannot_masquerade_as_macos_native_packaging(self):
        values = self.wrapped('apple')
        values[1]['inputs']['platform_variant'] = 'macos'
        values[2]['result']['wrapper']['native_targets'] = ['macos']
        self.store.rebind(values)
        self.store.reject(values, 'Capacitor supports only')

    def test_generated_example_hashes_match_synthetic_inputs_and_cli(self):
        for platform in ('apple', 'android'):
            folder = ROOT / f'skills/ct-devops-release-{platform}-app'
            intake = fixtures.asset(platform, 'example-input.json')
            output = fixtures.asset(platform, 'example-output.json')
            expected = hashlib.sha256(json.dumps(intake, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
            self.assertEqual(output['input_sha256'], expected)
            command = subprocess.run([sys.executable, str(folder / 'scripts/workflow.py'), 'hash-input', str(folder / 'assets/example-input.json')], capture_output=True, text=True)
            self.assertEqual(command.returncode, 0, command.stderr)
            self.assertEqual(json.loads(command.stdout), {'input_sha256': expected})
            values = self.store.case(platform, 'discover')
            values[1]['request'] += ' Changed synthetic request.'
            self.store.reject(values, 'digest|stale|input')

    def test_example_hash_generation_repairs_stale_digest(self):
        spec = importlib.util.spec_from_file_location('ct_resource_sync', ROOT / 'scripts/ct_lifecycle.py')
        sync = importlib.util.module_from_spec(spec); spec.loader.exec_module(sync)
        for platform in ('apple', 'android'):
            path = ROOT / f'skills/ct-devops-release-{platform}-app/assets/example-output.json'
            original = path.read_text()
            altered = json.loads(original); altered['input_sha256'] = '0' * 64
            original_read = Path.read_text
            def stale(p, *args, **kwargs):
                return json.dumps(altered) if p == path else original_read(p, *args, **kwargs)
            with patch.object(Path, 'read_text', stale):
                generated = json.loads(sync.outputs()[path])
            self.assertEqual(generated['input_sha256'], json.loads(original)['input_sha256'])


if __name__ == '__main__':
    unittest.main()
