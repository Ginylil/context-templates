"""Test-free store releases fixtures shared by contract suites."""
import copy
import datetime as dt
import importlib.util
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
from assembled_catalog import SKILLS
spec = importlib.util.spec_from_file_location('store_engineering_fixture', ROOT / 'tests/test_engineering_lifecycle.py')
fixture_module = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture_module)
workflow = fixture_module.workflow
spec = importlib.util.spec_from_file_location('store_manager', SKILLS / 'ct-product-manage-project/scripts/manage.py')
manager = importlib.util.module_from_spec(spec); spec.loader.exec_module(manager)
spec = importlib.util.spec_from_file_location('store_installer', ROOT / 'scripts/skills.py')
installer = importlib.util.module_from_spec(spec); spec.loader.exec_module(installer)


def asset(platform, name):
    return json.loads((SKILLS / f'ct-devops-release-{platform}-app/assets' / name).read_text(encoding='utf-8'))


class StoreReleaseFixture(unittest.TestCase):
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
