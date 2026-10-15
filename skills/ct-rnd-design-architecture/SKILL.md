---
name: ct-rnd-design-architecture
description: "Design a project architecture from agreed requirements, including component boundaries, data ownership, interfaces, failure behavior, and justified tradeoffs before implementation."
---

# Design architecture

A reviewable technical design traceable to project outcomes.

## Method

Start from the bound definition and the actual repository. Identify actors, trust boundaries, domain vocabulary, data lifecycle, expected load, and recovery expectations. Describe the smallest architecture that meets those requirements; do not infer a need for microservices, queues, or paid infrastructure from a diagram.

Compare credible options using the constraints that distinguish them: operational ownership, coupling, latency, durability, migration cost, and available expertise. For an existing system, show the proposed delta and compatibility path. Specify who owns each datum, what crosses each interface, what fails, and how callers recover. Explain consequential choices and rejected alternatives in the design document.

Map every success criterion to a concrete design mechanism. Review failure paths, authorization boundaries, deletion/retention behavior, and any schema or API migration. A component diagram is useful when it explains those boundaries, but it does not replace interface contracts. Identify unknown capacity or vendor behavior as a risk with a verification action.

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

Ready means the design is complete for engineering review; it is not implementation or runtime proof.

Python 3.10+ is the only validation dependency. Scripts check file identity,
structure, references, and declared evidence rules; they do not authenticate
authorship or establish domain quality from JSON. `record` executes only the
explicit argument vector supplied by the operator; review it before running.
