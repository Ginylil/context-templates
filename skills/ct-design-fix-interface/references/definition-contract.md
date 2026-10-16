# Project definition contract

All artifacts use UTF-8 JSON, integer `schema_version: 1`, exact documented fields,
and nonempty strings unless null or an empty list is explicitly allowed. Unknown
fields, duplicate JSON keys and nonfinite numeric constants are rejected.
Identifiers use lowercase letters/digits separated by single hyphens, starting
with a letter. Question IDs alone use `Q1` through `Q10`.

## Commands

Run `python3 <skill>/scripts/definition.py` on macOS/Linux, or `py -3` on Windows.
`<skill>` is the actual directory containing the installed `SKILL.md`. The
commands also work from a source checkout. Do not assume a particular agent path.
The following paths represent files in one existing, user-owned working directory:

```text
python3 <skill>/scripts/definition.py validate-input input.json
python3 <skill>/scripts/definition.py start input.json --ledger ledger.json
python3 <skill>/scripts/definition.py status ledger.json
python3 <skill>/scripts/definition.py apply ledger.json batch.json --expect-revision 0
python3 <skill>/scripts/definition.py apply ledger.json answers.json --expect-revision 1
python3 <skill>/scripts/definition.py validate-output ledger.json definition.json
python3 <skill>/scripts/definition.py render ledger.json definition.json --output definition.md
```

Use the revision actually returned by `status`; zero and one above are examples.
Successful commands return JSON and exit 0; validation/I/O errors go to stderr
and exit 1. A valid blocked definition exits 0 with `definition_status: blocked`:
artifact validity and planning readiness are different. New destinations require
an existing parent directory. `start` reuses a valid same-input ledger without
erasing events, and refuses a different input. `render` refuses any existing file.

`apply` validates the complete history before replacing the ledger atomically.
It refuses a stale revision or an existing `.lock` file. Exact retries with the
same event ID/content return `unchanged`, even if the revision has advanced;
reuse of an ID with changed content fails. An interrupted writer may leave a
lock; inspect the writer/state before explicitly removing that lock. Never
automatically delete it. A failed validation leaves ledger bytes unchanged.

## Input

`assets/example-input.json` is a complete synthetic input. Fields:

| Field | Meaning |
| --- | --- |
| `schema_version` | Integer `1` |
| `project_id` | Stable scope identifier; reuse across chats/agents for this interview |
| `idea` | The user's request, preserving its intent |
| `sources` | At least one `{id, reference, summary}` record; unique IDs; references identify the conversation, document, URL or repo path/revision |
| `constraints` | Unique strings; may be empty; must be retained in the output |
| `decisions` | Decision records below; may be empty when no decisions need modeling |
| `tracking` | `{system: "github", repository: string or null, project: string or null}` |

Tracking references are declarations, not verified remote objects. Preserve them
in the definition. A null target means selection is required before executable
task publication, not that local-only task execution is permitted. To change an
input tracking target, handle a reviewed follow-up; never silently substitute one.

A decision has exactly:

```json
{
  "id": "sharing",
  "topic": "Who can read a note",
  "depends_on": ["audience"],
  "blocking": true,
  "resolution": null
}
```

`depends_on` contains unique existing decision IDs. The graph must be acyclic.
`blocking` is a JSON boolean. A resolution is either null or
`{answer: nonempty string, source: nonempty string}`. A resolved decision must
have resolved prerequisites. Record known facts and supplied choices here before
asking; do not convert an unverified assumption into a sourced resolution.

## Ledger and events

The ledger is `{schema_version: 1, input: <validated input>, events: [...]}`.
The input is an immutable snapshot. Counters and current decisions are derived by
replaying all events; stored counters are not accepted. `status` returns revision,
usage/remaining limits, pending question and decision IDs, the current answerable
decision frontier, full decisions, and canonical input/ledger SHA-256 digests.
JSON indentation/key ordering do not change the digests.

Every event has a globally unique lowercase `id` in this ledger. An `ask` event
contains one entire presented batch, consuming one batch and all its questions:

