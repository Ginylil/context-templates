# Contract and command guide

The policy is [assets/contract.json](../assets/contract.json). It uses a small
strict schema vocabulary implemented by the bundled validator, not JSON Schema.
Read the domain fields there before authoring a handoff. Examples are synthetic,
blocked reports, not demonstration of actual project acceptance.

## Input

The exact top-level fields are `schema_version` (1), `project_id` (slug),
`request`, `repository` (null or `{path, revision, working_tree_sha256}`), `ledger` and `definition`
(null or `{path, sha256}`), `constraints` (strings), `sources`
(`{id, path, sha256}` records), and domain-specific `inputs`. Repository revision
identifies the inspected Git HEAD; relevant engineering candidates bind to that
revision and successful command proofs bind the working-tree digest. Describe
uncommitted changes explicitly rather than labeling them as a deployed SHA.
References resolve relative to the input JSON directory. Use actual file-byte
SHA-256 values. A supplied definition must be bound to its matching ledger and
project. A ready report needs a ready definition when `requires_definition` is
true. Review/bug/setup-improvement tasks can run without inventing a definition.
Requirement references resolve to the bound definition's `success_criteria` IDs;
source references resolve to the supplied source IDs. Preserve both input and
definition constraints in the output.

## Output

Use exactly `schema_version`, `project_id`, `skill`, `input_sha256`, `status`,
`summary`, `constraints`, `evidence`, `blockers`, and `result`. The input digest is
SHA-256 of UTF-8 JSON with sorted keys, compact separators, and Unicode preserved.
`status` is `ready` or `blocked`; ready has no blockers, blocked has at least one
`{reason, next_action}`. Every evidence entry has `{id, kind, reference}` where
`kind` is `command`, `artifact`, or `observation`, and `reference` is an actual
`{path, sha256}` file binding. Use command-proof JSON produced by `record` for
command evidence. An observation file has `kind: ct-observation.v1`, `source`,
`observed_at` (an ISO timestamp with timezone), `statement`, and `limitations`.
An artifact may be a real design document, screenshot, patch, or other deliverable;
a digest establishes identity and does not establish correctness.

Domain result fields:

- `scenarios`: array.
- `execution_order`: array.
- `excluded_checks`: array.
- `test_plan_artifact`: string. May be null while blocked.

Ready-only deterministic rules:

- `coverage`: `{"field": "requirement_ids", "items": "scenarios"}`.
- `nonempty`: `{"fields": ["scenarios", "test_plan_artifact"]}`.
- `cover-target`: `{"field": "scenario_id", "items": "execution_order", "target": "scenarios", "target_field": "id", "target_result": true}`.

These rules supplement semantic review. Validators cannot infer whether a
scenario is useful, whether a reported diagnosis explains the failure, whether a
screenshot is readable, or whether a finding is correct. Blocked outputs still
have valid field types and references; they may leave nullable proofs null and
result collections empty. They cannot claim ready-only guarantees.

## Commands

Run from any working directory with Python 3.10+; paths below are examples of
project-owned handoff files, not artifacts shipped by the skill:

```bash
python /path/to/skill/scripts/workflow.py validate-input /work/input.json
python /path/to/skill/scripts/workflow.py record --cwd /work/repository --output /work/test-proof.json --timeout 30 -- python -m unittest
python /path/to/skill/scripts/workflow.py validate-output /work/input.json /work/output.json
python /path/to/skill/scripts/workflow.py render /work/input.json /work/output.json --output /work/brief.md
```

`record` runs the explicit argv and writes exit status, timeout, output, source
revision, and working-tree identity. It does not select commands or grant
permission. Inspect commands from untrusted repositories before executing them;
never put secrets in argv or publish captured private output. A nonzero exit can
be valid evidence of an intentional regression, but it must fail for the reported
reason. Compare before and after conditions, including data and environment.
The same-command rule checks invocation comparability, not causal correctness.
Keep proof files outside the source repository or in an already ignored evidence
directory. Recording proof into the inspected tree would change its digest.
A candidate revision is the inspected Git HEAD with separately fingerprinted
working changes; a final commit or deployment needs its own recorded identity.

