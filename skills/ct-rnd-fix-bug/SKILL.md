---
name: ct-rnd-fix-bug
description: "Reproduce a reported software defect, identify its cause, make a focused repair, and prove the same regression check changes from failing to passing. Use for confirmed defects rather than broad feature work."
---

# Fix a bug

A focused repair with comparable before and after regression evidence.

## Method

Establish the observed and expected behavior from the report and current code. Inspect the matching revision, inputs, viewport, permissions, and environment. Reproduce the failure with the smallest meaningful check; for a visual defect, capture the matching rendered state before and after and include an interaction regression when possible. A guessed cause is not a diagnosis.

If the behavior cannot be reproduced, gather higher-signal logs, traces, network results, or a narrow test rather than repeatedly changing code around the theory. Bound any live evidence collection and preserve private data. For a new test, first demonstrate that it fails against the affected implementation for the reported reason. Record the unmodified failing invocation and its result.

For interface defects, use `ct-design-fix-interface` when available for rendered
reproduction, related occurrence coverage and clarification of uncertain variants.
Otherwise inspect shared owners and independent copies here; do not stop at the
reported location when the same evidenced cause recurs.

Trace the failure to the violated invariant, make a narrow repair, and rerun exactly the same regression command in the same worktree. Record a separate related check to catch plausible side effects. Explain why the change fixes the demonstrated cause and what remains untested. Use issue/Project tracking for the repair and preserve unrelated changes. If staging exists, provide the exact deployed candidate for the user's functional test before calling it accepted.

## Checked handoff

Read [the contract and command guide](references/contract.md) before preparing the
handoff. Create the input JSON in the project's working area; the agent fills it
from evidence rather than asking the user to complete a schema. Bind any supplied
definition, ledger, and source files by path and SHA-256. Run this package's
`scripts/workflow.py validate-input` before work and `validate-output` before
reporting completion. Capture command results with `record`; do not hand-author
passing command evidence. Keep output and proof artifacts outside the installed
skill and outside the inspected repository (or in an already ignored evidence
directory), so recording evidence does not itself change the working-tree digest. The blocked examples show structure only and claim no executed work.

Questions share the project's existing definition ledger: at most **10 questions
across 2 batches for the scope**, including earlier or resumed conversations.
Inspect its status before asking and record a batch before displaying it. Within
a batch, ask only independent decisions whose prerequisites are settled. Count
unanswered questions, preserve partial answers, and never reset the ledger or ask
outside it. If a standalone request needs questions and no ledger exists, use
this package's `scripts/definition.py` to create the scope ledger first; reconstruct
prior questions when resuming. At the cap, use explicit reversible assumptions
or return an actionable blocker. Silence never supplies an answer or permission.

This skill is directly invocable; installing the other catalog skills is not
required. GitHub Issues and Projects remain the source of truth for executable
work. Verify the repository, issue, Project membership, and dependencies when
acting on a task; a local handoff does not establish publication. Prepare external
writes only within the user's authorization, and read back a performed write.
Never infer authorization from a validator's success. Preserve unrelated work;
keep review-only requests read-only and obtain explicit approval for destructive
actions, new material costs, production dependencies, or scope expansion.

## Deliver and state the boundary

Render the checked JSON to a readable brief with `render`. Deliver its path, the
input/output/proof paths, what was actually checked, remaining limitations, and
the next action. Use `blocked` with an actionable reason when required context or
proof is unavailable. A structurally valid blocked report is not completion of
the underlying work. Reconcile relevant repository documentation after requested
implementation; keep local changes and publication authority separate.

Ready means a demonstrated local regression repair. A failing command caused by a broken test harness is not valid before evidence, and a passing unrelated command is not repair proof.

Python 3.10+ is the only validation dependency. Scripts check file identity,
structure, references, and declared evidence rules; they do not authenticate
authorship or establish domain quality from JSON. `record` executes only the
explicit argument vector supplied by the operator; review it before running.