```json
{
  "id": "batch-one",
  "type": "ask",
  "questions": [{
    "id": "Q1",
    "decision_id": "sharing",
    "prompt": "Who can read a note?",
    "options": ["Only its owner", "Selected collaborators"],
    "recommended_option": 0
  }]
}
```

`options` is empty for free text or contains 2–4 unique strings.
`recommended_option` is null or a zero-based integer index; it never supplies an
answer. Text answers are always allowed, including qualifications to a choice.
IDs increment across batches. Each decision may be asked once. Normalized exact
prompt duplicates are rejected, but semantic equivalence remains agent judgment.
All prerequisites must be settled **before** the batch. A pending batch prevents
another `ask`; a partially answered batch remains pending.

Record actual human responses, with a conversation reference in `source`:

```json
{
  "id": "answers-one",
  "type": "answer",
  "answers": [{
    "question_id": "Q1",
    "answer": "Only its owner; sharing is outside the first version.",
    "source": "User reply to Q1 in the current conversation"
  }]
}
```

Partial answers may arrive as separate uniquely named events. Empty answers and
answers to already-answered/unasked questions fail. There is no default-answer,
reset, delete-history, increase-budget, or reopen-question command.

Adapt after answers by adding decision branches:

```json
{
  "id": "add-export",
  "type": "add-decisions",
  "decisions": [{
    "id": "export",
    "topic": "Whether the first version needs note export",
    "depends_on": ["sharing"],
    "blocking": false,
    "resolution": null
  }]
}
```

All decision IDs remain unique across the complete history. For newly discovered
facts about **unasked** decisions use:

```json
{
  "id": "evidence-export",
  "type": "resolve",
  "resolutions": [{
    "decision_id": "export",
    "answer": "The supplied brief explicitly excludes export from version one.",
    "source": "Supplied brief, Exclusions section"
  }]
}
```

Resolved decisions cannot be overwritten. Contradictory later evidence should
become an explicit blocker in the definition, with a review action. The ledger
is a cooperative workflow guard, not tamper-proof storage: deliberate edits or
forked ledgers cannot be prevented without an external trusted store. Preserve
the existing file, retain it in project history when appropriate, and share its
path when handing off the same scope. Do not include private ledger data in a
public repository without reviewing its destination and audience.

## Definition

`assets/example-definition.json` matches `assets/example-ledger.json`, whose
history contains the bundled input, batch and answers examples. Every output
has these exact fields:

| Field | Required value |
| --- | --- |
| `schema_version`, `project_id` | `1` and the input scope ID |
| `input_sha256`, `ledger_sha256` | Current digests returned by `status` |
| `status` | `ready-for-planning` or `blocked` |
| `title`, `problem`, `desired_outcome`, `next_action` | Nonempty strings |
| `users`, `in_scope`, `out_of_scope` | Nonempty lists of unique nonempty strings |
| `success_criteria` | Nonempty list of `{id, criterion, verification}` with unique IDs and observable verification methods |
| `constraints` | Unique strings, containing every original input constraint |
| `decisions` | All settled decisions in ledger order, as `{id, answer, source}`; copy exactly from the derived state |
| `assumptions` | List of `{decision_id: unresolved ID or null, statement, impact}` |
| `blockers` | List of `{decision_id: unresolved ID or null, reason, next_action}` |
| `tracking` | Exactly the input tracking declaration |

All unresolved decisions need an assumption or blocker. Blocking decisions and
pending questions require blockers. Additional risks or contradictions can use
null `decision_id`. Any blocker requires `status: blocked`; blocked status must
contain at least one actionable blocker. An unanswered question cannot be treated
as a resolved choice. Nonblocking unasked decisions may remain explicit assumptions.
Each unresolved decision appears in exactly one of those lists; it cannot be
both an assumption and a blocker. No extra questions are needed just to fill the
budget or complete every branch.

Success criteria and verification text are checked for presence and unique IDs,
not semantic quality. The agent must judge relevance, measurability, contradictory
scope and evidence strength. Source references are not fetched or authenticated.
The renderer validates again, emits a deterministic readable brief including
pending question prompts/options, and refuses to overwrite prior user output.
Check it with the same ledger used for the JSON. Rendering does not record
another batch or answer any pending question.
