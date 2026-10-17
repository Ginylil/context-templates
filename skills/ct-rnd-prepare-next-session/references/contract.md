# Handoff contract

All JSON uses schema version integer `1`. Unknown/missing fields, duplicate JSON
properties, non-finite numbers and known credential/signing-file signatures are
rejected. Private filename checks include uppercase `.ENV` variants. Text fields
are nonempty single lines without control characters;
lists of strings contain distinct entries. Helpers use Python 3.10+ only and
never run project code, shell commands, Git or network requests.

## Input

The exact fields are:

| Field | Value |
| --- | --- |
| `schema_version` | Integer `1` |
| `scope` | `{description, workspace}`; workspace is an existing absolute directory or `null` when unknown/non-repository |
| `request` | User's handoff request and relevant intent |
| `constraints` | Array of preserve/do-not-touch instructions |
| `continuation` | `needed`, `blocked`, `complete`, or `undecided`; agent judgment, not automatically detected |
| `selected_next_action` | Exact already agreed objective, or `null`; completed scope requires `null` |
| `sources` | Nonempty array of source records below |

Each source has exactly `id`, `kind`, `location`, `status`, `checked_at`,
`reference`. IDs are distinct lowercase hyphenated identifiers. `kind` is `file`,
`git`, `github`, `conversation` or `artifact`. `location` is a safe human-readable
locator, such as a path or sanitized issue URL. Kind `file` uses its reference
path as the location. Keep task-specific machine paths only in private runtime
input; public examples use synthetic relative files and unknown workspace.

`status: verified` requires a timezone-qualified ISO timestamp and
`reference: {path, sha256}`. The referenced regular file must exist, contain no
detected signing-file/credential material, fit within 2 MB, and match the actual
lowercase SHA-256 of its bytes. Relative paths resolve against the input JSON's
directory, never the current directory or output JSON's directory. File links
are refused. Timestamps cannot be naive or more than five minutes in the future.
Old timestamps are visible evidence, not automatic claims of freshness.

For `git`, `github` and `conversation`, reference a sanitized saved observation.
The script checks that file, not the underlying provider or truth of its contents.
Capture current Git/worktree and relevant live remote state before classifying
claims. These records do not authenticate an agent, author, command or approval.

`status: unverified` requires `checked_at: null` and `reference: null`. Preserve
the locator and explain exactly how to verify it in output. Include at least a
sanitized user-request/conversation source even for non-repository work.

## Output

The exact fields are:

| Field | Value |
| --- | --- |
| `schema_version` | Integer `1` |
| `input_sha256` | Canonical digest printed by `hash-input`; computed from this input |
| `status` | `ready`, `blocked`, or `no-follow-up`; describes handoff preparation, not product acceptance |
| `summary` | Concise handoff result |
| `read_first` | Array of `{source_id, instruction}`; nonempty for a continuation |
| `verified_state` | Array of `{statement, source_ids}` with at least one verified source per claim |
| `unverified_state` | Array of `{statement, check_first, source_ids}`; every unverified input source must appear |
| `decision_frame` | `{deciding, not_deciding, reason}`; string arrays, with at least one deciding item and a selection rationale |
| `objective` | One immediate objective string, or `null` for no follow-up |
| `objective_kind` | `continue-work`, `resolve-blocker`, `establish-next-action`, or `none` |
| `constraints` | Exact input constraint list, in the same order |
| `validation` | Array of `{instruction, previous_result, source_ids}`; exact useful commands or manual checks |
| `blockers` | Array of `{reason, next_action}`; nonempty exactly when status is blocked |
| `final_response` | Nonempty distinct string list describing the next agent's report |

`previous_result` is `passed`, `failed`, `blocked` or `not-run`. Passed/failed
checks require at least one verified source. Do not claim an executed command
from a plan, source search or an unverified source. Empty `validation` is valid
when no meaningful check applies; do not invent commands to fill a template.

Needed scope can yield ready or blocked output. Blocked input always yields a
blocked handoff with `resolve-blocker`. Undecided input uses
`establish-next-action` when ready, or blocker resolution when blocked. Completed
input always yields `no-follow-up`, objective `null` and kind `none`. A selected
next action must be retained exactly in ready output. All referenced source IDs
must exist. The script cannot determine whether a string contains multiple
substantive goals; that remains part of prompt review.

## Commands and output files

```text
python3 <skill>/scripts/handoff.py validate-input input.json
python3 <skill>/scripts/handoff.py hash-input input.json
python3 <skill>/scripts/handoff.py validate-output input.json output.json
python3 <skill>/scripts/handoff.py render input.json output.json --prompt next-session.txt
```

The input SHA-256 uses sorted-key compact JSON, preserved Unicode and UTF-8.
Source hashes identify actual file bytes. Neither is a credential. Public example
hashes are generated by `make resources`; `make check` rejects stale fixtures.

Rendering revalidates sources and input/output bindings before writing plain
UTF-8 text. The output parent must already exist. Store runtime artifacts outside
the installed skill and inspected workspace. Existing different files and links
are refused; identical existing regular files return `unchanged` without a write.
No command creates a chat, publishes content or changes repository state.

Deliver the rendered prompt as a single text block after a concise note naming
material gaps. `no-follow-up` renders a short completion note instead of a new
task. Validators enforce consistency of declarations, not semantic completeness,
fresh remote state, factual truth, acceptance or permission. Secret checks are
heuristic; inspect for private identifiers and context that signatures cannot
recognize before sharing a handoff.
