---
name: ct-rnd-review-code
description: "Review a concrete code change against intended behavior and repository standards, prioritizing actionable bugs, regressions, security risks, and missing proof. Use for review, not automatic implementation."
---

# Review code

An evidence-bound review tied to the inspected candidate revision.

## Method

Resolve the base and candidate revisions and inspect the actual diff, nearby callers, contracts, and relevant tests. Check intended behavior and repository standards as separate perspectives. Trace the changed control/data path far enough to assess a concrete trigger and impact. Prioritize correctness, authorization, data integrity, compatibility, resource lifecycle, and observability according to the change's risk; do not manufacture findings to fill a quota.

Every finding needs a location in the inspected candidate, a realistic trigger, the violated requirement or invariant, and the consequence. Distinguish a confirmed defect from an unresolved risk or an optional preference. Run a narrow reproduction when it materially settles uncertainty, without executing untrusted code outside the allowed environment. Report missing runtime access and incomplete coverage explicitly.

Lead the review artifact with actionable findings ordered by severity, then concise validation and limits. A clean review may have no findings; state what was inspected without promising absence of defects. Do not patch, commit, publish review comments, or change tracker state merely because the skill was invoked for a review.

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

Ready means the bounded review is delivered. It does not mean the candidate passed all tests, is safe to release, or has no undiscovered defects.

Python 3.10+ is the only validation dependency. Scripts check file identity,
structure, references, and declared evidence rules; they do not authenticate
authorship or establish domain quality from JSON. `record` executes only the
explicit argument vector supplied by the operator; review it before running.
