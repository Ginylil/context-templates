---
name: ct-qa-test-user-flows
description: "Exercise real user journeys against a defined project and record pass, failure, or blocked evidence at the exact tested environment. Use for end-to-end functional checks, not a release decision or a source-only review."
---

# Test User Flows

Start from the project's success criteria and the requested environment. Map every criterion to a journey and include the relevant actor, starting state, expected result, and cleanup. Prefer the existing browser or integration harness; inventing a second harness usually weakens the evidence.

Confirm which deployed build is being exercised before testing. Use synthetic accounts and data within the authorized side effects. Include the successful route plus consequential permission, validation, recovery, and persistence failures. A UI assertion alone cannot prove tenant isolation; inspect the denied API operation when that boundary matters.

Record the actual steps, expected and observed behavior, and capture or command evidence per scenario. Retain failures in the report. An assessment can be complete with a failed verdict; never turn an unexecuted scenario into a pass. If a criterion cannot be exercised, report it as blocked with the missing prerequisite.

For projects with staging, local and CI results remain engineering evidence. Identify the exact staging build and hand it to the user for functional testing before calling it accepted. Browser automation, deployment success, and a human acceptance decision are different evidence levels. Do not repair discovered defects under a testing-only request; route actionable defects to ct-rnd-fix-bug when available.
## Validated handoff

Read [references/contract.md](references/contract.md) when preparing intake or output. The exact domain schema is [assets/contract.json](assets/contract.json). Use the packaged standalone helper from the installed skill directory, with `python3` on macOS/Linux or `py -3` on Windows:

```text
python3 <skill>/scripts/workflow.py validate-input input.json
python3 <skill>/scripts/workflow.py validate-output input.json output.json
python3 <skill>/scripts/workflow.py render input.json output.json --output report.md
```

Validate intake before work and output before handoff. Capture relevant command evidence with `record --cwd <repository> --output proof.json --timeout 60 -- <command> <arguments>`; recording runs that command, so use only in-scope commands. Inspect proofs and redact private content before including artifacts. Do not fabricate successful commands, source snapshots, approvals or metrics to satisfy validation.

Reuse the project's definition and shared scope ledger. All participating skills share ten questions across at most two batches for that scope, including resumed chats. Never start a fresh interview budget here. Inspect discoverable evidence first; route consequential missing decisions to ct-product-define-project if available, or report a blocked handoff with the missing decision and existing ledger. Do not bundle hidden subquestions.

GitHub Issues and Projects remain the execution source of truth once the plan is published. This skill does not silently create tracker entries or reset their state. Return proposed follow-up work with evidence for the planner; perform external writes only within explicit authority.
