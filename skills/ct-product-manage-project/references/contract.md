# State, routing and standalone resources

The guide has one versioned state JSON. Paths in references resolve relative to
the state file, and references contain `{path, sha256}` with an actual file hash.
Do not use a fake digest or a bare boolean claiming verification.

| Field | Value |
| --- | --- |
| `schema_version` | Integer `1` |
| `project_id`, `objective` | Stable scope identifier and user-facing outcome |
| `intent` | `continue`, or an intent from bundled `assets/catalog.json` |
| `local_only` | Boolean; true prevents all live GitHub verification |
| `ledger`, `definition`, `plan`, `tracking` | Nullable file references |
| `repository` | Null, or `{path, revision, working_tree_sha256}` for an existing Git checkout at that exact HEAD and working tree |
| `receipts` | Current specialist reports as `{skill, input: reference, output: reference}`; at most one per producer |
| `task_receipts` | `{task_id, input: reference, output: reference}` from `ct-rnd-build-feature` |
| `target_stage` | `candidate`, `staging`, or `production` |
| `done_statuses` | Nonempty list of actual Project statuses used for completed issues; normally `["Done"]` |

Examples start before definition with null references. A definition needs its
ledger; a plan needs its validated ready definition; a tracking receipt needs
its matching plan. The guide checks the bundled definition and planner
contracts independently of other skill installations. Stored tracking receipts
are identity-bound declarations until live verification is explicitly requested.

```text
python3 <skill>/scripts/manage.py state.json --skills-root <skills-directory>
python3 <skill>/scripts/manage.py state.json --skills-root <skills-directory> --output next.json
python3 <skill>/scripts/manage.py state.json --skills-root <skills-directory> --verify-tracking
python3 <skill>/scripts/manage.py state.json --skills-root <skills-directory> --validate-output next.json
```

Use `py -3` on Windows when appropriate. New output destinations are exclusive:
an existing file is never overwritten. Validation failures exit 1 with stderr;
valid routing decisions, including an explicit blocked route, exit 0. `status`
is `ready`, `blocked` or `complete`; `next_skill`, `task_id`, `milestone`,
`reason`, shared interview usage, local-only state and actual tracking-read flag
are returned. The input SHA-256 pins the state that produced the recommendation.

When no definition is present, the route selects Define a Project. A blocked
definition returns to the same ledger. When tasks are ready for planning, the
planner must validate its DAG, prepare payloads, publish within authorization,
and verify GitHub. Task execution is blocked until current readback succeeds.
The default verification mode in the planner requires new issues in Backlog;
the guide's ongoing mode allows later statuses and compares closures with
`done_statuses` and scoped task proof. Exact issue content and digest bindings
must still match. The guide never mutates issues or Project fields.

The normal execution route skips repository creation when a verified checkout
is provided, chooses one task whose dependencies have both remote completion
and local proof, then requests code review, QA and security before release.
The explicitly requested release stage is the completion milestone. Explicit
specialist intents remain available for existing projects or narrow read-only
assessment without forcing the full initial-project workflow.

Use `python3 <skill>/scripts/workflow.py inspect-repository <repo>` to obtain the
repository binding. After authorized source edits, preserve the earlier intake
as history, refresh this source metadata in the current intake, and bind the new
output digest. Do not change scope, constraints, or prior answers while refreshing
observed source state. Successful check evidence must match the final fingerprint.

## Specialist receipts

For the seventeen domain specialists, `scripts/workflow.py` validates both the
referenced intake and output with that producer's bundled `assets/contract.json`.
Therefore the producer must be installed to validate its receipt. Each complete
producer package carries its own identical standalone support scripts. A report
must match project identity, input digest, constraints, current definition/ledger,
repository where supplied, required checks and domain rules. The guide rejects
stale or wrong-project reports even if their status says ready. Feature reports
must additionally match the exact task ID, requirement IDs, and every planned
acceptance ID, criterion (`scenario`), and verification instruction. Each planned
acceptance ID must appear in the feature report's checked scenarios.

Completed task receipts retain their historical source binding as later tasks
advance the checkout. The task's Git revision must remain an ancestor of current
HEAD, and each passing command must match that task intake's revision and working
tree digest. This preserves recorded task evidence; it cannot prove historical
uncommitted files still exist or that later edits preserved behavior. Current
review, QA, security and release receipts must match the current checkout and
provide the final regression gates. No historical mode is exposed by the domain
CLI or accepted for other specialist reports.

An assessment's `ready` status means its bounded work is complete. It may expose
product, security or test failures. In particular the guide requires QA
`verdict: passed` before treating QA as a passing release gate. Human review
still owns consequential findings and acceptance. See each producer's contract
for its exact result fields and what its evidence can establish.

The platform release intents `release-apple-app` and `release-android-app` select
the corresponding installed specialist directly. Their bundled store helper
validates exact app/build/export identity and provider-state relationships when
receipts return. This routing recommendation is not a release authorization or
confirmation of store availability.

## Shared interview

`scripts/definition.py` is the complete Define a Project validator, bundled
without a cross-install dependency. Reuse the same ledger's `status` and `apply`
commands when recording newly necessary questions; do not start a new ledger to
obtain another allowance. Its interview is capped at ten recorded questions in
two batches, with settled dependency frontiers and actual submitted answers.
The package includes the canonical [definition contract](definition-contract.md)
with complete input, event and output formats. It also includes the canonical
[planning contract](planning-contract.md) for graph and tracking handoffs.

## Command evidence

The domain support tool can capture an explicitly supplied command:

```text
python3 <skill>/scripts/workflow.py record --cwd <repo> --output <proof.json> --timeout 30 -- <command> <arg>
```

This executes that argv without a shell, captures stdout/stderr, completion,
source revision and working-tree fingerprint, and makes no inferred retries.
Never pass secrets in argv or capture a paid/external mutation without its
authorization. Use a proof directory outside the measured repository or ignored
by Git so proof creation does not change the source fingerprint. The output is
reserved before execution; if it already exists the command does not run. A
failed or timed-out command still produces truthful proof. Recording success
means evidence was stored, not that the recorded check passed. Values may be
inspected or forged by the file owner; these are cooperative workflow checks,
not signed attestations or an authorization service.
