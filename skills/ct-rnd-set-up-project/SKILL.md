---
name: ct-rnd-set-up-project
description: "Create or complete a runnable repository with reproducible setup, environment configuration, development commands, tests, build, and CI. Use for project foundations before feature delivery."
---

# Set up a project

A reproducible project foundation with captured setup, test, and build evidence.

## Method

Inspect the selected path, ownership, repository instructions, and current files before writing. Reuse a suitable existing stack and approved provider choices. For a new stack, choose a small maintained foundation justified by the definition. Do not initialize over another project or assume an empty directory; preserve unrelated files and secrets.

Establish one documented setup path, a foreground development command with an observable readiness signal, a meaningful test, and a production build. Keep environment templates secret-free and distinguish required values from optional integrations. Prefer dependency lockfiles and version declarations that allow another developer and CI to reproduce the environment. Avoid installing global tools when a local invocation works.

Create CI for the repository's real checks and document how to run them locally. Run setup, tests, and build explicitly and capture each result. Inspect the development surface when it exists and record any missing credentials or unavailable dependencies truthfully. The foundation test must exercise actual runtime behavior, such as a health handler, rather than merely assert that a scaffold file exists. Document first-run setup and failure recovery.

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

Ready means the local foundation checks passed and CI configuration exists. CI execution, staging deployment, and product acceptance remain separate evidence levels.

Python 3.10+ is the only validation dependency. Scripts check file identity,
structure, references, and declared evidence rules; they do not authenticate
authorship or establish domain quality from JSON. `record` executes only the
explicit argument vector supplied by the operator; review it before running.
