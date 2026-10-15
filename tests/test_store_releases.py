"""Offline store contracts. Synthetic receipts do not prove provider behavior."""
import copy
import contextlib
import io
import zipfile
import datetime as dt
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / 'skills'
spec = importlib.util.spec_from_file_location('store_engineering_fixture', ROOT / 'tests/test_engineering_lifecycle.py')
fixture_module = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture_module)
workflow = fixture_module.workflow
spec = importlib.util.spec_from_file_location('store_manager', SKILLS / 'ct-product-manage-project/scripts/manage.py')
manager = importlib.util.module_from_spec(spec); spec.loader.exec_module(manager)
spec = importlib.util.spec_from_file_location('store_installer', ROOT / 'scripts/skills.py')
installer = importlib.util.module_from_spec(spec); spec.loader.exec_module(installer)


def asset(platform, name):
    return json.loads((SKILLS / f'ct-devops-release-{platform}-app/assets' / name).read_text(encoding='utf-8'))


class StoreReleaseTests(unittest.TestCase):
    def setUp(self):
        self.f = fixture_module.EngineeringLifecycleTests(); self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.base = self.f.base
        for relative in ('ios/Fixture.xcodeproj/project.pbxproj', 'android/app/build.gradle', 'android/app/src/main/AndroidManifest.xml'):
            path = self.f.repository / relative; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('Synthetic native configuration fixture; not a compiled platform project.\n')
        final = self.base / 'configured-source.json'
        workflow.record([sys.executable, 'check.py'], self.f.repository, final)
        self.f.evidence = [e for e in self.f.evidence if e['kind'] != 'command' or e['id'] == 'before']
        self.f.evidence += [{'id': name, 'kind': 'command', 'reference': {'path': final.name, 'sha256': workflow.file_digest(final)}} for name in ('after', 'check')]

    def case(self, platform='apple', stage='prepare', device=False):
        policy, intake, output = [asset(platform, x) for x in ('contract.json', 'example-input.json', 'example-output.json')]
        intake['repository'] = {'path': 'repository', 'revision': self.f.revision,
                                'working_tree_sha256': workflow.tree_digest(self.f.repository)}
        intake['sources'] = [{'id': 'permission', **self.f.source_ref}, {'id': 'acceptance', **self.f.source_ref}]
        artifact = self.f.write('candidate.ipa' if platform == 'apple' else 'candidate.aab', 'Synthetic artifact fixture; not an application binary.')
        tracks = {'discover': 'none', 'configure': 'none', 'prepare': 'none', 'upload': 'none', 'testflight-internal': 'testflight-internal',
                  'testflight-external': 'testflight-external', 'submit-review': 'app-store',
                  'play-internal': 'internal', 'play-closed': 'alpha', 'play-open': 'beta',
                  'production': 'app-store' if platform == 'apple' else 'production'}
        data = intake['inputs']
        data.update(app_id='1234567890' if platform == 'apple' else 'com.example.notes', application_id='com.example.notes', version='1.0.0', build_number='1',
                    setup_mode='existing-native', requested_capabilities=[], candidate_revision=self.f.revision, artifact=artifact, target_stage=stage, track=tracks[stage],
                    authorization_source=None if stage == 'prepare' else 'permission',
                    authorized_stage=None if stage == 'prepare' else stage, require_device_proof=device,
                    countries=['US'] if stage == 'production' else [], rollout_percent=100 if stage != 'prepare' else 0)
        common = {'platform': platform, **{k: data[k] for k in ('platform_variant', 'app_id', 'application_id', 'version', 'build_number', 'candidate_revision')},
                  'artifact_sha256': artifact['sha256'], 'source': 'Synthetic fixture, not actual human authorization.',
                  'observed_at': dt.datetime.now(dt.timezone.utc).isoformat()}
        permission = dict(common, kind='ct-store-authorization.v1', authorized=True,
                          **{k: data[k] for k in ('target_stage', 'track', 'audience', 'countries', 'rollout_percent')})
        acceptance = dict(common, kind='ct-store-acceptance.v1', accepted=True)
        intake['sources'] = [{'id': 'permission', **self.f.write('authorization.json', permission)},
                             {'id': 'acceptance', **self.f.write('acceptance.json', acceptance)}]
        cfg = workflow.store_module().configuration_module()
        snapshot = cfg.discover(self.f.repository, platform, vars(workflow))
        data['discovery'] = self.f.write('discovery.json', snapshot)
        output.update(status='ready', blockers=[], summary='Synthetic contract fixture; no store contacted.', evidence=copy.deepcopy(self.f.evidence))
        result = output['result']
        result.update(candidate_revision=self.f.revision, artifact_sha256=artifact['sha256'], build_check='after', outcome=stage,
                      checks=[{'id': name, 'name': 'Synthetic ' + name, 'status': 'passed', 'evidence_ids': ['after']}
                              for name in ('tests', 'signing', 'compliance', 'recovery', 'tracking')])
        cfg_files = ['ios/Fixture.xcodeproj/project.pbxproj'] if platform == 'apple' else ['android/app/build.gradle', 'android/app/src/main/AndroidManifest.xml']
        result.update(environment_loader='Native fixture defaults; no dotenv loader.',
            configuration=[{'id': area, 'area': area, 'name': 'FIXTURE_' + area.upper().replace('-', '_'),
                'purpose': 'Synthetic ' + area + ' configuration.', 'required': True, 'status': 'configured',
                'location': cfg_files[0], 'setup_action': 'No action; synthetic configured fixture.',
                'verification': 'Inspect synthetic fixture proof.', 'storage': 'public-config', 'sensitive': False,
                'bundled': False, 'user_action': False, 'evidence_ids': ['after']} for area in cfg.AREAS],
            setup_plan=[], wrapper={'mode': 'existing-native', 'source_kind': 'native', 'delivery': 'native',
                'config_files': cfg_files, 'web_output_dir': None, 'runtime_url': None, 'backend_plan': 'not-applicable',
                'native_targets': [data['platform_variant']], 'sync_check': None, 'smoke_check': 'after',
                'limitations': ['Synthetic source fixture; not a signed app or device.']})
        if stage in ('discover', 'configure'):
            data['artifact'] = None; result['artifact_sha256'] = None
        if stage == 'discover':
            result['build_check'] = None; result['checks'] = []
        values = [policy, intake, output]
        if stage not in ('prepare', 'discover', 'configure'): self.receipt(values, platform, stage, 'store_readback')
        if stage == 'production':
            self.receipt(values, platform, 'testflight-internal' if platform == 'apple' else 'play-internal', 'testing_readback')
            result['acceptance_source'] = 'acceptance'
        if device:
            proof = {'kind': 'ct-device-proof.v1', 'platform': platform,
                     **{k: data[k] for k in ('platform_variant', 'app_id', 'application_id', 'version', 'build_number', 'candidate_revision')},
                     'artifact_sha256': artifact['sha256'], 'observed_at': dt.datetime.now(dt.timezone.utc).isoformat(),
                     'installed': True, 'smoke_passed': True, 'limitations': ['Synthetic fixture; no actual device.']}
            self.evidence(values, 'device_proof', proof)
        self.rebind(values)
        return values

    def evidence(self, values, field, data):
        key = field.replace('_', '-')
        ref = self.f.write(key + '.json', data)
        values[2]['evidence'] = [e for e in values[2]['evidence'] if e['id'] != key]
        values[2]['evidence'].append({'id': key, 'kind': 'artifact', 'reference': ref})
        values[2]['result'][field] = key

    def receipt(self, values, platform, stage, field):
        data = values[1]['inputs']
        testing = stage not in ('prepare', 'upload', 'submit-review', 'production')
        track = ('testflight-internal' if platform == 'apple' else 'internal') if field == 'testing_readback' else data['track']
        native = ('Testing' if testing else {'upload': 'PROCESSING', 'submit-review': 'WAITING_FOR_REVIEW', 'production': 'READY_FOR_DISTRIBUTION'}.get(stage)) if platform == 'apple' else ('uploaded' if stage == 'upload' else 'completed')
        record = {'kind': 'ct-store-readback.v1', 'platform': platform,
                  **{k: data[k] for k in ('platform_variant', 'app_id', 'application_id', 'version', 'build_number', 'candidate_revision')},
                  'artifact_sha256': data['artifact']['sha256'], 'stage': stage, 'track': track,
                  'observed_at': dt.datetime.now(dt.timezone.utc).isoformat(),
                  'source': 'https://appstoreconnect.apple.com/apps' if platform == 'apple' else 'https://play.google.com/console',
                  'native_status': native, 'distribution_status': 'available' if testing else {'upload': 'processing', 'submit-review': 'submitted', 'production': 'published'}[stage],
                  'review_status': 'approved' if stage in ('testflight-external', 'production') else ('pending' if stage == 'submit-review' else 'not-required'),
                  'testers_configured': testing, 'tester_access_verified': testing, 'external_eligible': True if platform == 'apple' else None,
                  'compliance_complete': True, 'production_access': True, 'rollout_percent': 100,
                  'countries': data['countries'] if field == 'store_readback' else [], 'audience': data['audience'],
                  'public_url': ('https://apps.apple.com/us/app/example/id' + data['app_id'] if platform == 'apple' else 'https://play.google.com/store/apps/details?id=' + data['application_id']) if stage == 'production' else None}
        self.evidence(values, field, record)
        return record

    def rebind(self, values):
        values[2]['input_sha256'] = workflow.digest(values[1])

    def validate(self, values):
        return workflow.validate_output(*values, self.base)

    def reject(self, values, reason):
        with self.assertRaisesRegex(ValueError, reason): self.validate(values)

    def modify_record(self, values, field='store_readback', **changes):
        item = next(e for e in values[2]['evidence'] if e['id'] == values[2]['result'][field])
        data = workflow.load(self.base / item['reference']['path']); data.update(changes)
        self.evidence(values, field, data)

    def test_every_requested_milestone_validates_without_fresh_definition(self):
        for platform in ('apple', 'android'):
            for stage in asset(platform, 'contract.json')['inputs']['fields']['target_stage']['enum']:
                with self.subTest(platform=platform, stage=stage):
                    self.validate(self.case(platform, stage))

    def test_ready_cli_runs_from_each_agent_install_and_built_zip(self):
        names = ['ct-devops-release-apple-app', 'ct-devops-release-android-app']
        home = self.base / 'home'
        with contextlib.redirect_stdout(io.StringIO()):
            installer.install(ROOT, home, list(installer.TARGETS), names, False)
            installer.build(ROOT, self.base / 'packages')
        for platform in ('apple', 'android'):
            name = f'ct-devops-release-{platform}-app'
            values = self.case(platform, 'testflight-external' if platform == 'apple' else 'play-closed')
            intake = self.f.write('cli-input.json', values[1]); output = self.f.write('cli-output.json', values[2])
            locations = [(agent, home / target / name) for agent, target in installer.TARGETS.items()]
            with zipfile.ZipFile(self.base / 'packages' / (name + '.zip')) as archive:
                archive.extractall(self.base / 'unpacked')
            locations.append(('zip', self.base / 'unpacked' / name))
            for label, folder in locations:
                script = folder / 'scripts/workflow.py'
                for command in (['validate-input', str(self.base / intake['path'])],
                                ['validate-output', str(self.base / intake['path']), str(self.base / output['path'])],
                                ['render', str(self.base / intake['path']), str(self.base / output['path']), '--output', str(self.base / (platform + '-' + label + '.md'))]):
                    result = subprocess.run([sys.executable, str(script), *command], cwd=self.base, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_apple_bundle_hyphens_do_not_use_android_identifier_rules(self):
        values = self.case()
        values[1]['inputs']['application_id'] = 'com.example.follow-up'
        workflow.validate_input(values[0], values[1], self.base)
        values = self.case('android')
        values[1]['inputs']['application_id'] = 'com.example.follow-up'
        with self.assertRaisesRegex(ValueError, 'bundle/package identifier'):
            workflow.validate_input(values[0], values[1], self.base)

    def test_honest_packaged_blocked_examples_validate(self):
        for platform in ('apple', 'android'):
            self.validate([asset(platform, x) for x in ('contract.json', 'example-input.json', 'example-output.json')])

    def test_upload_does_not_claim_tester_availability(self):
        values = self.case(stage='upload')
        self.modify_record(values, distribution_status='available')
        self.reject(values, 'later milestone')

    def test_testing_requires_access_beyond_group_assignment(self):
        for platform, stage in [('apple', 'testflight-internal'), ('android', 'play-internal')]:
            values = self.case(platform, stage); self.modify_record(values, tester_access_verified=False)
            self.reject(values, 'not verified access')

    def test_apple_internal_only_is_never_admitted(self):
        values = self.case(stage='testflight-internal'); self.modify_record(values, external_eligible=False)
        self.reject(values, 'Internal Only')

    def test_external_beta_pending_review_blocks(self):
        values = self.case(stage='testflight-external'); self.modify_record(values, review_status='pending')
        self.reject(values, 'review incomplete')

    def test_external_beta_can_use_provider_confirmed_no_review_needed(self):
        values = self.case(stage='testflight-external'); self.modify_record(values, review_status='not-required')
        self.validate(values)

    def test_add_for_review_is_not_actual_submission(self):
        values = self.case(stage='submit-review'); self.modify_record(values, native_status='Ready for Review')
        self.reject(values, 'submission not confirmed')

    def test_draft_and_halted_play_are_not_testing(self):
        for status in ('draft', 'halted'):
            values = self.case('android', 'play-closed'); self.modify_record(values, native_status=status)
            self.reject(values, 'not rolled out')

    def test_open_testing_requires_confirmed_eligibility(self):
        values = self.case('android', 'play-open'); self.modify_record(values, production_access=False)
        self.reject(values, 'eligibility')

    def test_invalid_apple_native_testing_states_are_rejected(self):
        for native in ('Not Available for Testing', 'Not Validated', 'Ready to Test', 'Made Up'):
            values = self.case(stage='testflight-internal'); self.modify_record(values, native_status=native)
            self.reject(values, 'native status')

    def test_human_decisions_are_bound_to_candidate_and_scope(self):
        values = self.case('android', 'production')
        record = workflow.load(self.base / 'acceptance.json'); record['build_number'] = '2'
        values[1]['sources'][1].update(self.f.write('acceptance.json', record)); self.rebind(values)
        self.reject(values, 'decision candidate mismatch')
        values = self.case('android', 'play-internal')
        record = workflow.load(self.base / 'authorization.json'); record['audience'] = ['Public users']
        values[1]['sources'][0].update(self.f.write('authorization.json', record)); self.rebind(values)
        self.reject(values, 'authorization scope mismatch')

    def test_google_oauth_values_are_not_credential_references(self):
        values = self.case('android')
        values[1]['inputs']['credential_refs'][0].update(provider='env', name='ya29.' + 'synthetic_value_abcdefghijklmnop')
        self.rebind(values); self.reject(values, 'credential-like')

    def test_closed_track_cannot_change_without_matching_authorization(self):
        values = self.case('android', 'play-closed')
        values[1]['inputs']['track'] = 'customer-preview'
        self.receipt(values, 'android', 'play-closed', 'store_readback'); self.rebind(values)
        self.reject(values, 'authorization scope mismatch: track')

    def test_wrong_track_scope_candidate_and_artifact_fail(self):
        for field, change, reason in [('track', 'production', 'stage/track'), ('audience', ['Other group'], 'scope changed'),
             ('build_number', '999', 'build_number'), ('artifact_sha256', '0' * 64, 'wrong artifact'),
             ('candidate_revision', '0' * 40, 'candidate_revision')]:
            values = self.case(stage='testflight-internal'); self.modify_record(values, **{field: change})
            self.reject(values, reason)

    def test_artifact_bytes_and_output_hash_are_checked(self):
        values = self.case(); (self.base / values[1]['inputs']['artifact']['path']).write_text('Changed artifact')
        self.reject(values, 'stale or mismatched')
        values = self.case(); values[2]['result']['artifact_sha256'] = '0' * 64
        self.reject(values, 'digest mismatch')

    def test_mutation_needs_action_scoped_authority(self):
        values = self.case(stage='testflight-internal')
        values[1]['inputs']['authorized_stage'] = 'production'; self.rebind(values)
        self.reject(values, 'scoped authorization')

    def test_credentials_are_references_never_inline_values(self):
        values = self.case(); values[1]['inputs']['credential_refs'][0]['value'] = 'synthetic-forbidden-value'
        self.rebind(values); self.reject(values, 'unknown fields')
        values = self.case(); values[1]['inputs']['credential_refs'][0]['name'] = 'ghp_' + 'z' * 40
        self.rebind(values); self.reject(values, 'credential-like')

    def test_production_needs_testing_and_human_acceptance(self):
        for field, reason in [('testing_readback', 'missing store readback'), ('acceptance_source', 'human acceptance')]:
            values = self.case('android', 'production'); values[2]['result'][field] = None
            self.reject(values, reason)

    def test_production_cannot_reuse_other_build_testing(self):
        values = self.case('android', 'production'); self.modify_record(values, 'testing_readback', build_number='2')
        self.reject(values, 'build_number')

    def test_public_storefront_and_rollout_are_bound(self):
        values = self.case('android', 'production'); self.modify_record(values, public_url='https://play.google.com/store/apps/details?id=com.example.other')
        self.reject(values, 'wrong Play storefront')
        values = self.case('android', 'production'); self.modify_record(values, native_status='completed', rollout_percent=50)
        values[1]['inputs']['rollout_percent'] = 50
        decision = workflow.load(self.base / 'authorization.json'); decision['rollout_percent'] = 50
        values[1]['sources'][0].update(self.f.write('authorization.json', decision)); self.rebind(values)
        self.reject(values, 'rollout fraction')

    def test_device_proof_is_separate_and_candidate_bound(self):
        values = self.case(stage='testflight-internal', device=True); self.validate(values)
        values[2]['result']['device_proof'] = None; self.reject(values, 'installed-device')
        values = self.case(stage='testflight-internal', device=True)
        item = next(e for e in values[2]['evidence'] if e['id'] == 'device-proof')
        data = workflow.load(self.base / item['reference']['path']); data['build_number'] = '2'
        self.evidence(values, 'device_proof', data); self.reject(values, 'wrong device candidate')

    def test_stale_future_and_secret_bearing_source_urls_fail(self):
        values = self.case(stage='upload')
        self.modify_record(values, observed_at=(dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=2)).isoformat())
        self.reject(values, 'stale readback')
        values = self.case(stage='upload'); self.modify_record(values, source='https://appstoreconnect.apple.com/apps?token=do-not-log')
        self.reject(values, 'sanitized provider')

    def test_malformed_provider_fields_fail_as_validation_errors(self):
        for field, value in [('source', 42), ('public_url', True), ('observed_at', None),
                             ('native_status', {}), ('audience', 'all-users'), ('rollout_percent', True)]:
            values = self.case(stage='testflight-internal'); self.modify_record(values, **{field: value})
            with self.assertRaises(ValueError): self.validate(values)

    def test_wrong_apple_platform_variant_is_rejected(self):
        values = self.case(stage='testflight-internal'); self.modify_record(values, platform_variant='macos')
        self.reject(values, 'platform_variant')

    def test_failed_required_check_cannot_be_ready(self):
        values = self.case(); values[2]['result']['checks'][0]['evidence_ids'] = ['before']
        self.reject(values, 'failing or timed-out')

    def test_project_guide_routes_each_platform_directly(self):
        state = json.loads((SKILLS / 'ct-product-manage-project/assets/example-state.json').read_text())
        for platform in ('apple', 'android'):
            state['intent'] = f'release-{platform}-app'
            result = manager.route(state, self.base, SKILLS)
            self.assertEqual(result['next_skill'], f'ct-devops-release-{platform}-app')

    def test_manager_enforces_platform_readback_not_just_base_schema(self):
        values = self.case(stage='testflight-internal'); self.modify_record(values, external_eligible=False)
        intake = self.f.write('manager-input.json', values[1]); report = self.f.write('manager-output.json', values[2])
        state = json.loads((SKILLS / 'ct-product-manage-project/assets/example-state.json').read_text())
        state.update(project_id=values[1]['project_id'], repository=values[1]['repository'], receipts=[{'skill': values[0]['skill'], 'input': intake, 'output': report}])
        with self.assertRaisesRegex(ValueError, 'Internal Only'):
            manager.validate_state(state, self.base, SKILLS)
