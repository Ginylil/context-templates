"""Behavioral checks for development graph and authoritative tracking readback."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
from assembled_catalog import SKILLS
SKILL = SKILLS / 'ct-rnd-plan-development'


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


plan = module(SKILL / 'scripts/plan.py', 'ct_plan_tests')
installer = module(ROOT / 'scripts/skills.py', 'ct_plan_installer')


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.ledger, self.definition, self.value = [json.loads((SKILL / 'assets' / f'example-{key}.json').read_text(encoding="utf-8"))
                                                   for key in ('ledger', 'definition', 'plan')]
        self.args = (self.ledger, self.definition, self.value)

    def live(self):
        payload = plan.prepare(*self.args)
        issues = [{'html_url': f'https://github.com/example/follow-up-notes/issues/{n}',
                   'title': task['title'], 'body': task['body'], 'state': 'open'}
                  for n, task in enumerate(payload['tasks'], 1)]
        receipt = {key: payload[key] for key in ('schema_version', 'project_id', 'plan_id', 'plan_sha256')}
        receipt['issues'] = [{'task_id': task['id'], 'url': issue['html_url']}
                             for task, issue in zip(payload['tasks'], issues)]
        items = [{'id': f'item-{n}', 'isArchived': False, 'content': {'url': issue['html_url']},
                  'fieldValueByName': {'name': 'Backlog'}} for n, issue in enumerate(issues)]
        return receipt, issues, items

    def check_live(self, receipt, issues, items, **kwargs):
        with patch.object(plan, 'gh', return_value=[issues]) as read, patch.object(plan, 'read_project', return_value=items):
            result = plan.verify_tracking(*self.args, receipt, **kwargs)
            self.assertEqual(read.call_args.args[0][0], 'api')
            self.assertIn('GET', read.call_args.args[0])
            return result

    def test_complete_example_deterministic_payload_and_constraint_preservation(self):
        self.assertEqual(plan.validate_plan(*self.args), self.value)
        payload = plan.prepare(*self.args)
        self.assertEqual(payload, plan.prepare(*copy.deepcopy(self.args)))
        for task in payload['tasks']:
            for constraint in self.definition['constraints']:
                self.assertIn(constraint, task['body'])
        self.assertEqual(self.check_live(*self.live())['issue_count'], 2)

    def test_invalid_graphs_and_coverage_fail(self):
        mutations = [lambda p: p['tasks'][0]['depends_on'].append('list-follow-ups'),
                     lambda p: p['tasks'][0]['depends_on'].append('missing'),
                     lambda p: p['tasks'].append(copy.deepcopy(p['tasks'][0])),
                     lambda p: p['tasks'].pop(),
                     lambda p: p['tasks'][0].update(status='done'),
                     lambda p: p['tasks'][0]['acceptance'][0].update(requirement_ids=['missing']),
                     lambda p: p.update(schema_version=True),
                     lambda p: p.update(extra=True),
                     lambda p: p['tracking'].update(project='https://github.com/orgs/example/projects/0'),
                     lambda p: p.update(definition_sha256='stale'),
                     lambda p: p.update(ledger_sha256='stale')]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                value = copy.deepcopy(self.value)
                mutate(value)
                with self.assertRaises(ValueError):
                    plan.validate_plan(self.ledger, self.definition, value)

    def test_cannot_replace_declared_targets_or_drop_constraints(self):
        self.ledger['input']['tracking'] = dict(self.value['tracking'])
        self.definition['tracking'] = dict(self.value['tracking'])
        self.definition['input_sha256'] = plan.digest(self.ledger['input'])
        self.definition['ledger_sha256'] = plan.digest(self.ledger)
        self.value.update(ledger_sha256=plan.digest(self.ledger), definition_sha256=plan.digest(self.definition))
        self.value['tracking']['repository'] = 'other/repo'
        with self.assertRaisesRegex(ValueError, 'cannot replace'):
            plan.validate_plan(*self.args)
        self.definition['constraints'] = []
        with self.assertRaisesRegex(ValueError, 'cannot drop'):
            plan.validate_plan(*self.args)

    def test_blocked_definition_and_restarted_or_over_budget_history_cannot_plan(self):
        self.definition.update(status='blocked', blockers=[{'decision_id': None, 'reason': 'Contradictory source',
                                                         'next_action': 'Resolve with owner'}])
        with self.assertRaisesRegex(ValueError, 'blocked'):
            plan.validate_plan(*self.args)
        self.setUp()
        self.ledger['events'] = []
        with self.assertRaisesRegex(ValueError, 'stale ledger'):
            plan.validate_plan(*self.args)
        self.setUp()
        decisions = [{'id': f'choice-{n}', 'topic': f'Choice {n}', 'depends_on': [],
                      'blocking': True, 'resolution': None} for n in range(9)]
        self.ledger['events'].extend([
            {'id': 'new-decisions', 'type': 'add-decisions', 'decisions': decisions},
            {'id': 'overflow', 'type': 'ask', 'questions': [
                {'id': f'Q{n+3}', 'decision_id': d['id'], 'prompt': d['topic'],
                 'options': [], 'recommended_option': None} for n, d in enumerate(decisions)]}])
        with self.assertRaises(ValueError):
            plan.validate_plan(*self.args)

    def test_stale_receipt_and_missing_duplicate_mismatched_live_evidence_fail(self):
        mutations = [lambda r, i, p: r.update(verified=True),
                     lambda r, i, p: r.update(plan_sha256='old'),
                     lambda r, i, p: r['issues'].pop(),
                     lambda r, i, p: r['issues'].append(copy.deepcopy(r['issues'][0])),
                     lambda r, i, p: r['issues'][0].update(url='https://github.com/other/repo/issues/1'),
                     lambda r, i, p: i.append(copy.deepcopy(i[0])),
                     lambda r, i, p: i.pop(),
                     lambda r, i, p: i[0].update(title='Changed'),
                     lambda r, i, p: i[0].update(body=i[0]['body'].replace('ct-plan-sha256:', 'old:')),
                     lambda r, i, p: i[0].update(state='closed'),
                     lambda r, i, p: i[0].update(pull_request={}),
                     lambda r, i, p: i[0].update(body=12),
                     lambda r, i, p: p.pop(),
                     lambda r, i, p: p.append(copy.deepcopy(p[0])),
                     lambda r, i, p: p[0].update(isArchived=True),
                     lambda r, i, p: p[0].update(fieldValueByName={'name': 'In progress'})]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                receipt, issues, items = self.live()
                mutate(receipt, issues, items)
                with self.assertRaises(ValueError):
                    self.check_live(receipt, issues, items)

    def test_project_readback_pagination_wrong_project_and_missing_access(self):
        def page(more, url=None):
            return {'data': {'organization': {'projectV2': {'url': url or self.value['tracking']['project'],
                    'closed': False, 'items': {'nodes': [], 'pageInfo': {'hasNextPage': more, 'endCursor': 'next'}}}}}}
        for pages in ([page(True)], [page(False, 'wrong')], [{'data': {'organization': None}}],
                      [{'errors': [{'message': 'denied'}]}]):
            with self.subTest(pages=pages), patch.object(plan, 'gh', return_value=pages):
                with self.assertRaises(ValueError):
                    plan.read_project(self.value['tracking']['project'])
        with patch.object(plan, 'gh', return_value=[page(True), page(False)]) as read:
            self.assertEqual(plan.read_project(self.value['tracking']['project']), [])
            self.assertIn('--paginate', read.call_args.args[0])

    def test_ongoing_readback_returns_remote_state_without_resetting_progress(self):
        receipt, issues, items = self.live()
        items[0]['fieldValueByName'] = {'name': 'Done'}
        issues[0]['state'] = 'closed'
        with self.assertRaises(ValueError):
            self.check_live(receipt, issues, items)
        result = self.check_live(receipt, issues, items, require_backlog=False)
        self.assertEqual(result['tasks'][0], {'task_id': self.value['tasks'][0]['id'],
                                            'issue_url': issues[0]['html_url'],
                                            'issue_state': 'closed', 'project_status': 'Done'})
        self.assertEqual(result['tasks'][1]['project_status'], 'Backlog')
        for status in (None, {}, {'name': ''}, {'name': '   '}, {'name': 42}):
            for require_backlog in (True, False):
                with self.subTest(status=status, require_backlog=require_backlog):
                    issues[0]['state'] = 'open'
                    items[0]['fieldValueByName'] = status
                    with self.assertRaises(ValueError):
                        self.check_live(receipt, issues, items, require_backlog=require_backlog)

    def test_ongoing_readback_allows_checkbox_progress_but_not_changed_criteria(self):
        receipt, issues, items = self.live()
        issues[0]['body'] = issues[0]['body'].replace('- [ ] ', '- [x] ')
        self.check_live(receipt, issues, items, require_backlog=False)
        with self.assertRaises(ValueError):
            self.check_live(receipt, issues, items)
        issues[0]['body'] += '\nScope changed without replanning.\n'
        with self.assertRaises(ValueError):
            self.check_live(receipt, issues, items, require_backlog=False)

    def test_unavailable_live_api_never_passes(self):
        for side_effect in (FileNotFoundError('gh missing'), subprocess.TimeoutExpired('gh', 45)):
            with patch.object(plan.subprocess, 'run', side_effect=side_effect):
                with self.assertRaisesRegex(ValueError, 'unavailable'):
                    plan.verify_tracking(*self.args, self.live()[0])
        with patch.object(plan.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'denied')):
            with self.assertRaisesRegex(ValueError, 'failed'):
                plan.verify_tracking(*self.args, self.live()[0])
        for response in (subprocess.CompletedProcess([], 0, 'not-json', ''),
                         subprocess.CompletedProcess([], 0, '{"errors":[{"message":"denied"}]}', '')):
            with patch.object(plan.subprocess, 'run', return_value=response):
                with self.assertRaises(ValueError):
                    plan.verify_tracking(*self.args, self.live()[0])

    def test_installed_standalone_cli_for_every_agent_and_exclusive_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            standalone = work / 'catalog'
            shutil.copytree(SKILL, standalone / 'skills' / SKILL.name)
            for agent in installer.TARGETS:
                home = work / agent
                with contextlib.redirect_stdout(io.StringIO()):
                    installer.install(standalone, home, [agent], [SKILL.name], False)
                installed = home / installer.TARGETS[agent] / SKILL.name
                inputs = [str(installed / 'assets' / f'example-{key}.json') for key in ('ledger', 'definition', 'plan')]
                command = [sys.executable, str(installed / 'scripts/plan.py')]
                checked = subprocess.run(command + ['validate', *inputs], cwd=work, capture_output=True, text=True)
                self.assertEqual(checked.returncode, 0, checked.stderr)
                output = work / f'{agent}.json'
                prepared = subprocess.run(command + ['prepare', *inputs, '--output', str(output)], cwd=work, capture_output=True, text=True)
                self.assertEqual(prepared.returncode, 0, prepared.stderr)
                before = output.read_bytes()
                refused = subprocess.run(command + ['prepare', *inputs, '--output', str(output)], cwd=work, capture_output=True, text=True)
                self.assertEqual(refused.returncode, 1)
                self.assertEqual(output.read_bytes(), before)

    def test_bundled_definition_validator_matches_source(self):
        self.assertEqual((SKILL / 'scripts/definition.py').read_bytes(),
                         (SKILLS / 'ct-product-define-project/scripts/project.py').read_bytes())


if __name__ == '__main__':
    unittest.main()
