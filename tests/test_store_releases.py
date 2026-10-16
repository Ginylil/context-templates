"""Offline store contracts. Synthetic receipts do not prove provider behavior."""
import contextlib
import io
import zipfile
import datetime as dt
import json
import subprocess
import sys
import unittest

from store_releases_fixture import (
    StoreReleaseFixture,
    ROOT,
    SKILLS,
    asset,
    workflow,
    fixture_module,
    manager,
    installer,
)


class StoreReleaseTests(StoreReleaseFixture):
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



if __name__ == "__main__":
    unittest.main()
