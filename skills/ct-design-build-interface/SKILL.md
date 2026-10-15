---
name: ct-design-build-interface
description: "Design and implement an interface with clear hierarchy, platform-appropriate interaction, accessibility, and rendered proof. Use for substantial interface work after the intended user flow is defined."
---

# Build an interface

A rendered, interactive engineering candidate with requirement and viewport coverage.

## Method

Inspect the current design language, actual user flow, content, and target platform before choosing a visual direction. Read the project's design contract when present. Establish hierarchy from the user's primary task; simplify copy, competing actions, and unnecessary choices before adding ornament. Preserve recognizable patterns unless the requested change justifies replacing them.

For substantial new visual work, produce a concrete reviewable direction before full implementation. Use real content structure, primary states, and representative narrow/wide viewports. Build with repository-native components and semantic controls. Support keyboard/focus behavior, meaningful labels, readable contrast, touch targets, reduced motion, and loading/empty/error states as relevant. Verify evolving browser capabilities against primary documentation when using them.

Run the interface and inspect the rendered result at each requested viewport. Capture actual screenshots and exercise the primary interaction, including its failure or recovery path. For existing defects, match the original viewport and provide before/after evidence; new surfaces may have a null before capture with an explicit explanation. Check overflow, content wrapping, assets, console errors, and interaction state before recording proof. Hand off the exact deployed staging version for user testing where staging exists; local rendered review remains engineering/design evidence.

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

Ready means the candidate was rendered and its primary interaction checked at the declared viewports. Screenshot hashes establish artifact identity, not visual quality or user acceptance.

Python 3.10+ is the only validation dependency. Scripts check file identity,
structure, references, and declared evidence rules; they do not authenticate
authorship or establish domain quality from JSON. `record` executes only the
explicit argument vector supplied by the operator; review it before running.
