"""Domain-specific lifecycle contract checks; fixtures are not product acceptance."""
import sys
import unittest

from engineering_lifecycle_fixture import (
    EngineeringLifecycleFixture,
    ROOT,
    SKILLS,
    NAMES,
    asset,
    workflow,
)


class EngineeringLifecycleTests(EngineeringLifecycleFixture):
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



if __name__ == "__main__":
    unittest.main()