Use `python /path/to/skill/scripts/definition.py --help` for the shared interview
commands. Maintain one ledger for the scope. Ask events count when recorded,
including unanswered questions; at most ten questions and two batches are allowed.
The ledger's history checks cannot authenticate a user's answer or detect every
compound or semantically duplicated question; the agent must enforce that intent.

## Standalone question ledger

If questions are necessary and no ledger exists for this scope, prepare a
separate `interview-input.json` with exactly:

```json
{
  "schema_version": 1,
  "project_id": "example-project",
  "idea": "The actual user request",
  "sources": [{"id": "request", "reference": "Current user message", "summary": "The supplied request"}],
  "constraints": [],
  "decisions": [{"id": "hosting", "topic": "Where this app must run", "depends_on": [], "blocking": true, "resolution": null}],
  "tracking": {"system": "github", "repository": null, "project": null}
}
```

Use the actual workflow project ID, known constraints, sources, tracking targets,
and consequential decisions. Sources need at least one entry. A known decision
has `resolution: {"answer": "Actual supplied choice", "source": "Its source"}`;
unknown choices have null resolution. Dependencies reference existing decisions
and must be acyclic. Inspect prior history before starting: this template does
not authorize a new budget for an existing interview.

```bash
python /path/to/skill/scripts/definition.py start /work/interview-input.json --ledger /work/ledger.json
python /path/to/skill/scripts/definition.py status /work/ledger.json
python /path/to/skill/scripts/definition.py apply /work/ledger.json /work/event.json --expect-revision 0
```

Use the revision actually returned by `status`. An ask event is
`{"id":"batch-one","type":"ask","questions":[{"id":"Q1","decision_id":"hosting","prompt":"Where must the app run?","options":[],"recommended_option":null}]}`.
One event is one entire displayed batch. Add independent questions to the same
`questions` array; use sequential `Q1` through `Q10` across the interview.
Options may be empty for free text or contain 2–4 distinct choices with a null
or zero-based recommendation index. Record the batch before displaying it;
a recommendation is not an answer.

An answer event is
`{"id":"answers-one","type":"answer","answers":[{"question_id":"Q1","answer":"The actual user answer, including qualifications","source":"User reply to Q1"}]}`.
Partial answers are valid and remain pending. Each event ID is unique; uncertain
retries reuse its exact content. `apply` refuses stale revisions and invalid
history without replacing the ledger. It cannot authenticate answers or detect
every semantic duplicate/compound question, so the agent must check those.

For a later branch, apply
`{"id":"add-domain","type":"add-decisions","decisions":[{"id":"domain","topic":"Whether a custom domain is required","depends_on":["hosting"],"blocking":false,"resolution":null}]}`.
To settle an unasked choice from evidence, apply
`{"id":"resolve-domain","type":"resolve","resolutions":[{"decision_id":"domain","answer":"Actual evidenced choice","source":"Supplied source"}]}`.
Do not overwrite settled decisions, silently resolve asked questions, or erase
history after a conflict. Record a blocker instead. After the ledger changes,
refresh its file-byte SHA-256 binding in the workflow input. If a bound definition
is now stale, obtain a freshly validated definition against the updated ledger
before a ready handoff; never modify its digest alone to imply validation.

## Completion boundary

Ready means the test plan covers the agreed outcomes; no scenario has passed merely because the plan validates.

## Current source binding

Use `python3 <skill>/scripts/workflow.py inspect-repository <repo>` to obtain
`{path, revision, working_tree_sha256}` when a repository is supplied. Keep proof
files outside that repository or in an ignored directory. After authorized code
changes, retain the earlier intake as history, refresh the current intake source
fingerprint, and bind the output to its new digest. Preserve the original scope,
constraints and interview answers. Passing checks must match this final source
state; an earlier failing reproduction can retain its historical source binding.
