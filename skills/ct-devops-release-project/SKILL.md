---
name: ct-devops-release-project
description: "Prepare or execute a scoped release with build proof, rollback information, exact revision tracking, and separate staging and production evidence. Use for release work, not general feature implementation."
---

# Release Project

For Apple App Store/TestFlight or Google Play work, prefer the installed
`ct-devops-release-apple-app` or `ct-devops-release-android-app` specialist when
available. Those own store-specific testing, review and publication milestones;
this skill remains the generic repository release lane.

Read the repository's actual release procedure, branch protections, environment identity and artifact provenance. Identify the exact candidate revision, relevant dirty work, required checks and recovery route before any deployment. A successful build is a candidate, not a deployment.

Run the narrow required checks and capture the repository-native build. Reuse a proven artifact when the release procedure supports it. Record target, version and artifact identity so the source tested can be connected to the source deployed. Fix only blockers within the authorized release scope.

For staging-enabled projects, deploy only when authorized, verify the deployed revision, and hand that exact build to the user for functional acceptance. Stop at that gate if acceptance is missing. Never treat CI, a deploy trigger, a browser spot check, or group assignment as human acceptance. If staging does not exist, state that explicitly and document the project's actual qualification route.

Before production, confirm the applicable authorization and acceptance source, required checks, rollback constraints, and pending migrations. New material spend and irreversible migrations require explicit decisions. After an authorized deployment, read back the live revision and exercise the relevant live health check. If deployment outcome is ambiguous, inspect current state before retrying. Retain failed attempts and report which recovery action is supported by evidence.
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
