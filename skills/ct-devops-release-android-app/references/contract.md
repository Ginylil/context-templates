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
nullable provider `app_id`, bundle/package `application_id`,
nullable marketing `version` and `build_number`, requested `target_stage`, actual `track`,
nullable exported `artifact`, logical `credential_refs`, `authorization_source`,
`authorized_stage`, `require_device_proof`, `audience`, `countries`, and `rollout_percent`.
Apple app IDs are App Store Connect numeric IDs; Android app IDs equal the package
identifier. Apple exports are `.ipa` or `.pkg`; Android uploads are `.aab`.
Artifact references resolve to real private files, never signing credentials.
Credential references contain only `provider` (`env`, `keychain`, `secret-manager`)
and a logical `name`; inline values and extra fields are rejected. These fields
name prerequisite stores, not a credential lookup or an authorization grant.
Keep tester identities and signing/account details out of public examples.
For new setup, IDs/version/build may be null until discovered; actual release
phases require all four. `setup_mode` is `existing-native` or `wrap-web`;
`requested_capabilities` contains applicable kebab-case areas such as
`authentication` or `deep-links`. `build_exposure_prefixes` records any custom
uppercase client-inlining prefixes, in addition to the standard checked ones.
Nullable `discovery` references the generated snapshot by path and actual file
SHA-256. Follow [the setup guide](setup.md) for the selected platform/framework.

Run using an absolute skill path (use `py -3` instead of `python3` on Windows):

```text
python3 <skill>/scripts/configuration.py --repository <repository> --platform android --output /private/discovery.json
python3 <skill>/scripts/workflow.py inspect-repository <repository>
python3 <skill>/scripts/workflow.py validate-input /private/input.json
python3 <skill>/scripts/workflow.py hash-input /private/input.json
python3 <skill>/scripts/workflow.py record --cwd <repository> --output /private/build-proof.json --timeout 60 -- <explicit-build-command>
python3 <skill>/scripts/workflow.py validate-output /private/input.json /private/output.json
python3 <skill>/scripts/workflow.py render /private/input.json /private/output.json --output /private/report.md
```

`record` executes only the supplied argv without a shell or automatic retry. Review
its effects first; never supply secrets in argv or capture them in stdout/stderr.
Keep proof outside the measured checkout or in an already ignored private directory.
For longer builds use the repository's established evidence capture; do not claim
a 60-second timeout is a build failure diagnosis. New output paths refuse overwrite.

## Configuration discovery and setup report

`configuration.py` reads Git-listed project structure, recognized dependency names
and literal environment references from source. It reports names and locations,
never environment values or private-key contents. Keep `.env` files and signing
files ignored and untracked: recognizable private filenames in Git's public set
block discovery and store source binding before content hashing. Public
`.env.example`/`.env.template` files must contain placeholders only and remain
part of the ordinary source fingerprint. Run this preflight before capturing
source identity. Private discovery output includes absolute local paths; never
commit it to the public catalog. No project script, install, build, dashboard
request or secret lookup runs during discovery.

The snapshot includes repository identity, configuration paths, detected framework
hints, literal environment names/source paths, environment file paths/ignore state,
skipped sources and limitations. Validation regenerates it and rejects drift.
This is a bounded heuristic, not a parser for arbitrary loaders, CI variables or
platform settings: the agent must review those manually and include every
applicable setting/capability in the inventory.

`result.configuration` is an inventory with unique `id`, `area`, `name`, `purpose`,
`required`, `status`, exact `location`, `setup_action`, `verification`, `storage`,
`sensitive`, `bundled`, `user_action`, and `evidence_ids`. Status is `configured`,
`missing`, `invalid`, `not-applicable` or `unverified`. The required baseline areas
are app-identity, toolchain, runtime, native-project, build-export, signing,
upload-auth, store-record, store-metadata, privacy-permissions, testing, recovery,
and tracking, plus requested capabilities. Multiple settings may share an area.
Discovered literal environment names must each have a runtime row. Mark an
inapplicable item explicitly with its reason; do not use that to skip core setup.

`result.setup_plan` provides one actionable entry per unresolved required item:
`configuration_id`, `action`, `where`, `verification`, `owner` (`agent` or `user`),
`status` (`pending`, `done`, `blocked`), `evidence_ids`. Configured rows and done
steps need evidence. Report exact files, loader, target or dashboard section,
never merely "configure .env". `environment_loader` describes the real loading
mechanism, precedence and environment. Configured local secrets require an
existing ignored file and a named loader; secrets must never use client-exposed
prefixes or be bundled. CI injection does not make a shipped value private.

`result.wrapper` records `mode` (unknown/unsupported/existing-native/capacitor/
expo/react-native/custom), `source_kind` (unknown/native/static/ssr/remote),
`delivery` (undecided/native/bundled/hosted), actual `config_files`, nullable
`web_output_dir` and `runtime_url`, `backend_plan`, `native_targets`, nullable
command-evidence IDs `sync_check` and `smoke_check`, and nonempty `limitations`.
A web wrap needs a supported route, selected native target, existing config files,
passing sync/smoke command evidence and either built web output containing
`index.html` or a supported production HTTPS hosted route. Capacitor hosted
`server.url` is rejected as a production route. SSR needs an explicit backend
plan. Capacitor targets are limited to iOS/Android; other platforms need their
own selected route. Existing native routes also require passing native smoke
command evidence. These structural checks supplement agent inspection of effective native
settings and actual runtime behavior; they cannot establish those facts alone.

A ready `discover` means the inventory and actionable setup plan are complete;
missing settings can remain. It requires current discovery and cannot claim an
export or provider milestone. A ready `configure` additionally requires resolved
required settings, applicable core native configuration, matching native target,
build proof, native smoke command evidence and the five check areas; it still cannot claim store/testing
readback or an exported artifact. Later phases reuse those configuration gates
and add their candidate/export/provider checks. Keep `track` as `none` for
`discover` and `configure`.

## Output and milestone checks

The envelope is `schema_version`, `project_id`, `skill`, `input_sha256`, `status`,
`summary`, `constraints`, `evidence`, `blockers`, `result`. The canonical input
SHA-256 is UTF-8 sorted-key compact JSON, preserving Unicode. Compute it with
`hash-input`; never paste a digest from another project. Both public example
`input_sha256` values are generated from their included synthetic intake JSON by
`make resources`; `make check` rejects stale generated values. File/artifact
references instead hash actual bytes, as do installer ownership receipts.
A digest identifies content and is not a credential. Example files contain no
real candidate, private app identity or provider receipt. `ready` has no
blockers; `blocked` has actionable `{reason, next_action}` entries and never means
release completion. Preserve intake/definition constraints. Evidence entries are
`{id, kind, reference}`, where kind is command, artifact or observation. Use `record`
for command proofs; see the bundled workflow's help and the platform guide.

For `configure` and release phases, result includes a passing
`build_check`, five checked areas (`tests`, `signing`, `compliance`, `recovery`,
`tracking`) with evidence. Release phases also bind the actual candidate/export. Result has nullable `store_readback`, `testing_readback`,
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
