---
name: ct-devops-release-apple-app
description: "Prepare or execute Apple app releases through signed uploads, TestFlight internal and external testing, App Review, and App Store publication with exact candidate evidence and scoped authorization."
---

# Release an Apple app

Advance the actual Apple release lane to one requested milestone: `prepare`, `upload`,
`testflight-internal`, `testflight-external`, `submit-review`, or `production`.
Existing apps do not need a new product definition to release a known candidate.
Read repository instructions and [platform guide](references/platform.md) before execution.

## Establish the candidate and authority

Inspect source/worktree identity, platform, bundle ID, version/build, archive/export
configuration, signed artifact, and App Store Connect state. Prefer repository-owned
commands. Verify the GitHub Issue, Project membership and dependencies before execution;
prepare missing tracking and obtain any missing write authority.
Do not silently create a tracker or duplicate an app record.

Uploader authentication, signing, browser access, and runner access are separate.
Intake accepts only `credential_refs` with provider (`env`, `keychain`, or
`secret-manager`) and logical name. Never read secret values into chat, reports,
examples, screenshots, or public files.
Keep runtime inputs, artifacts, and proof private outside this public catalog.

## Execute the requested milestone

Run checks, inspect the final exported artifact, and bind its digest to source/build.
Use an external/App-Review-capable upload
even for internal testers: never select TestFlight Internal Only or export with
`testFlightInternalTestingOnly=true`. Confirm eligibility from effective export
configuration and provider evidence rather than a generic beta status.

Uploads, tester/group changes, TestFlight review, App Store review, and production
each need authorization covering that action and target. Reuse existing authority.
An internal testing request does not authorize external review or public release.
Read current state before each action and read it back afterward. An ambiguous
upload or submission is a reason to inspect state, not retry blindly.

Separate local export, upload, processing, exact group/build assignment, tester
access, review submission, approval, public availability, and device installation.
External review requires its actual review state; App Store "Add for Review"
alone is a draft. Stop at the requested milestone. Before production require
candidate-bound testing readback, human acceptance of that candidate, and
production authorization. Honor repository staging rules; say when staging is
absent and use the actual TestFlight qualification route. Approval alone does
not prove storefront availability. Report unsupported recovery or rollback limits.

## Validate and hand off

Read [the input/output contract](references/contract.md). From the installed skill
run `python3 scripts/workflow.py validate-input input.json`,
then `validate-output input.json output.json`; use `py -3` on Windows.
Render with `render input.json output.json --output report.md`.
Capture command evidence using `record --cwd <repository> --output <private-proof>
--timeout 60 -- <command> <arguments>` only after reviewing its action and output
for secrets. Never record commands that print credentials. Validators check
structure and evidence bindings; they do not authenticate approvals or replace
live provider checks. Return actual milestone, exact candidate, evidence,
mutations, blockers and next action; a valid blocked report is not a release.

Reuse the scope's ledger: **10 questions total across at most 2 batches**, including
resumed work. Inspect evidence first, record independent questions before asking,
and never reset an existing budget or hide subquestions. If no ledger exists and
questions are needed, create one with the bundled `scripts/definition.py`.
At the cap use reversible assumptions or a blocker; silence is never permission.
Preserve original private skills and unrelated work.
