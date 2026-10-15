---
name: ct-marketing-research-market
description: "Research audiences, competitors, alternatives, positioning and channels using dated sources and explicit uncertainty. Use for evidence-backed market decisions, not launch execution or invented market sizing."
---

# Research Market

Begin with the decision the research should inform, intended audience and geography. Separate customer jobs and current alternatives from product categories; a spreadsheet or manual process may be the most relevant competitor. Include evidence that could contradict the proposed positioning.

Use current primary sources for prices, product capabilities and platform rules, preserving URLs, observed dates and source snapshots. Customer statements support their own context, not an entire segment. Treat vendor promises, sponsored reports and estimated traffic according to their limitations. Cross-check consequential claims before recommending substantial spend or effort.

Build a concise alternative comparison around the customer job, tradeoffs and evidence. Distinguish verified facts, inference and hypotheses. A missing source is an unknown, not evidence that a competitor lacks a feature. Do not turn search result counts or invented percentages into market size.

Return positioning options with supporting claim IDs, validation needed and bounded channel tests. Prepare recommendations without contacting prospects, signing up, purchasing tools or publishing content unless explicitly requested. Capture changed or unavailable sources and date-sensitive uncertainty.
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
