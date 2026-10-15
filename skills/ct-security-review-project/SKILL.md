---
name: ct-security-review-project
description: "Review application and delivery security within an agreed scope, producing evidence-backed findings and explicit coverage gaps. Use for security assessments, not active exploitation or a guarantee of safety."
---

# Review Project Security

Identify protected assets, actors, entry points and trust boundaries before listing vulnerabilities. Ground the review in the exact repository revision and actual deployment/configuration evidence available. Distinguish a dangerous pattern from a reachable, consequential defect.

Inspect the applicable boundaries: identity and sessions; object- and tenant-level authorization; input and output handling; secrets and sensitive data; dependencies and build trust; infrastructure permissions; and abuse of agent/tool capabilities when present. Choose depth according to the application rather than assigning the same checklist to every project.

For each finding, connect a demonstrated entry point to a protected asset, describe impact and confidence, cite bounded evidence, and propose the smallest mitigation plus a meaningful validation. Redact credentials, customer data and attack-enabling private details from public artifacts. Mark inaccessible controls unassessed; do not infer a deployed control from infrastructure code alone.

Remain within the requested authority. Active scans, exploit attempts, credential rotation, permission changes, and dependency upgrades need the applicable authorization. Prefer non-destructive local reproductions using synthetic data. Return prioritized fixes and remaining uncertainty. A ready assessment means this bounded review is complete; it does not certify the system secure.
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
