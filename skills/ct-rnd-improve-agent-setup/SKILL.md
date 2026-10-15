---
name: ct-rnd-improve-agent-setup
description: "Use an observed development failure to improve repository agent instructions, tool setup, checks, or supporting skills, with the same before and after verification. Use for grounded workflow repairs rather than speculative policy expansion."
---

# Improve agent setup

A small agent-workflow repair with demonstrated benefit.

## Method

Read the concrete failure evidence and the smallest relevant repository instructions and tool configuration. Determine whether the failure comes from missing documentation, a broken deterministic check, unavailable capability, unclear ownership, or an agent judgment error. Do not turn one exceptional run into a universal rule or add an agent/skill simply because a task was difficult.

Locate the canonical owner, resolving installed links before editing. Prefer a small correction in the existing instructions or script over duplicated rules, new orchestration layers, or broad environment changes. Keep public guidance portable and keep private account names, paths, histories, and credentials out of public packages. When a script can enforce the invariant, repair the script and retain a meaningful invalid case rather than relying only on prose.

Build a bounded reproducible check for the observed failure. Demonstrate its failure before the correction, apply the correction, then run the same check. Verify related setup paths when the change affects them. Reconcile instructions with actual commands, identify which judgment still belongs to the agent, and report the demonstrated benefit and limitations. Obtain the required authorization for changes outside the requested repository or public publishing.

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

Ready means the observed setup defect is repaired under the tested conditions. It does not prove every model or agent runtime follows the guidance.

Python 3.10+ is the only validation dependency. Scripts check file identity,
structure, references, and declared evidence rules; they do not authenticate
authorship or establish domain quality from JSON. `record` executes only the
explicit argument vector supplied by the operator; review it before running.
