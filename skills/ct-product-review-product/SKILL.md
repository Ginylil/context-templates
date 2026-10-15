---
name: ct-product-review-product
description: "Assess product value, onboarding and outcomes from observed usage and customer evidence, then propose measurable improvements. Use for an existing product review, not market research or unsolicited customer contact."
---

# Review Product

Frame the review around a concrete customer job and product decision. Inspect the actual flow and available usage, support, feedback or research evidence. Establish the population, period, denominator and instrumentation limitations before interpreting a conversion or retention metric.

Keep observations, interpretations and recommendations separate. Small samples, internal demonstrations and imagined personas do not establish demand. Look for the earliest point at which users obtain meaningful value; compare intended activation with observed behavior and consequential failures, accessibility barriers, pricing confusion or recovery friction.

Tie each opportunity to observed evidence, the affected audience and an explicit outcome measure. Include a counter-metric to detect harmful tradeoffs. Recommend a bounded experiment with a decision rule instead of claiming an uplift. If evidence is missing, propose what to collect and why; do not manufacture customer quotes, metrics or certainty.

Use only consented research material and authorized account access. Drafting interview questions is within assessment; contacting users, publishing surveys, changing pricing or launching experiments requires the relevant request. Route market competition to ct-marketing-research-market and new implementation tasks through the GitHub-backed development plan.
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
