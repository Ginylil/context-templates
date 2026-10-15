---
name: ct-marketing-launch-product
description: "Prepare product launch assets and measurement, then publish only explicitly authorized assets with duplicate prevention and live readback. Use for launch preparation or execution, not market discovery."
---

# Launch Product

Read the agreed positioning, target audience, product availability and supported claims before drafting. Confirm that the product revision and destination can deliver the promise. Distinguish launch preparation, scheduling, publication and public availability in every status report.

Adapt each asset to its channel and audience while preserving the approved claim evidence. Include the intended action and destination. Define baseline, target, measurement window and attribution limits; an unmeasured baseline stays unknown. Do not invent testimonials, user counts, revenue, endorsements or performance improvements.

Default to the requested mode. In prepare mode, write reviewable local assets and a publishing checklist. In publish mode, require the exact authorization source for account, channel, content and timing. Resolve missing approval without posting. Paid promotion and new metered services require explicit authorization. Never embed private customer material or credentials in assets.

Before each authorized write, inspect existing scheduled/published state and use a stable asset/channel idempotency key. After an ambiguous response, reconcile state before retrying. Record returned IDs and verify the published item, destination and audience visibility. A successful API response alone is not live proof. Report partial publication honestly and preserve the recovery/edit route.
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
