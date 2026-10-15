---
name: ct-rnd-plan-development
description: "Turn a ready project definition into small executable development slices, acceptance checks, dependencies, and verified GitHub Issues and Project Backlog items. Use before implementation or when replanning agreed scope; unresolved product decisions belong in project definition."
---

# Plan development

Produce a dependency graph that another engineer or agent can execute without
rediscovering the scope. Planning is complete only when every task has exactly
one verified GitHub issue and one item in the selected Project's Backlog.
Local validation and prepared publication payloads are intermediate results.

## Verify the starting point

Read the supplied project definition and its original interview ledger, then the
smallest relevant repository instructions, architecture, and existing tracker
state. Use `scripts/plan.py validate` on the authored plan; it validates the
definition and replays the original question history using the bundled contract.
A blocked definition or stale digest prevents planning readiness. Do not create
a fresh ledger, reopen settled choices, or obtain another question budget.

If scope remains unclear, return the original ledger and precise blocker to the
definition workflow. If that skill is unavailable, report the missing decision
without pretending it is answered. Keep ten questions/two batches total for this
scope, including earlier chats and other skills. Publication permission is a
separate authorization boundary and never an inferred answer.

Select the actual GitHub repository and user/organization Project. Preserve any
targets already settled in the definition. Null targets can be filled here after
checking the user's context and read-only GitHub access. Unknown targets block
publication; do not create repositories or Projects merely to satisfy the schema.
Inspect existing issues and Project fields before preparing writes.

## Build useful slices

Read [the contract](references/contract.md) for fields and commands. Start with
the smallest complete user outcome, then sequence additional slices. Each task
needs an observable outcome, explicit acceptance and verification, and only its
real prerequisites. Prefer complete behavior across the necessary layers over
separate frontend/backend/database tickets. A required shared foundation may be
its own task when it has independently observable proof and linked requirements.

Map every project success criterion to at least one task acceptance criterion.
Preserve constraints, exclusions, decisions and assumptions; the generated issue
bodies carry them verbatim. Do not hide new product scope inside technical work.
Name uncertain implementation details as investigation work with an explicit
decision deliverable. Ensure verification can fail when the behavior is wrong,
and distinguish local, CI, staging, human acceptance and production evidence.
Task size follows proof and independence, not a fixed count or arbitrary duration.

Review the graph against the real repository and intended user flow. Scripts
check structure and traceability, not whether a requirement was understood or a
slice is well designed. All newly published tasks start in Backlog even if their
dependencies are already complete; admission to execution is a later decision.

## Prepare, publish, and read back

Run `validate`, then `prepare` to create deterministic issue titles/bodies and
stable per-task markers. New payload destinations are exclusive; existing files
are never overwritten. Show a concise plan with task dependencies and important
risks. Honor instructions to keep work local: report prepared, publication pending,
and stop before external writes when publication is not authorized.

When authorized, publish through available GitHub tools or the official CLI/API.
Read [publication and recovery](references/contract.md#publication-and-recovery)
before writes. Reconcile markers and existing bodies first, create only missing
issues, add each to the chosen Project, and explicitly select its Backlog status.
Preserve other work and existing lifecycle state; conflicting, already-progressed,
or ambiguous matches require reconciliation rather than duplication or reset.
Use argument arrays or body files, never interpolate issue content into shell code.

Record the exact issue URLs in a receipt, then run `verify-tracking`. That command
uses read-only live GitHub API calls to check every issue body/title, duplicate
markers, membership and Backlog status. A supplied `verified: true`, an API mutation
success, or a saved screenshot cannot replace readback. Failures or inaccessible
Projects remain blocked with the smallest recovery action. An interrupted run
can reuse unchanged markers/payloads; uncertain writes must be looked up before retry.

Deliver the readable graph, definition/ledger/plan/payload paths, exact issue and
Project links, verification evidence and any blockers. Treat GitHub Issues and
Projects as the execution source of truth after publication. Read them again when
work resumes; this script verifies initial publication, not later task completion.

## Runtime boundary

Python 3.10+ is the only dependency for local validation/preparation. Live readback
additionally needs an authenticated `gh` with repository and Project read access.
The bundled `definition.py` is the definition skill's canonical validator copy;
no other skill installation or private library is required. Scripts never publish,
install packages, execute project code, or increase the question budget. GitHub.com
Projects v2 user/organization URLs are supported; Enterprise and other trackers
must remain blocked until an explicit adapter is implemented and verified.
