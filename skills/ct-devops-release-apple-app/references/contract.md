# Store release input/output contract

This skill uses the strict envelope and schema in [assets/contract.json](../assets/contract.json).
Use Python 3.10+ and the complete installed folder; no provider SDK or credentials
are needed for offline validation. Examples are synthetic, blocked handoffs.

## Intake and commands

The agent prepares `input.json`, not a user questionnaire. Envelope fields are
`schema_version: 1`, `project_id`, `request`, nullable `repository`, `ledger` and
`definition`, `constraints`, `sources`, and `inputs`. Source references are
`{id, path, sha256}`; other file references are `{path, sha256}`. Paths resolve
relative to the intake file. Digests pin actual file bytes. Repository identity
contains `{path, revision, working_tree_sha256}` from `inspect-repository`.
Preserve the source intake as history when refreshing identity after authorized
changes; successful command proof must match the final source fingerprint.
Existing app releases do not require a newly invented product definition. Supplied
ledger/definition pairs are validated; all questions reuse the scope's 10/2 budget.
The bundled [definition contract](definition-contract.md) documents ledger commands.

`inputs` binds candidate revision, `platform_variant` (Apple OS or Android),
provider `app_id`, bundle/package `application_id`,
marketing `version`, `build_number`, requested `target_stage`, actual `track`,
nullable exported `artifact`, logical `credential_refs`, `authorization_source`,
`authorized_stage`, `require_device_proof`, `audience`, `countries`, and `rollout_percent`.
Apple app IDs are App Store Connect numeric IDs; Android app IDs equal the package
identifier. Apple exports are `.ipa` or `.pkg`; Android uploads are `.aab`.
Artifact references resolve to real private files, never signing credentials.
Credential references contain only `provider` (`env`, `keychain`, `secret-manager`)
and a logical `name`; inline values and extra fields are rejected. These fields
name prerequisite stores, not a credential lookup or an authorization grant.
Keep tester identities and signing/account details out of public examples.

Run using an absolute skill path (use `py -3` instead of `python3` on Windows):

```text
python3 <skill>/scripts/workflow.py inspect-repository <repository>
python3 <skill>/scripts/workflow.py validate-input /private/input.json
python3 <skill>/scripts/workflow.py record --cwd <repository> --output /private/build-proof.json --timeout 60 -- <explicit-build-command>
python3 <skill>/scripts/workflow.py validate-output /private/input.json /private/output.json
python3 <skill>/scripts/workflow.py render /private/input.json /private/output.json --output /private/report.md
```

`record` executes only the supplied argv without a shell or automatic retry. Review
its effects first; never supply secrets in argv or capture them in stdout/stderr.
Keep proof outside the measured checkout or in an already ignored private directory.
For longer builds use the repository's established evidence capture; do not claim
a 60-second timeout is a build failure diagnosis. New output paths refuse overwrite.

## Output and milestone checks

The envelope is `schema_version`, `project_id`, `skill`, `input_sha256`, `status`,
`summary`, `constraints`, `evidence`, `blockers`, `result`. The canonical input
SHA-256 is UTF-8 sorted-key compact JSON, preserving Unicode. `ready` has no
blockers; `blocked` has actionable `{reason, next_action}` entries and never means
release completion. Preserve intake/definition constraints. Evidence entries are
`{id, kind, reference}`, where kind is command, artifact or observation. Use `record`
for command proofs; see the bundled workflow's help and the platform guide.

Result binds the candidate and actual artifact digest. It includes a passing
`build_check`, five checked areas (`tests`, `signing`, `compliance`, `recovery`,
`tracking`) with evidence, nullable `store_readback`, `testing_readback`,
`device_proof` and `acceptance_source`, exact requested `outcome`, recovery and
limitations. A ready outcome equals the requested phase. Record unresolved
required checks or permissions as blocked rather than relabeling them passed.
Prepare cannot claim provider milestones. Later phases require an actual source
reference for authorization scoped to that phase. Production also requires
candidate-bound testing evidence and a human acceptance source. These are
cooperative records, not authenticated signatures or an authorization service.

## Sanitized provider readback

