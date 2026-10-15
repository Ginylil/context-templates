# Development plan contract

Use UTF-8 JSON, exact documented fields, integer `schema_version: 1`, and
nonempty text. IDs are lowercase hyphenated slugs. Duplicate JSON keys and
nonfinite numeric constants fail. Keep working artifacts outside the installed
skill. `assets/example-plan.json` matches the supplied synthetic definition and
ledger. The bundled `definition.py` is a byte-for-byte copy of the definition
skill validator; maintain it through canonical synchronization, never independent
changes. It replays the original ten-question/two-batch ledger.

## Commands and imports

```text
python3 <skill>/scripts/plan.py validate ledger.json definition.json plan.json
python3 <skill>/scripts/plan.py prepare ledger.json definition.json plan.json --output payload.json
python3 <skill>/scripts/plan.py verify-tracking ledger.json definition.json plan.json tracking.json
```

Use `py -3` on Windows. All commands return JSON/exit 0 on success; blocked,
malformed, inaccessible, or conflicting state returns stderr/exit 1. Preparation
requires an existing parent directory and refuses every existing output file.
There is no overwrite, reset or network mutation option. Imports expose
`validate_plan(ledger, definition, plan)` (returns the plan or raises ValueError),
`digest(value)` (canonical SHA-256), `prepare(...)` and `verify_tracking(...)`.
Never interpret `valid-local-plan` or `prepared` as planning completion.

`verify_tracking(..., require_backlog=False)` is an import-only ongoing readback
mode for a project guide. It accepts open/closed Issues and progressed nonempty
Project Status values, while retaining all identity, digest, exact body, duplicate
and membership checks. Its result includes `tasks` records with `task_id`,
`issue_url`, `issue_state` and `project_status` from the live APIs. The default and
CLI remain strict initial-publication checks requiring open Issues in Backlog.
Ongoing mode permits acceptance checkbox progress (`[x]`/`[X]`) while requiring
the exact original criterion text and all source/digest bindings. Initial
Backlog verification still requires the exact unchecked publication payload.
Neither mode infers completion from a status label; the guide must compare live
tracking with its current evidence and repository lifecycle contract.

## Plan

| Field | Contract |
| --- | --- |
| `schema_version` | Integer 1 |
| `project_id` | Exactly the ready definition's scope ID |
| `plan_id` | Stable plan slug; retain across retries |
| `definition_sha256`, `ledger_sha256` | Canonical digests of the supplied artifacts |
| `tracking` | `{system: "github", repository: "owner/repo", project: "https://github.com/orgs/OWNER/projects/N"}`; `/users/OWNER/projects/N` also supported |
| `tasks` | Nonempty list of task records |

An already-declared definition tracking target must match exactly. Null targets
can be completed; they do not authorize creation of new remote resources.

Each task has exactly `id`, `title`, `outcome`, `depends_on`, `acceptance`, and
`status`. `status` is `backlog`. `depends_on` contains unique existing task IDs;
self references and every cycle fail. Task IDs are unique. `acceptance` is a
nonempty list of `{id, requirement_ids, criterion, verification}`. Acceptance IDs
are unique across the whole plan. Each `requirement_ids` list is nonempty and
references the definition's `success_criteria` IDs. Every success criterion must
be covered. Scripts cannot determine semantic coverage or sensible task size.

The deterministic payload has `{schema_version, project_id, plan_id,
plan_sha256, tracking, tasks}`. Each payload task has `{id, title, marker, body}`.
The stable HTML marker identifies scope/plan/task; a second marker binds the
entire plan digest, so content changes cannot silently reuse stale receipts.
Bodies include acceptance, dependencies and the authoritative scope, exclusions,
constraints, decisions and assumptions. They must be published without edits.

## Publication and recovery

1. Verify repository and Project identity and access; inspect existing `Status`
   options. Require `Backlog` explicitly. Do not rename fields or modify workflows
   to make verification pass without authorization.
2. Search/list all repository issues for the exact `<!-- ct-plan:... -->` marker,
   including closed issues. A matching current issue can be reused only when its
   title/body and intended lifecycle agree. Multiple matches, changed content,
   or an already-progressed item require explicit reconciliation. Never silently
   reset progressed work to Backlog. A changed plan requires review before edits.
3. Create missing issues from payload titles/body files; add them to the selected
   Project and select Backlog. Retain exact task IDs and dependency relationships
   in the deterministic body. Capture issue URLs and Project item identifiers.
4. After each ambiguous or failed write, inspect remote state before retrying.
   A partially published plan remains incomplete; retain the same marker IDs and
   recover only missing operations. No automatic deletion or rollback of issues.
5. Build the receipt below and run live verification. Do not execute tasks from
   a local-only graph or claim complete until readback succeeds.

The workflow may use runtime GitHub connectors. CLI users should consult
[GitHub CLI issue create](https://cli.github.com/manual/gh_issue_create),
[GitHub's Projects API guide](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)
and [gh api](https://cli.github.com/manual/gh_api) when writing. The readback script
uses paginated GET repository issues and GraphQL `projectV2.items` with
`fieldValueByName(name: "Status")`. It performs no writes. API/CLI availability
and authorization are checked at runtime; inaccessible evidence is a blocker.

## Tracking receipt

```json
{
  "schema_version": 1,
  "project_id": "follow-up-notes",
  "plan_id": "first-release",
  "plan_sha256": "canonical digest of the exact plan",
  "issues": [
    {"task_id": "save-private-note", "url": "https://github.com/example/follow-up-notes/issues/1"},
    {"task_id": "list-follow-ups", "url": "https://github.com/example/follow-up-notes/issues/2"}
  ]
}
```

There must be exactly one issue per task. Supplied URLs are declarations, not
proof. Live verification lists all repository issues to detect duplicate/stale
plan markers, requires matching exact title/body and an open Issue (not a PR),
then reads every Project item page and requires exactly one active membership
with `Status: Backlog`. Closed/inaccessible Projects, truncated responses, stale
digests and missing status values block completion. This is evidence at the time
of the command, not permanent certification or implementation acceptance.
