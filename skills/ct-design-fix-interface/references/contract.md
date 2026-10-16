# Interface correction contract

The agent fills [assets/contract.json](../assets/contract.json) from the report,
inspected source and actual rendered evidence. Bundled examples are synthetic
blocked intakes, not private app data or proof of a completed repair. Python
3.10+ and Git suffice for validation. Use the project's browser harness to obtain
real screenshots and interaction/regression proof; no browser is bundled.

## Commands and evidence sequence

Use absolute installed skill paths (`py -3` instead of `python3` on Windows):

```text
python3 <skill>/scripts/interface.py --repository <repo> --root . --term ActionButton --term overflow --output /private/before-scan.json
python3 <skill>/scripts/workflow.py inspect-repository <repo>
python3 <skill>/scripts/workflow.py validate-input /private/input.json
python3 <skill>/scripts/workflow.py record --cwd <repo> --output /private/before-check.json --timeout 60 -- <actual-regression-argv>
```

Choose meaningful search terms from the actual owner, symptom and aliases; the
names above are examples. Repeat `--root` and `--term` for all relevant frontend
roots and aliases. Review the generated file list and inspect component callers,
route families, runtime-only variants and alternate implementations manually.
The scanner reads Git-listed tracked/nonignored source with supported frontend
extensions, excluding generated/dependency folders. It performs case-sensitive
literal search, reports paths/line numbers/terms and source digests without line
contents, and never runs project code or changes it. Large, unreadable or linked
source is reported as skipped; resolve those gaps before a ready handoff. Ignored
files, unsupported extensions and semantic equivalence remain explicit limits.
Never put credentials or private content in search terms or public examples.

Keep scans, screenshots, ledgers and command proof outside the measured repository
or in an already ignored private evidence directory. New output paths refuse
overwrite. Capture the baseline scan and failing regression from the same source
state; retain both after edits. Preserve the initial intake as history. After
fixing, record the same regression plus related checks/build, capture renders,
create a new final scan with the same roots/terms, and refresh the intake's current
repository fingerprint and output input digest. Do not replace the baseline scan.

```text
python3 <skill>/scripts/interface.py --repository <repo> --root . --term ActionButton --term overflow --output /private/after-scan.json
python3 <skill>/scripts/workflow.py hash-input /private/input.json
python3 <skill>/scripts/workflow.py validate-output /private/input.json /private/output.json
python3 <skill>/scripts/workflow.py render /private/input.json /private/output.json --output /private/report.md
```

`record` executes exactly the supplied argv without a shell or retries. Inspect
its effects and output first; never capture secret-printing commands. Keep using
the established project harness; a passing unrelated command is not UI proof.

## Input and clarification

The shared envelope is `schema_version`, `project_id`, `request`, nullable
`repository`, `ledger`, `definition`, `constraints`, `sources`, and `inputs`.
Repository is `{path, revision, working_tree_sha256}` from `inspect-repository`.
File references are `{path, sha256}` with actual file-byte hashes, resolved from
the intake directory; source references also include a unique `id`.

Inputs contain current `candidate_revision`, `reported_behavior`, nullable
`expected_behavior`, `understanding_source` (user-report/repository-evidence/
user-answer/unresolved), `understanding_source_ids`, nullable
`understanding_question_id`, `search: {roots, terms}`, nullable `before_scan`,
`viewports: [{id, width, height}]` and the exact `reproduction_argv`.
A design/working-example interpretation needs source references. A user-answer
interpretation needs a real answered question in the shared ledger. Explicit,
clear reports need no redundant confirmation. Unresolved intent cannot authorize
a correction. Existing defects require no fresh product definition; supplied
ledger/definition history is still checked.

When a correction or variant is uncertain, record and ask a relevant question in
the shared ten-question/two-batch ledger. Dependent alternatives belong in a later
batch, not as hidden conditional questions. See [definition-contract.md](definition-contract.md)
for init/apply/status commands. An unknown or unanswered question cannot be used
as an agreed answer, and silence cannot settle one. Update file-byte bindings
after ledger changes. Hold files with uncertain corrections unchanged; a shared
owner that affects one must wait too. Independent confirmed files can proceed.

## Output, coverage and completion

The output envelope is `schema_version`, `project_id`, `skill`, `input_sha256`,
`status` (ready/blocked), `summary`, `constraints`, `evidence`, `blockers`, `result`.
Compute `input_sha256` with `hash-input` (canonical compact sorted-key UTF-8 JSON,
preserving Unicode). `make resources` derives the synthetic example's input hash;
check/build reject stale generated output. File/artifact hashes bind real bytes,
not a copied example value. Evidence is `{id, kind, reference}`. `record` produces
command proof; artifacts reference actual files. Observations reference JSON with
`kind: ct-observation.v1`, `source`, timezone-qualified `observed_at`, `statement`,
`limitations`; record what was actually inspected and what remains unverified.

Result includes current `candidate_revision`, exact agreed `expected_behavior`,
`root_cause`, nullable `after_scan`, and:

- `scope_review`: inspected `routes`, `components`, `additional_searches`, explicit
  `exclusions: [{path, reason}]` and nonempty `limitations`. Source search alone
  cannot establish semantic or whole-project coverage.
- `occurrences`: unique `id`, repository-relative `path`, nonempty `owner_paths`, context, `scan_matches`
  (`[{phase: before|after, match_id}]`), `verdict` (fixed/intentional/uncertain),
  specific `rationale`, nullable `question_id`, `evidence_ids`, and `surface_ids`.
  Each match in both scans must be classified exactly once for a ready result.
  Group matches from the same file/semantic occurrence; add manual occurrences
  for consumers or aliases found outside literal search. Intentional means a
  justified preserved variant, not an uninspected match. Uncertain requires a
  pending ledger question and unchanged occurrence/owner files. List the actual
  shared component/style/token owners in `owner_paths`; an unchanged consumer
  does not make it safe to edit a shared owner that affects it. Answered decisions keep
  their question ID when reclassified.
- `surfaces`: unique `id`, linked `occurrence_ids`, exact `route`, interaction
  `state`, `viewport_id`, `before`/`after` screenshot evidence IDs, `inspection`
  observation ID, passing `interaction_check` command ID and `status`.
  Capture comparable viewport PNGs at device scale 1, with the declared width
  and height. Check the same route, state, content and environment; explain any
  unavoidable difference rather than comparing unrelated screens. All fixed
  occurrences need rendered coverage at every declared viewport; surfaces may
  cover multiple occurrences when they share the actually tested route/state.
- `before_check`, `after_check`, `related_check`, `build_check`: command IDs. Before
  must fail for this defect; after reruns identical argv/cwd and passes against
  final source. Related/build checks must also pass against final source. The
  baseline scan must match the failing proof's revision/worktree fingerprint;
  final scan is regenerated and compared to the actual current source.
- `staging_handoff`, `remaining_limits`: exact deployed candidate and required
  human testing, or an explicit unavailable/not-deployed/no-staging boundary.

Blocked reports retain actionable `{reason, next_action}` entries, partial
confirmed work, uncertainty and untested areas. Ready requires a clear correction,
complete bounded inventory classification, at least one corrected occurrence,
no uncertainty, no skipped scan sources and matching rendered/command evidence.
The script checks source/file bindings, PNG headers/dimensions, classifications,
ledger relationships and declared proof, not semantic intent, visual quality,
browser authenticity or human acceptance. The agent must actually inspect the
renders and context. Arbitrary text or synthetic fixtures cannot prove a live UI.
