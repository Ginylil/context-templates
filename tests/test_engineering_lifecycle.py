"""Domain-specific lifecycle contract checks; fixtures are not product acceptance."""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / 'skills'
NAMES = (
    'ct-rnd-design-architecture', 'ct-rnd-set-up-project', 'ct-rnd-build-feature',
    'ct-rnd-fix-bug', 'ct-rnd-review-code', 'ct-rnd-improve-agent-setup',
    'ct-design-build-interface', 'ct-qa-plan-tests',
)
_spec = importlib.util.spec_from_file_location('ct_engineering_workflow', SKILLS / 'ct-product-manage-project/scripts/workflow.py')
workflow = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(workflow)


def asset(name, file):
    return json.loads((SKILLS / name / 'assets' / file).read_text(encoding='utf-8'))


class EngineeringLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.ledger = asset('ct-product-define-project', 'example-ledger.json')
        self.definition = asset('ct-product-define-project', 'example-definition.json')
        self.requirements = [x['id'] for x in self.definition['success_criteria']]
        self.ledger_ref = self.write('ledger.json', self.ledger)
        self.definition_ref = self.write('definition.json', self.definition)
        self.repository = self.base / 'repository'
        self.repository.mkdir()
        self.evidence = []
        self.source_ref = self.write('source.txt', 'Synthetic test source; not live project evidence.\n')
        self.artifact('deliverable', 'A concrete synthetic test deliverable.\n')
        (self.repository / 'check.py').write_text('from pathlib import Path\nraise SystemExit(0 if Path("fixed").exists() else 1)\n', encoding='utf-8')
        subprocess.run(['git', 'init', '-q', str(self.repository)], check=True, capture_output=True)
        subprocess.run(['git', 'add', 'check.py'], cwd=self.repository, check=True, capture_output=True)
        subprocess.run(['git', '-c', 'user.name=Contract Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture'], cwd=self.repository, check=True, capture_output=True)
        self.revision = workflow.revision(self.repository)
        argv = [sys.executable, 'check.py']
        self.proof('before', argv)
        (self.repository / 'fixed').write_text('fixed\n', encoding='utf-8')
        self.proof('after', argv)
        self.proof('check', [sys.executable, '-c', 'assert 2 + 2 == 4'])

    def write(self, name, value):
        path = self.base / name
        path.write_text(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False), encoding='utf-8')
        return {'path': name, 'sha256': workflow.file_digest(path)}

    def artifact(self, key, value):
        self.evidence.append({'id': key, 'kind': 'artifact', 'reference': self.write(key + '.txt', value)})

    def proof(self, key, argv):
        path = self.base / (key + '.json')
        workflow.record(argv, self.repository, path)
        self.evidence.append({'id': key, 'kind': 'command', 'reference': {'path': path.name, 'sha256': workflow.file_digest(path)}})

    def ready(self, name):
        policy = asset(name, 'contract.json')
        value = asset(name, 'example-input.json')
        value['repository'] = {'path': 'repository', 'revision': self.revision, 'working_tree_sha256': workflow.tree_digest(self.repository)}
        if 'candidate_revision' in value['inputs']:
            value['inputs']['candidate_revision'] = self.revision
        value['ledger'] = self.ledger_ref
        value['definition'] = self.definition_ref
        value['sources'] = [{'id': 'source', **self.source_ref}]
        output = asset(name, 'example-output.json')
        output.update(status='ready', blockers=[], evidence=copy.deepcopy(self.evidence), summary='Synthetic contract test with real local command execution.')
        output['constraints'] += self.definition['constraints']
        result = output['result']
        if 'candidate_revision' in result:
            result['candidate_revision'] = self.revision
        if name == 'ct-rnd-design-architecture':
            result.update(components=[{'id': 'web', 'responsibility': 'Authenticate and manage notes.', 'owned_data': ['notes']},
                                      {'id': 'storage', 'responsibility': 'Persist owner-scoped records.', 'owned_data': ['stored notes']}],
                          interfaces=[{'id': 'save', 'from': 'web', 'to': 'storage', 'contract': 'Owner-scoped note write.', 'failure_behavior': 'Return retryable persistence failure.'}],
                          requirement_map=[{'id': 'all-requirements', 'requirement_ids': self.requirements, 'design': 'Owner-scoped persistence and ordered reads.'}],
                          decisions=[{'id': 'single-service', 'choice': 'One web service.', 'alternatives': ['Separate services'], 'rationale': 'A single owner and small workload.', 'source_ids': ['source']}],
                          design_artifact='deliverable')
        elif name == 'ct-rnd-set-up-project':
            value['repository'] = None
            value['inputs']['target_path'] = 'repository'
            result['target_path'] = 'repository'
            value['inputs']['commands'].update(setup=[sys.executable, '-c', 'assert 2 + 2 == 4'], test=[sys.executable, 'check.py'], build=[sys.executable, '-c', 'assert 2 + 2 == 4'])
            result.update(created_paths=['app.py'], setup_check='check', test_check='after', build_check='check', ci_artifact='deliverable', instruction_artifact='deliverable')
        elif name == 'ct-rnd-build-feature':
            value['inputs'].update(task_id='task-save-note', requirement_ids=[self.requirements[0]],
                acceptance=[{'id': 'save-note', 'requirement_ids': [self.requirements[0]],
                             'scenario': 'Save and reload a note.', 'verification': 'Run the persistence regression.'}])
            result.update(task_id='task-save-note', changes=[{'path': 'app.py', 'reason': 'Save notes.'}],
                          scenarios=[{'id': 'save-note', 'requirement_ids': [self.requirements[0]], 'status': 'passed', 'evidence_ids': ['after']}],
                          test_check='after', build_check='check')
        elif name == 'ct-rnd-fix-bug':
            value['inputs']['reproduction_argv'] = [sys.executable, 'check.py']
            result.update(root_cause='A missing guard allowed empty values.', changes=[{'path': 'app.py', 'reason': 'Reject empty notes.'}],
                          before_check='before', after_check='after', related_check='check')
        elif name == 'ct-rnd-review-code':
            value['inputs']['change_source'] = 'source'
            result.update(reviewed_source='source', reviewed_files=[{'path': 'app.py', 'source_id': 'source'}],
                          assessments=[{'area': 'validation', 'conclusion': 'The reviewed guard rejects empty values.', 'evidence_ids': ['deliverable']}], review_artifact='deliverable')
        elif name == 'ct-rnd-improve-agent-setup':
            value['inputs'].update(observed_failure='source', verification_argv=[sys.executable, 'check.py'])
            result.update(observed_source='source', failure_mechanism='A stale documented invocation.', changes=[{'path': 'AGENTS.md', 'reason': 'Correct invocation.'}],
                          before_check='before', after_check='after', instruction_artifact='deliverable')
        elif name == 'ct-design-build-interface':
            value['inputs']['requirement_ids'] = self.requirements
            result.update(design_rationale='Make the next client action easy to scan.',
                          surfaces=[{'id': 'screen-' + v['id'], 'requirement_ids': self.requirements, 'viewport_id': v['id'],
                                     'before': None, 'after': 'deliverable', 'interaction_check': 'after', 'status': 'passed'} for v in value['inputs']['viewports']], build_check='check')
        elif name == 'ct-qa-plan-tests':
            result.update(scenarios=[{'id': 'private-notes', 'requirement_ids': self.requirements, 'risk': 'Private records leak across owners.',
                                     'preconditions': ['Two isolated test users.'], 'steps': ['Create a note as the owner.', 'Attempt direct access as the other user.'],
                                     'expected': 'Only the owner can read the persisted note.', 'surface': 'Browser and API integration',
                                     'test_data': 'Two synthetic accounts and one secret-free note.', 'cleanup': 'Remove records using test fixture cleanup.'}],
                          execution_order=[{'scenario_id': 'private-notes'}], test_plan_artifact='deliverable')
        output['input_sha256'] = workflow.digest(value)
        return policy, value, output

    def check(self, values):
        return workflow.validate_output(*values, base=self.base)

    def reject(self, values, message):
        with self.assertRaisesRegex(ValueError, message):
            self.check(values)

    def test_all_examples_are_self_contained_blocked_reports(self):
        for name in NAMES:
            with self.subTest(skill=name):
                folder = SKILLS / name / 'assets'
                workflow.validate_input(asset(name, 'contract.json'), asset(name, 'example-input.json'), base=folder)
                workflow.validate_output(asset(name, 'contract.json'), asset(name, 'example-input.json'), asset(name, 'example-output.json'), base=folder)

    def test_each_domain_accepts_its_complete_ready_report(self):
        for name in NAMES:
            with self.subTest(skill=name):
                self.check(self.ready(name))

    def test_architecture_rejects_unknown_interface_component(self):
        values = self.ready('ct-rnd-design-architecture')
        values[2]['result']['interfaces'][0]['to'] = 'unowned-database'
        self.reject(values, 'unknown target')

    def test_architecture_rejects_unmapped_requirement(self):
        values = self.ready('ct-rnd-design-architecture')
        values[2]['result']['requirement_map'][0]['requirement_ids'] = self.requirements[:1]
        self.reject(values, 'coverage: missing')

    def test_architecture_requires_actual_design_artifact(self):
        values = self.ready('ct-rnd-design-architecture')
        values[2]['result']['design_artifact'] = None
        self.reject(values, 'nonempty')

    def test_setup_requires_real_successful_build_command(self):
        values = self.ready('ct-rnd-set-up-project')
        values[2]['result']['build_check'] = 'before'
        self.reject(values, 'exit code')
        values[2]['result']['build_check'] = 'deliverable'
        self.reject(values, 'recorded command')

    def test_setup_requires_setup_and_ci_evidence(self):
        values = self.ready('ct-rnd-set-up-project')
        values[2]['result']['setup_check'] = None
        self.reject(values, 'missing evidence')
        values[2]['result']['setup_check'] = 'check'
        values[2]['result']['ci_artifact'] = None
        self.reject(values, 'nonempty')

    def test_setup_cannot_change_target_directory(self):
        values = self.ready('ct-rnd-set-up-project')
        values[2]['result']['target_path'] = '/some-other-project'
        self.reject(values, 'changed the requested target')

    def test_feature_covers_only_its_selected_requirement_subset(self):
        values = self.ready('ct-rnd-build-feature')
        context = self.check(values)
        self.assertEqual(len(context['requirement']), 3)
        self.assertEqual(len(values[1]['inputs']['requirement_ids']), 1)

    def test_feature_rejects_failed_scenario_even_with_passing_build(self):
        values = self.ready('ct-rnd-build-feature')
        values[2]['result']['scenarios'][0]['status'] = 'failed'
        self.reject(values, 'all-status')

    def test_feature_rejects_mismatched_task_identity(self):
        values = self.ready('ct-rnd-build-feature')
        values[2]['result']['task_id'] = 'different-task'
        self.reject(values, 'changed the requested target')

    def test_feature_rejects_missing_selected_requirement_coverage(self):
        values = self.ready('ct-rnd-build-feature')
        values[1]['inputs']['requirement_ids'] = self.requirements
        values[2]['input_sha256'] = workflow.digest(values[1])
        self.reject(values, 'coverage: missing')

    def test_bug_requires_original_failure_and_same_regression_command(self):
        values = self.ready('ct-rnd-fix-bug')
        values[2]['result']['before_check'] = 'after'
        self.reject(values, 'exit code')
        values[2]['result']['before_check'] = 'before'
        values[2]['result']['after_check'] = 'check'
        self.reject(values, 'same command')

    def test_review_can_report_no_findings_but_requires_reviewed_source(self):
        values = self.ready('ct-rnd-review-code')
        self.check(values)
        self.assertEqual(values[2]['result']['findings'], [])
        values[2]['result']['reviewed_files'][0]['source_id'] = 'not-inspected'
        self.reject(values, 'unknown source')

    def test_review_cannot_silently_change_candidate(self):
        values = self.ready('ct-rnd-review-code')
        values[2]['result']['candidate_revision'] = 'different-revision'
        self.reject(values, 'changed the requested target')

    def test_review_without_report_is_incomplete(self):
        values = self.ready('ct-rnd-review-code')
        values[2]['result']['review_artifact'] = None
        self.reject(values, 'nonempty')

    def test_agent_setup_requires_comparable_before_after_execution(self):
        values = self.ready('ct-rnd-improve-agent-setup')
        values[2]['result']['after_check'] = 'check'
        self.reject(values, 'same command')

    def test_agent_setup_requires_bound_observed_failure(self):
        values = self.ready('ct-rnd-improve-agent-setup')
        values[1]['inputs']['observed_failure'] = None
        values[2]['input_sha256'] = workflow.digest(values[1])
        values[2]['result']['observed_source'] = None
        self.reject(values, 'nonempty')

    def test_interface_rejects_missing_or_mismatched_viewport(self):
        values = self.ready('ct-design-build-interface')
        values[2]['result']['surfaces'][0]['viewport_id'] = 'unreviewed-tablet'
        self.reject(values, 'unknown target')
        values = self.ready('ct-design-build-interface')
        values[2]['result']['viewports'][0]['width'] = 1024
        self.reject(values, 'changed the requested target')

    def test_interface_requires_capture_and_interaction_evidence(self):
        values = self.ready('ct-design-build-interface')
        values[2]['result']['surfaces'][0]['after'] = 'missing-capture'
        self.reject(values, 'unknown evidence')

    def test_feature_cannot_skip_planned_acceptance_scenarios(self):
        values = self.ready('ct-rnd-build-feature')
        values[1]['inputs']['acceptance'].append({'id': 'reload-note',
            'requirement_ids': [self.requirements[0]], 'scenario': 'Reload the saved note.',
            'verification': 'Reload in a browser.'})
        values[2]['input_sha256'] = workflow.digest(values[1])
        self.reject(values, 'cover-target')

    def test_test_plan_requires_expected_requirement_coverage(self):
        values = self.ready('ct-qa-plan-tests')
        values[2]['result']['scenarios'][0]['requirement_ids'] = self.requirements[:1]
        self.reject(values, 'coverage: missing')

    def test_test_execution_order_cannot_reference_unknown_scenario(self):
        values = self.ready('ct-qa-plan-tests')
        values[2]['result']['execution_order'][0]['scenario_id'] = 'missing-test'
        self.reject(values, 'cover-target')

    def test_duplicate_test_scenario_identity_is_rejected(self):
        values = self.ready('ct-qa-plan-tests')
        values[2]['result']['scenarios'] *= 2
        self.reject(values, 'duplicate id')

    def test_ready_cannot_omit_required_definition_or_drop_constraints(self):
        values = self.ready('ct-rnd-set-up-project')
        values[1]['definition'] = None
        values[2]['input_sha256'] = workflow.digest(values[1])
        self.reject(values, 'ready project definition')
        values = self.ready('ct-rnd-set-up-project')
        values[2]['constraints'] = values[1]['constraints']
        self.reject(values, 'drop constraints')

    def test_interface_cannot_skip_a_requested_viewport(self):
        values = self.ready('ct-design-build-interface')
        values[2]['result']['surfaces'].pop()
        self.reject(values, 'cover-target')

    def test_bug_cannot_substitute_a_different_requested_regression(self):
        values = self.ready('ct-rnd-fix-bug')
        values[1]['inputs']['reproduction_argv'] = [sys.executable, 'other_check.py']
        values[2]['input_sha256'] = workflow.digest(values[1])
        self.reject(values, 'command-matches-input')

    def test_setup_cannot_pass_with_a_different_build_invocation(self):
        values = self.ready('ct-rnd-set-up-project')
        values[1]['inputs']['commands']['build'] = [sys.executable, 'build.py']
        values[2]['input_sha256'] = workflow.digest(values[1])
        self.reject(values, 'command-matches-input')

    def test_agent_setup_cannot_substitute_a_different_verification(self):
        values = self.ready('ct-rnd-improve-agent-setup')
        values[1]['inputs']['verification_argv'] = [sys.executable, 'unrelated.py']
        values[2]['input_sha256'] = workflow.digest(values[1])
        self.reject(values, 'command-matches-input')

    def test_test_plan_cannot_omit_a_scenario_from_execution_order(self):
        values = self.ready('ct-qa-plan-tests')
        values[2]['result']['execution_order'] = []
        self.reject(values, 'cover-target')

    def test_candidate_cannot_claim_a_revision_other_than_inspected_head(self):
        values = self.ready('ct-rnd-build-feature')
        values[1]['inputs']['candidate_revision'] = '0' * 40
        values[2]['result']['candidate_revision'] = '0' * 40
        values[2]['input_sha256'] = workflow.digest(values[1])
        self.reject(values, 'repository-revision')

    def test_passing_check_becomes_stale_after_source_changes(self):
        values = self.ready('ct-rnd-build-feature')
        (self.repository / 'check.py').write_text('raise SystemExit(0)\n', encoding='utf-8')
        self.reject(values, 'working tree changed')

    def test_setup_receipts_must_run_in_requested_target_directory(self):
        values = self.ready('ct-rnd-set-up-project')
        (self.base / 'different-repository').mkdir()
        values[1]['inputs']['target_path'] = 'different-repository'
        values[2]['result']['target_path'] = 'different-repository'
        values[2]['input_sha256'] = workflow.digest(values[1])
        self.reject(values, 'command-cwd-input')

    def test_changed_evidence_bytes_are_rejected(self):
        values = self.ready('ct-rnd-review-code')
        (self.base / 'deliverable.txt').write_text('Changed after binding.\n', encoding='utf-8')
        self.reject(values, 'stale or mismatched digest')


if __name__ == '__main__':
    unittest.main()
