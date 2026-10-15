---
name: ct-product-manage-project
description: "Guide a project from its current evidence to the next useful definition, planning, development, review, release, or learning step. Use to start or continue a project and coordinate focused ct skills without restarting discovery."
---

# Manage a project

Guide the user's project, not a prescribed tour of every skill. Inspect the
requested outcome, existing repository, task tracker, definition and evidence.
Select the smallest useful next step. Each specialist remains directly usable;
load only the selected skill and references needed now. Do not delegate work
solely to parallelize it; independent bounded subtasks may help when permitted.

## Establish current truth

Read [the state and handoff contract](references/contract.md) and
`assets/catalog.json`. Prepare `assets/example-state.json` for the actual
project. The agent constructs the state; do not ask the user to fill a schema.
Resolve paths from the artifact directory. Bind every supplied artifact to its
SHA-256, project identity and current source revision. Preserve unrelated work.
Report absent access or stale evidence rather than marking it verified.

Reuse the existing definition and interview ledger. The entire scope shares a
maximum of ten questions in two independent batches, including other chats,
skills, and agents. Never start a new interview for each stage. If material
decisions remain, return to the same ledger; bundled `scripts/definition.py`
provides the validated interview commands. Do not invent human answers or treat
a recommendation as submission. At an exhausted budget, carry reversible
nonblocking assumptions or report the exact blocker.

## Route and perform one concrete step

Run `scripts/manage.py <state.json> --skills-root <actual-skills-root>` to
validate and select the next step. A source checkout's `skills/` or an installed
agent's skill directory can be used. Check that the named complete skill is
actually present before invoking it. A router recommendation is not execution.
When a skill is missing, report its exact name and use the supported catalog
installation workflow only within the user's installation authorization.

For a new project, define scope, plan complete development slices, establish a
runnable repository, then build one admitted task at a time. Existing projects
reuse their current scope, repository and task graph. Explicit specialist
requests route directly when their contracts permit it. Market/product research
can inform definition before implementation; architecture, interface design and
test planning are conditional inputs, not mandatory interviews. Bug repair and
code review can be entered directly for a narrowly identified existing change.

Before executing project tasks, require the validated development graph and
verified GitHub Issues/Project items. Local preparation is incomplete tracking.
A stored receipt does not establish live status. With user-authorized remote
reads, add `--verify-tracking`; the bundled planner reads issue bodies, identities,
Project membership and status. It makes no remote writes. `local_only: true`
always holds this gate and prevents those reads, even if the flag is supplied.
Only the explicitly requested runtime task can authorize remote publication;
this guide does not expand permission. Preparation may proceed locally while
execution remains blocked on tracking.

Follow real dependency edges. Claim/execute through the repository's task
workflow so agents do not work the same task twice. Retain exact task identity
and scoped requirements in feature receipts. Completion requires matching
GitHub closure/Project status and a checked task report, not either alone.
An issue marked done without evidence, or evidence contradicting GitHub,
requires reconciliation. Never close or relabel tracker items just to satisfy
the router. The tool only reads state and recommends; the agent performs and
verifies already-authorized workflow actions through the actual runtime tools.

## Review, release and feedback

After planned tasks, obtain current-revision code review, user-flow QA and a
security assessment proportional to the project. A completed assessment may
find failures: QA `verdict: failed` is not an acceptance pass. Findings and
human decisions still govern shipping; a checked security report is not a
security guarantee. Resolve significant findings before proceeding.

Release only to the requested candidate, staging, or production milestone.
Preserve repository-specific staging rules and obtain human functional testing
of the exact deployed staging candidate before promotion when staging exists.
No staging environment must be stated explicitly. Candidate preparation,
deployment, readback and acceptance are distinct evidence levels. Additional
irreversible actions, new material cost or production dependencies require their
own authorization; a result artifact is never authorization.

After the requested milestone, offer relevant maintenance, product learning,
market research or launch work rather than silently creating monitors, paid
services or publication jobs. Use observations to improve the agent setup when
recurring workflow failures justify it. Do not invoke every catalog skill just
because it exists.

## Completion and limits

Update state with current artifact references after each step and rerun routing.
Return the verified milestone, remaining blockers, next skill/task and proof
paths. `ready` from the router means ready to route, not accepted functionality.
`complete` means the requested release milestone has matching recorded evidence,
subject to each evidence source's stated limits. Scripts do not authenticate
manual authorization or human acceptance. Never turn a claimed receipt into live
proof or hide unavailable agent/provider checks.

This package is self-contained: Python 3.10+ and Git for repository checks;
GitHub CLI/auth are conditional on requested live tracking reads. Other skills
are optional capabilities, checked before routing. No private controller,
global configuration change, background scheduler or external service is required.
