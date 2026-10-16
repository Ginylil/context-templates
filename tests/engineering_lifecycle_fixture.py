"""Test-free engineering lifecycle fixtures shared by contract suites."""
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
from assembled_catalog import SKILLS
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


class EngineeringLifecycleFixture(unittest.TestCase):
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
