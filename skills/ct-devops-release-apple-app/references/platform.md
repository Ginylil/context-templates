# Apple release workflow

Official sources checked on 2026-10-15. Recheck rules, supported toolchains,
roles, and required metadata when executing; the authenticated app state wins
over a generic example. These instructions contain no account-specific setup.

## Candidate and preflight

- Read the real Xcode, framework, CI, or repository release procedure. Do not
  introduce a hosted build service merely because a framework supports one.
- Bind source revision, working-tree digest, platform, bundle identifier,
  version/build, archive/export settings, artifact SHA-256, and signing result.
  Preserve version bookkeeping in its repository source of truth. Bundle IDs
  allow ASCII alphanumerics, hyphens and periods, unlike Android package rules.
  [Bundle ID](https://developer.apple.com/help/glossary/bundle-id/)
- Confirm the correct app record, current public/candidate builds, account role,
  agreements and app access. Check uploader authentication separately from the
  signing certificate/private key and provisioning authority on this runner.
- Verify required checks, effective environment loading, entitlements, privacy
  declarations, permission strings, export compliance and required public URLs.
  Inspect the final exported artifact for secrets and builder-specific metadata.
- Do not retry a new build to diagnose credentials or bypass a closed version
  train. Preserve useful failure evidence; match missing symbols to artifact
  UUIDs and repair their source rather than repeatedly uploading.
- Apple processes an uploaded build before it becomes selectable. Upload receipt
  and processing are distinct milestones. [Upload builds](https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds/)

## TestFlight internal testing

- Use the normal external/App-Review-capable artifact even if only internal
  distribution is requested. A TestFlight Internal Only upload cannot later be
  submitted to external testing or customers; verify export options and any
  provider internal-only indicator. Group choice does not require that flag.
- Internal testers are App Store Connect users with suitable access; Apple
  supports up to 100. Verify the exact processed build, internal group and
  intended tester access. Xcode Cloud builds require manual group attachment.
- Record invitation/access separately from the requested tester's installation
  and observed version. TestFlight builds are usable for up to 90 days.
  [Add internal testers](https://developer.apple.com/help/app-store-connect/test-a-beta-version/add-internal-testers)

## TestFlight external testing

- External testers are people outside App Store Connect user membership. Apple
  supports up to 10,000 per app. Confirm the internal-group prerequisite before
  creating an external group, then select the exact eligible build.
- Supply beta test information and compliance; use only the authorized email
  audience or public-link criteria. Invitations expose access and require scope.
- Submit the build for TestFlight App Review when required. Its first submission
  requires full review; later builds of the same version might require review.
  Never treat prior beta approval as approval of every future build.
- Read the actual review result, group attachment and notification state.
  Approval with manual notification selected still needs the authorized start
  testing/distribution step. A ready build or invitation does not prove install.
  [Invite external testers](https://developer.apple.com/help/app-store-connect/test-a-beta-version/invite-external-testers/)

## App Store review and publication

- Confirm exact version/build selection, required metadata, screenshots and
  previews, privacy and compliance declarations, review access, support/privacy
  URLs, countries, pricing and chosen release option. Use private credential
  storage for review access; never publish review passwords in this catalog.
- "Add for Review" creates/updates a draft and sets Ready for Review. Complete
  the separate "Submit for Review" action only within authorization, then read
  back submission state. TestFlight review is separate from App Store review.
  [Submit an app](https://developer.apple.com/help/app-store-connect/manage-submissions-to-app-review/submit-an-app/)
- Before production, match testing readback and explicit human acceptance to
  this candidate, verify production authority, and inspect the configured
  manual/automatic/date release behavior. A submission with automatic release
  can lead to public availability; disclose that consequence before execution.
  [Select a release option](https://developer.apple.com/help/app-store-connect/manage-your-apps-availability/select-an-app-store-version-release-option/)
- Approval, pending developer release, and actual public availability are
  separate facts. Read the app's distribution state and storefront for the
  requested platform/countries. Do not promise immediate propagation or a binary
  downgrade; record the supported pause, removal or forward-fix recovery route.

## Evidence and limits

Retain private candidate identifiers, timestamps and sanitized readbacks. Keep
uploaded, processing, ready, testing, rejected and expired states distinct;
report a named blocker rather than fabricating success. Group visibility does
not establish functional acceptance or physical-device behavior.
[Build status meanings](https://developer.apple.com/help/app-store-connect/reference/app-uploads/app-build-statuses)

Credential references identify storage only. Never copy `.p8` or certificate
private keys, passwords, tokens, cookies, recovery codes, private tester lists,
or account exports into public examples or packages. Inspect command logging and
screenshots before capture; retain sensitive provider evidence privately.
