---
name: ct-qa-plan-tests
description: "Turn agreed requirements and risks into a traceable acceptance test plan with realistic data, failure scenarios, proof surfaces, and execution gates before implementation or qualification."
---

# Plan tests

A risk-informed test plan covering each agreed project outcome.

## Method

Read the bound definition, current implementation boundaries, critical business flows, and existing tests. Separate requirements from proposed behavior and identify ambiguities before inventing expected results. Use the shared decision ledger for consequential unknowns. Map each success criterion to an observable test, then add risk-driven cases for permissions, invalid/duplicate inputs, partial failure, persistence, retries, and recovery when those behaviors exist.

Choose the cheapest surface that can establish each claim: a unit check for a pure rule, an integration check for a service boundary, a browser/device check for interaction, or a staging exercise for deployed behavior. Define preconditions, realistic secret-free data, steps, expected results, and cleanup. Avoid tests that simply repeat implementation details or depend on brittle incidental wording. Do not require a production write to prove behavior that can be safely exercised elsewhere.

Order checks by dependencies and cost. Identify what can run locally or in CI, what requires credentials or external services, and what must be handed to the user on an exact staging candidate. Record exclusions with their impact rather than implying full coverage. The output is an executable plan with evidence requirements, not a list of claimed passes. If test execution was requested too, run it separately and report actual results at their evidence level.

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

Ready means the test plan covers the agreed outcomes; no scenario has passed merely because the plan validates.

Python 3.10+ is the only validation dependency. Scripts check file identity,
structure, references, and declared evidence rules; they do not authenticate
authorship or establish domain quality from JSON. `record` executes only the
explicit argument vector supplied by the operator; review it before running.
