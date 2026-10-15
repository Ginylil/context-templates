---
name: ct-devops-release-android-app
description: "Discover configuration, set up or wrap an existing web app, and release Android apps through signed bundles, Play internal, closed and open testing, and production rollout with exact candidate evidence and scoped authorization."
---

# Release an Android app

Advance the actual Play lane through `discover` or `configure`, then `prepare`, `upload`, `play-internal`, `play-closed`,
`play-open`, or `production`. Existing apps do not need a new product definition.
Read repository instructions and [the platform guide](references/platform.md).

For missing setup or a web app that needs a native shell, use the
[configuration and wrapping guide](references/setup.md). Discover the actual
stack and loader first; preserve existing native/framework choices. Return
exact missing settings with location, action, owner, safe storage, verification
and status. Configure only the selected authorized route; `discover` is read-only.
Neither discovered settings nor a successful configuration check authorizes an
upload or proves native behavior, Play access, or store acceptance.

## Establish the candidate and authority

Inspect source revision/worktree, application ID, version name/code, release profile,
signed artifact, current track and intended audience. Prefer repository-owned commands.
Verify the existing GitHub Issue, Project membership and dependencies before execution;
prepare missing tracking and obtain any missing external-write authority.
Do not silently create duplicate app records, tracks or tester lists.

Uploader authentication, upload-key signing, Play App Signing and runner access are
separate. Intake accepts only `credential_refs` with provider (`env`, `keychain`,
or `secret-manager`) and logical name. Never put service-account JSON, keystores,
passwords, tokens or tester lists in chat, reports, examples or public files.
Keep runtime evidence private outside this catalog; inspect output before capture.

## Execute the requested milestone

Run checks, inspect the release-signed bundle, and bind its digest to source, app ID
and version code. Debug signing or an emulator APK does not prove Play readiness.
Reconcile uploaded bundles and releases before retrying; do not blindly reuse
rejected codes, promote a different candidate or rebuild for a stale device.

Uploads, tester changes, review, track changes and production each need authority
for their action and target. Reuse existing authorization. Internal testing does
not authorize closed/open testing or public release. Confirm actual Console
eligibility; new-personal-account rules do not apply to every developer.
Open testing exposes the app publicly and requires explicit scope.

Read back track, version code, review/publishing status, countries, audience and
rollout fraction after each action. Separate uploaded, draft, submitted, approved,
distributed, tester-eligible, opted-in and installed states. Internal app sharing
is separate from internal testing. Stop at the requested milestone.

Production requires candidate-bound testing readback, human acceptance of that
candidate, and production authority. Honor repository staging rules; if no
staging exists, say so and use the actual Play testing qualification route.
Inspect managed publishing and first-release versus update rollout behavior.
Approval alone does not prove availability. Record a supported recovery route
and limits; halting rollout does not undo existing installations.

## Validate and hand off

Read [the input/output contract](references/contract.md). From the installed skill
run `python3 scripts/workflow.py validate-input input.json`,
then `validate-output input.json output.json`; use `py -3` on Windows.
Render with `render input.json output.json --output report.md`. Capture explicit safe
commands with `record --cwd <repository> --output <private-proof> --timeout 60
-- <command> <arguments>` only within authority; never record credential-printing
commands. Validators check structure and evidence bindings, not approval
authenticity or live availability. Deliver exact milestone/candidate, mutations,
evidence, limitations and next action; valid blocked output is not a release.

Reuse the scope ledger: **10 total questions across at most 2 batches**, including
resumed work. Inspect evidence first, record independent questions before asking,
and never reset the budget or hide subquestions. Create a ledger with bundled
`scripts/definition.py` only if questions are needed and none exists. At the cap,
use reversible assumptions or report a blocker. Silence is never permission.
Preserve original private skills and unrelated work.
