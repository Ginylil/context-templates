---
name: ct-rnd-build-feature
description: "Implement a complete agreed feature in an existing project, including integration, failure and recovery paths, and meaningful regression evidence. Use for feature work after scope and tracking are established."
---

# Build a feature

A complete engineering candidate traceable to agreed outcomes.

## Method

Read the task, bound definition, applicable instructions, and nearby implementation before changing code. Confirm the task's GitHub Issue and Project item and respect their dependencies; use their existing state rather than creating parallel local tracking. If a direct request has no tracking yet, prepare the task and obtain any missing external-write authorization before publication. Do not call development complete without verified tracking.

Choose one thin vertical slice that produces observable behavior across the necessary layers. Identify the acceptance scenarios and the most consequential failure paths before coding. Add a regression test where it demonstrates missing behavior, then implement the smallest complete change. Cover validation, permissions, loading/empty/error states, retry or recovery, and resource cleanup where relevant. Reuse repository interfaces and avoid speculative abstractions.

Verify the behavior at the cheapest credible surface, then run the relevant integration checks and production build. Record failures as failures; repair the cause rather than weakening the acceptance requirement. For a project with staging, hand the exact deployed revision and scenario to the user for functional testing before calling it accepted or promoting it. A screenshot, local test, CI pass, or deploy trigger is not staging acceptance. If no staging exists, state that explicitly and describe the remaining acceptance boundary.

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

Ready means an engineering candidate with passing local checks and a concrete staging handoff, not user acceptance, merge, or production availability.

Python 3.10+ is the only validation dependency. Scripts check file identity,
structure, references, and declared evidence rules; they do not authenticate
authorship or establish domain quality from JSON. `record` executes only the
explicit argument vector supplied by the operator; review it before running.