A store readback is artifact evidence referencing exact JSON, never an opaque
status sentence. Do not publish real provider receipts or runtime artifacts.
Use exactly these fields:

- `kind: "ct-store-readback.v1"`, `platform: "apple"` or `"android"`.
- `platform_variant`, `app_id`, `application_id`, `version`, `build_number`, `candidate_revision`,
  `artifact_sha256`: match the inspected candidate and export.
- `stage`, `track`: requested phase and exact provider track. Apple prepare/upload
  use `none`, TestFlight uses its named phase, App Review/production use `app-store`.
  Android prepare/upload use `none`, internal uses `internal`, open uses `beta`,
  production uses `production`; closed uses the actual closed-track identifier.
- `observed_at`: timezone-qualified ISO timestamp, refreshed within an hour.
- `source`: sanitized provider HTTPS URL without credentials, query or fragment.
- `native_status`: verbatim provider status; preserve the actual Console/API fact.
- `distribution_status`: normalized `uploaded`, `processing`, `available`,
  `submitted`, `published`, `draft`, or `halted`, based on that observation.
- `review_status`: `not-required`, `not-submitted`, `pending`, `approved`, `rejected`.
- Boolean `testers_configured`, `tester_access_verified`, `compliance_complete`,
  `production_access`; `external_eligible` is Boolean for Apple, null for Android.
- `audience`, `countries`, `rollout_percent`: actual observed scope, matching intake.
- `public_url`: null until relevant, then the exact app's public store URL.

Testing needs available distribution, configured testers, verified access and
satisfied review. Apple external testing needs satisfied beta review (approved, or explicitly
not required by the provider for that build); every Apple
upload must remain external eligible. Android availability needs `completed` or
`inProgress`, with 100 percent or a matching partial rollout; an edit/draft or
halted rollout is insufficient. Open testing requires confirmed eligibility.
Upload may be processing, but cannot claim testing. App Review submission needs
Waiting for Review/In Review, not Ready for Review. Apple testing availability
accepts only the requested lane's `Testing` / `IN_BETA_TESTING` state; unknown
states remain blocked until reviewed against current provider documentation. Production needs public
availability, correct storefront identity, country/rollout scope and actual
eligibility. Refresh provider facts again immediately before mutation; the hour
bound only rejects old evidence, it cannot prevent changes after observation.
Production testing readback can have a different testing audience/rollout, but
must name the identical source, export and version/build. This validator checks
normalized relationships and some native-state contradictions; it is not a full
provider state-machine adapter and does not call either store.

## Candidate-bound human decisions

An authorization source references JSON containing `kind:
"ct-store-authorization.v1"`, `platform`, `platform_variant`, `app_id`, `application_id`, `version`,
`build_number`, `candidate_revision`, `artifact_sha256`, `source`, `observed_at`,
`authorized: true`, `target_stage`, `track`, `audience`, `countries`, `rollout_percent`.
Bind it to the exact candidate and requested action/audience. `source` records the
actual user instruction or trusted approval reference; do not generate permission
from a recommendation or validator result.

A production acceptance source references JSON with `kind:
"ct-store-acceptance.v1"`, the same candidate fields, `source`, `observed_at`,
and `accepted: true` (omit authorization-only scope fields). Capture the actual
human acceptance and its limitations; never fabricate consent from silence. The
script rejects declared identity contradictions but cannot authenticate the actor.

## Device proof and limits

Group attachment, invitation and verified tester access are distinct from install
and smoke proof. If requested, provide artifact JSON with exactly `kind:
"ct-device-proof.v1"`, `platform`, the seven candidate identity fields above,
`observed_at`, `installed: true`, `smoke_passed: true`, and nonempty `limitations`.
Without it, report device proof unavailable. A public rollout percentage is scoped
availability, not proof that every eligible device has received an update.

File bindings and structured checks reject mismatches; they do not authenticate
human authorship, prove that a build was signed correctly from arbitrary text,
validate a live token, or establish that an observation is true. Human review owns
those judgments. No secret loading, upload, tester invitation, review submission,
production action, or paid operation is performed by validation or installation.
