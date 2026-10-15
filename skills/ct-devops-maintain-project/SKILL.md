---
name: ct-devops-maintain-project
description: "Assess service health, spend, changes, security, failures and recovery readiness, with explicit monitoring gaps and prioritized maintenance. Use for bounded operational reviews, not an implicit recurring monitor."
---

# Maintain Project

Establish the service inventory, providers, account/environment identities and exact observation window. Use existing telemetry and billing sources before adding instrumentation or running cost-incurring queries. Describe visibility gaps before drawing health conclusions.

Keep separate coverage for spend/waste, changes, security, health, failed jobs/errors, incidents, and recovery. A quiet alert feed does not establish health if collection or the operator machine was offline. Name metric periods, units, retention limits and delayed cost data. Validate suspected waste against resource ownership and activity before proposing removal.

For each action, identify target, expected benefit, impact and recovery. Read-only assessment does not authorize cleanup, access changes, new dependencies, backup deletion, or a paid service. Exact-target revalidation and the applicable approval must precede destructive execution. Distinguish backups existing from a demonstrated restore; propose a bounded recovery exercise when proof is absent.

If an active incident is found, report its impact and evidence promptly and follow the project's incident procedure within authority. Otherwise return a prioritized maintenance report and missing access. Scheduling or continuous monitoring requires an explicit request; a completed review does not promise future observation.
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
