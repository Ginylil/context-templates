"""Input/output policy and negative controls for next-session handoffs."""
import copy
import datetime as dt
from pathlib import Path
from unittest.mock import patch

from session_handoff_fixture import HandoffFixture, checks, handoff


class HandoffTests(HandoffFixture):
    def test_synthetic_examples_validate_and_render_uncertainty(self):
        self.validate()
        prompt = handoff.render(self.intake, self.output, self.base)
        for text in (self.output['objective'], str(self.base / 'example-source.md'),
                     'Unverified state', 'Workspace is unverified', 'not new authorization',
                     self.intake['constraints'][1]):
            self.assertIn(text, prompt)

    def test_source_drift_and_stale_input_binding_are_rejected(self):
        self.intake['request'] += ' Changed scope.'
        with self.assertRaisesRegex(ValueError, 'stale or different input'):
            self.validate()
        self.bind()
        (self.base / 'example-source.md').write_text('Changed evidence.', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'stale or mismatched digest'):
            self.validate()

    def test_workspace_requires_an_existing_absolute_directory(self):
        for workspace in ('relative/workspace', str(self.base / 'missing'), False):
            self.intake['scope']['workspace'] = workspace
            with self.subTest(workspace=workspace), self.assertRaises(ValueError):
                checks.validate_input(self.intake, self.base)
        self.intake['scope']['workspace'] = str(self.base)
        self.bind()
        self.validate()

    def test_sources_must_include_the_user_request_not_only_repository_evidence(self):
        self.intake['sources'][0]['kind'] = 'artifact'
        with self.assertRaisesRegex(ValueError, 'user-request/conversation source'):
            checks.validate_input(self.intake, self.base)

    def test_constraints_and_selected_action_cannot_be_dropped(self):
        self.output['constraints'] = []
        with self.assertRaisesRegex(ValueError, 'Preserve all input constraints'):
            self.validate()
        self.output['constraints'] = copy.deepcopy(self.intake['constraints'])
        self.output['objective'] = 'Implement and merge a different feature.'
        with self.assertRaisesRegex(ValueError, 'selected next action'):
            self.validate()

    def test_unchecked_sources_cannot_support_verified_claims_or_disappear(self):
        self.output['verified_state'][0]['source_ids'] = ['remote']
        with self.assertRaisesRegex(ValueError, 'Unverified source'):
            self.validate()
        self.output['verified_state'][0]['source_ids'] = ['request']
        self.output['unverified_state'] = []
        with self.assertRaisesRegex(ValueError, 'Carry every unverified source'):
            self.validate()

    def test_unknown_duplicate_and_malformed_records_are_rejected(self):
        original = copy.deepcopy(self.intake)
        for mutate in (lambda: self.intake.update(schema_version=True),
                       lambda: self.intake.update(extra='unrecognized'),
                       lambda: self.intake['sources'].append(copy.deepcopy(self.intake['sources'][0])),
                       lambda: self.intake['sources'][0].update(id=[]),
                       lambda: self.intake['sources'][0]['reference'].update(sha256='copied-digest'),
                       lambda: self.intake['sources'][1].update(checked_at='2026-01-01T00:00:00Z')):
            self.intake = copy.deepcopy(original)
            mutate()
            with self.assertRaises(ValueError):
                checks.validate_input(self.intake, self.base)
        self.intake = original
        self.output['read_first'][0]['source_id'] = 'unknown'
        with self.assertRaisesRegex(ValueError, 'Unknown source reference'):
            self.validate()

    def test_naive_invalid_and_future_timestamps_are_rejected(self):
        for value in ('2026-01-01', 'not-a-time',
                      (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)).isoformat()):
            self.intake['sources'][0]['checked_at'] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'checked_at'):
                checks.validate_input(self.intake, self.base)

    def test_blocked_handoff_requires_resolution_goal_and_actionable_blocker(self):
        self.intake.update(continuation='blocked', selected_next_action=None)
        self.bind()
        with self.assertRaisesRegex(ValueError, 'contradicts continuation'):
            self.validate()
        self.output['status'] = 'blocked'
        with self.assertRaisesRegex(ValueError, 'actionable blockers'):
            self.validate()
        self.output['blockers'] = [{'reason': 'Repository access is unavailable.',
                                    'next_action': 'Establish read access to the selected repository.'}]
        with self.assertRaisesRegex(ValueError, 'resolve the blocker'):
            self.validate()
        self.output.update(objective='Establish repository read access.', objective_kind='resolve-blocker')
        self.validate()

    def test_undecided_scope_does_not_fabricate_implementation_work(self):
        self.intake.update(continuation='undecided', selected_next_action=None)
        self.bind()
        with self.assertRaisesRegex(ValueError, 'focused next-action assessment'):
            self.validate()
        self.output.update(objective_kind='establish-next-action',
                           objective='Assess current evidence and select one defensible next action.')
        self.validate()

    def test_completed_scope_has_no_manufactured_next_task(self):
        self.intake.update(continuation='complete', selected_next_action=None)
        self.bind()
        self.output.update(status='no-follow-up', objective=None, objective_kind='none')
        self.validate()
        prompt = handoff.render(self.intake, self.output, self.base)
        self.assertIn('No next-session prompt is needed.', prompt)
        self.assertNotIn('Immediate goal:', prompt)
        self.output['objective'] = 'Find some cleanup to do.'
        with self.assertRaisesRegex(ValueError, 'must not invent follow-up'):
            self.validate()

    def test_claimed_executed_checks_need_verified_evidence(self):
        row = self.output['validation'][0]
        row['previous_result'] = 'passed'
        with self.assertRaisesRegex(ValueError, 'expected text list'):
            self.validate()
        row['source_ids'] = ['remote']
        with self.assertRaisesRegex(ValueError, 'Unverified source'):
            self.validate()
        row['source_ids'] = ['request']
        self.validate()  # Authorship and semantic truth still require agent review.

    def test_secrets_in_input_output_and_source_are_rejected_without_echo(self):
        token = 'gh' + 'p_' + 'notavalidcredential0123456789ABCDEFG'
        original = self.intake['request']
        for where in ('input', 'output', 'source'):
            with self.subTest(where=where):
                if where == 'input':
                    self.intake['request'] = token
                elif where == 'output':
                    self.intake['request'] = original
                    self.output['summary'] = token
                else:
                    self.output['summary'] = 'Synthetic handoff.'
                    path = self.base / 'example-source.md'
                    path.write_text(token, encoding='utf-8')
                    import hashlib
                    self.intake['sources'][0]['reference']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                with self.assertRaisesRegex(ValueError, 'redacted') as error:
                    self.validate()
                self.assertNotIn(token, str(error.exception))

    def test_signing_and_environment_sources_are_rejected_before_reading(self):
        for name in ('.env', '.env.production', '.ENV', '.ENV.PRODUCTION',
                     'upload.p8', 'signing.keystore'):
            path = self.base / name
            path.write_text('Synthetic private configuration.', encoding='utf-8')
            reference = self.intake['sources'][0]['reference']
            reference['path'] = name
            with patch.object(Path, 'read_bytes', side_effect=AssertionError('must not read')):
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'redacted'):
                    checks.source_file(reference, self.base)
