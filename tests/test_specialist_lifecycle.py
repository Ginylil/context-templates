"""Domain gate tests for assessment, release, operations and launch contracts."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
from assembled_catalog import SKILLS
NAMES = ['ct-qa-test-user-flows', 'ct-security-review-project', 'ct-devops-release-project',
         'ct-devops-maintain-project', 'ct-product-review-product',
         'ct-marketing-research-market', 'ct-marketing-launch-product']
SPEC = importlib.util.spec_from_file_location('ct_specialist_workflow', SKILLS / 'ct-product-manage-project/scripts/workflow.py')
workflow = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workflow)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def asset(name, filename):
    return read(SKILLS / name / 'assets' / filename)


class SpecialistLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.ledger = read(SKILLS / 'ct-product-define-project/assets/example-ledger.json')
        self.definition = read(SKILLS / 'ct-product-define-project/assets/example-definition.json')
        self.ledger_ref = self.write('ledger.json', self.ledger)
        self.definition_ref = self.write('definition.json', self.definition)
        self.source_ref = self.write('source.txt', 'Synthetic local fixture: review and release authorization are limited to this test.')
        self.artifact_ref = self.write('report.txt', 'Synthetic local evidence fixture. No live service was contacted.')
        # Local disposable Git history binds the release to an actual source revision.
        self.repo = self.base / 'repo'
        self.repo.mkdir()
        (self.repo / 'source.txt').write_text('Synthetic fixture source.\n', encoding='utf-8')
        for args in [['init', '-q'], ['add', 'source.txt'],
                     ['-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                      'commit', '-qm', 'Synthetic release fixture']]:
            subprocess.run(['git', *args], cwd=self.repo, check=True, capture_output=True)
        self.revision = workflow.revision(self.repo)
        # Run an actual harmless command; proof output is outside the measured repository.
        workflow.record([sys.executable, '-c', 'print("fixture build complete")'], self.repo,
                        self.base / 'build.json', timeout=10)
        self.command_ref = {'path':'build.json','sha256':hashlib.sha256((self.base/'build.json').read_bytes()).hexdigest()}

    def write(self, name, value):
        path = self.base / name
        path.write_text(value if isinstance(value, str) else json.dumps(value), encoding='utf-8')
        return {'path':name, 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

    def case(self, name):
        policy = asset(name, 'contract.json')
        intake = asset(name, 'example-input.json')
        intake.update(ledger=self.ledger_ref, definition=self.definition_ref,
                      sources=[{'id':'decision-source', **self.source_ref}])
        output = asset(name, 'example-output.json')
        output.update(status='ready', blockers=[], summary='Bounded synthetic fixture assessment complete.',
                      constraints=list(dict.fromkeys(intake['constraints'] + self.definition['constraints'])),
                      evidence=[{'id':'report','kind':'artifact','reference':self.artifact_ref},
                                {'id':'build','kind':'command','reference':self.command_ref}])
        result = output['result']
        if name == 'ct-qa-test-user-flows':
            intake['inputs']['journeys'] = [{'id':'notes','actor':'Owner','goal':'Manage private notes',
                'requirement_ids':[x['id'] for x in self.definition['success_criteria']]}]
            result.update(candidate_revision=intake['inputs']['candidate_revision'], verdict='passed',
                scenarios=[{'id':'complete-notes','journey_id':'notes',
                            'requirement_ids':[x['id'] for x in self.definition['success_criteria']],
                            'steps':['Run a synthetic complete journey.'],'expected':'Criteria hold.',
                            'actual':'Synthetic fixture assertion passed.','status':'passed','evidence_ids':['report']}])
        elif name == 'ct-security-review-project':
            result['assessed_areas']=[{'id':'auth','area':'Authorization','status':'limited',
                                      'evidence_ids':['report'],'limitations':['Synthetic fixture only.']}]
        elif name == 'ct-devops-release-project':
            intake['repository']={'path':str(self.repo),'revision':self.revision,'working_tree_sha256':workflow.tree_digest(self.repo)}
            intake['inputs']['candidate_revision']=self.revision
            result.update(candidate_revision=intake['inputs']['candidate_revision'],build_check='build',
                          checks=[{'id':'build','name':'Build','status':'passed','evidence_ids':['build']}],
                          outcome='candidate-prepared')
        elif name == 'ct-devops-maintain-project':
            result['coverage']=[{'id':x,'area':x,'status':'unavailable','evidence_ids':['report'],
                                 'observed_at':'2026-10-01T12:00:00+00:00','limitations':['Synthetic fixture only.']}
                                for x in ['spend','changes','security','health','failures','incidents','recovery']]
        elif name == 'ct-product-review-product':
            result['observations']=[{'id':'activation','claim':'Source records a first-session interruption.',
                'source_ids':['decision-source'],'evidence_ids':['report'],'confidence':'low',
                'limitations':['Synthetic sample.']}]
        elif name == 'ct-marketing-research-market':
            result['claims']=[{'id':'alternative','claim':'Source describes a manual alternative.',
                'source_ids':['decision-source'],'evidence_ids':['report'],'source_date':'2026-10-01',
                'confidence':'low','limitations':['Synthetic sample.']}]
        elif name == 'ct-marketing-launch-product':
            result.update(product_revision=intake['inputs']['product_revision'],outcome='drafts-prepared',
                assets=[{'id':'landing','channel':'Owned product website','audience':'Freelancers',
                         'message':'Record your own client notes.','call_to_action':'Read the preview.',
                         'claim_sources':['decision-source'],'artifact':'report'}],
                measurement=[{'id':'visit','event':'Preview visit','baseline':'Unknown','target':'Define after baseline.',
                              'window':'First seven days after an authorized launch.','limitations':['No launch executed.']}])
        output['input_sha256']=workflow.digest(intake)
        return policy, intake, output

    def validate(self, case):
        return workflow.validate_output(*case, base=self.base)

    def test_packaged_blocked_examples_are_honest_and_valid(self):
        for name in NAMES:
            with self.subTest(name=name):
                policy, intake, output = (asset(name, x) for x in
                                         ['contract.json','example-input.json','example-output.json'])
                workflow.validate_input(policy, intake, self.base)
                workflow.validate_output(policy, intake, output, self.base)
                self.assertEqual(output['status'], 'blocked')

    def test_all_specialist_ready_assessments_validate_with_real_local_files(self):
        for name in NAMES:
            with self.subTest(name=name):
                self.validate(self.case(name))

    def test_release_rejects_failed_build_and_fake_phase(self):
        case=self.case('ct-devops-release-project')
        case[2]['result']['outcome']='production-verified'
        with self.assertRaises(ValueError): self.validate(case)
        case=self.case('ct-devops-release-project')
        workflow.record([sys.executable,'-c','raise SystemExit(3)'],self.repo,self.base/'failed.json',10)
        case[2]['evidence'][1]['reference']={'path':'failed.json','sha256':hashlib.sha256((self.base/'failed.json').read_bytes()).hexdigest()}
        with self.assertRaises(ValueError): self.validate(case)

    def test_release_requires_repository_bound_candidate_and_current_source(self):
        case=self.case('ct-devops-release-project')
        case[1]['repository']=None
        case[2]['input_sha256']=workflow.digest(case[1])
        with self.assertRaises(ValueError): self.validate(case)
        case=self.case('ct-devops-release-project')
        case[1]['inputs']['candidate_revision']='unrelated-candidate'
        case[2]['result']['candidate_revision']='unrelated-candidate'
        case[2]['input_sha256']=workflow.digest(case[1])
        with self.assertRaises(ValueError): self.validate(case)
        case=self.case('ct-devops-release-project')
        (self.repo/'source.txt').write_text('Changed after successful build.',encoding='utf-8')
        with self.assertRaises(ValueError): self.validate(case)

    def test_production_requires_authorization_acceptance_and_readback(self):
        case=self.case('ct-devops-release-project')
        case[1]['inputs']['target_stage']='production'
        case[2]['input_sha256']=workflow.digest(case[1])
        case[2]['result']['outcome']='production-verified'
        with self.assertRaises(ValueError): self.validate(case)
        case[2]['result'].update(authorization_source='decision-source',production_readback='report')
        with self.assertRaises(ValueError): self.validate(case)
        case[2]['result']['staging_acceptance']='decision-source'
        case[2]['result']['staging_readback']='report'
        self.validate(case)

    def test_launch_drafts_cannot_claim_publication(self):
        case=self.case('ct-marketing-launch-product')
        case[2]['result']['outcome']='publication-verified'
        with self.assertRaises(ValueError): self.validate(case)

    def test_launch_publish_requires_explicit_source_and_live_readback(self):
        case=self.case('ct-marketing-launch-product')
        case[1]['inputs']['mode']='publish'
        case[2]['input_sha256']=workflow.digest(case[1])
        case[2]['result']['outcome']='publication-verified'
        with self.assertRaises(ValueError): self.validate(case)
        case[2]['result'].update(authorization_source='decision-source', live_readback='report',
            publications=[{'id':'published','channel':'Owned product website','asset_id':'missing',
                           'idempotency_key':'launch-fixture-once','url':'https://example.invalid/launch','evidence':'report'}])
        with self.assertRaises(ValueError): self.validate(case)
        case[2]['result']['publications'][0]['asset_id']='landing'
        self.validate(case)

    def test_launch_prepare_rejects_claimed_publications(self):
        case=self.case('ct-marketing-launch-product')
        case[2]['result']['publications']=[{'id':'published','channel':'Owned product website',
            'asset_id':'landing','idempotency_key':'synthetic-once','url':'https://example.invalid/launch','evidence':'report'}]
        with self.assertRaises(ValueError): self.validate(case)

    def test_product_recommendations_must_link_real_observations(self):
        case=self.case('ct-product-review-product')
        case[2]['result']['opportunities']=[{'id':'faster-start','problem':'Setup interrupts first use.',
            'audience':'Freelancers','supporting_observations':['not-observed'],
            'proposed_change':'Test a shorter setup.','success_measure':'First useful note saved.',
            'counter_metric':'Failed authentication rate.','confidence':'low'}]
        with self.assertRaises(ValueError): self.validate(case)
        case[2]['result']['opportunities'][0]['supporting_observations']=['activation']
        self.validate(case)

    def test_market_positioning_must_link_real_claims(self):
        case=self.case('ct-marketing-research-market')
        case[2]['result']['positioning_options']=[{'id':'manual-notes','audience':'Freelancers',
            'problem':'Follow-up information is scattered.','promise':'Keep notes together.',
            'supporting_claims':['not-sourced'],'validation_needed':'Customer interviews.'}]
        with self.assertRaises(ValueError): self.validate(case)
        case[2]['result']['positioning_options'][0]['supporting_claims']=['alternative']
        self.validate(case)

    def test_qa_requires_complete_criterion_coverage(self):
        case=self.case('ct-qa-test-user-flows')
        case[2]['result']['scenarios'][0]['requirement_ids'].pop()
        with self.assertRaises(ValueError): self.validate(case)

    def test_qa_preserves_requested_environment_and_journeys(self):
        case=self.case('ct-qa-test-user-flows')
        case[2]['result']['environment']='production'
        with self.assertRaises(ValueError): self.validate(case)
        case=self.case('ct-qa-test-user-flows')
        case[2]['result']['scenarios'][0]['journey_id']='not-requested'
        with self.assertRaises(ValueError): self.validate(case)

    def test_qa_cannot_claim_unrelated_revision_or_pass_failed_command(self):
        case=self.case('ct-qa-test-user-flows')
        case[1]['repository']={'path':str(self.repo),'revision':self.revision,'working_tree_sha256':workflow.tree_digest(self.repo)}
        case[1]['inputs']['candidate_revision']='0'*40
        case[2]['result']['candidate_revision']='0'*40
        case[2]['input_sha256']=workflow.digest(case[1])
        with self.assertRaises(ValueError): self.validate(case)
        case=self.case('ct-qa-test-user-flows')
        workflow.record([sys.executable,'-c','raise SystemExit(3)'],self.repo,self.base/'qa-fail.json',10)
        case[2]['evidence'].append({'id':'failed-flow','kind':'command','reference':{'path':'qa-fail.json','sha256':workflow.file_digest(self.base/'qa-fail.json')}})
        case[2]['result']['scenarios'][0]['evidence_ids']=['failed-flow']
        with self.assertRaises(ValueError): self.validate(case)

    def test_staging_deployment_requires_readback_beyond_build(self):
        case=self.case('ct-devops-release-project')
        case[1]['inputs']['target_stage']='staging'
        case[2]['input_sha256']=workflow.digest(case[1])
        case[2]['result']['outcome']='staging-deployed'
        with self.assertRaises(ValueError): self.validate(case)
        case[2]['result']['staging_readback']='report'
        self.validate(case)

    def test_qa_failed_execution_is_not_a_passed_verdict(self):
        case=self.case('ct-qa-test-user-flows')
        case[2]['result']['scenarios'][0]['status']='failed'
        with self.assertRaises(ValueError): self.validate(case)
        case[2]['result']['verdict']='failed'
        self.validate(case)  # Completed failure assessment is valid; acceptance is not implied.

    def test_maintenance_cannot_omit_unavailable_coverage(self):
        case=self.case('ct-devops-maintain-project')
        case[2]['result']['coverage'].pop()
        with self.assertRaises(ValueError): self.validate(case)

    def test_supported_claims_cannot_reference_missing_sources(self):
        for name, field in [('ct-product-review-product','observations'),('ct-marketing-research-market','claims')]:
            with self.subTest(name=name):
                case=self.case(name)
                case[2]['result'][field][0]['source_ids']=['unavailable']
                with self.assertRaises(ValueError): self.validate(case)

    def test_security_rejects_invented_evidence_and_empty_ready_review(self):
        case=self.case('ct-security-review-project')
        case[2]['result']['assessed_areas'][0]['evidence_ids']=['unavailable']
        with self.assertRaises(ValueError): self.validate(case)
        case=self.case('ct-security-review-project')
        case[2]['result']['assessed_areas']=[]
        with self.assertRaises(ValueError): self.validate(case)

    def test_hash_drift_and_dropped_constraints_are_rejected(self):
        case=self.case('ct-devops-maintain-project')
        (self.base/'report.txt').write_text('Changed after reference capture.',encoding='utf-8')
        with self.assertRaises(ValueError): self.validate(case)
        case=self.case('ct-devops-maintain-project')
        case[2]['constraints']=[]
        with self.assertRaises(ValueError): self.validate(case)


if __name__ == '__main__':
    unittest.main()
