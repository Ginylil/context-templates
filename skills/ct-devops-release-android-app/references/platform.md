# Google Play release workflow

Official sources checked on 2026-10-15. Recheck current policy, tooling and
account-specific Console state when executing. Examples must remain synthetic;
no developer account or signing setup belongs in the public package.

## Candidate and preflight

- Discover the actual repository build/submit lane rather than assuming hosted
  framework services. Bind source revision, working-tree digest, application ID,
  version name/code, release profile, artifact SHA-256 and signing result.
- Produce and inspect the release-signed Android App Bundle for a normal modern
  Play release. Existing legacy applications may have supported APK lanes;
  inspect their actual rules instead of claiming all APK uploads are impossible.
- The upload key signs the bundle; Play App Signing signs generated delivery
  APKs. A debug/placeholder signer is a blocker. Verify credentials and runner
  access separately from signing; do not export keys for diagnosis.
  [App signing](https://developer.android.com/studio/publish/app-signing)
- Keep version codes aligned with repository truth and inspect existing uploaded
  artifacts before allocating one. Higher compatible codes affect which build
  a tester receives; a reused upload code is not repaired by repeated submission.
  [Versioning](https://developer.android.com/studio/publish/versioning)
- Check app record, account role, listing/content/privacy requirements, countries,
  pricing, policy/review blockers and exact target track. Internal testing can
  start before all app setup is complete; do not require production polish for
  a narrowly requested internal test.

## Testing tracks and tester access

- Internal: up to 100 testers; inspect the exact released bundle, intended lists
  and tester link. Temporary listing information can coexist with a usable test.
- Closed: configure the intended email list or Google Group and exact track.
  Verify membership and active opt-in; a group member must still opt into testing.
- Open: publicly visible test; confirm listing readiness, eligibility and explicit
  authority for that audience before rollout.
- Internal/closed tests before public tracks need a shared store/opt-in URL rather
  than assumptions about search discovery. Publication/propagation can take time.
- Internal testers must opt out before receiving closed/open tracks. Eligible
  users generally receive the highest compatible version code across available
  tracks; inspect shadowing and eligibility before diagnosing a stale device.
- Internal app sharing is a separate distribution surface. Upload, track state,
  configured access, opt-in and installed version each require their own proof.
  [Configure testing](https://support.google.com/googleplay/android-developer/answer/9845334?hl=en)

## Conditional production-access requirement

For personal developer accounts created after November 13, 2023, current rules
require at least 12 closed-test testers opted in continuously for 14 days before
applying for production access. Internal testing does not fulfill that gate.
The application includes testing/readiness questions; reaching a count does not
guarantee approval. For these accounts, open testing becomes available after
production access. Verify account type, actual Console eligibility and current
requirements instead of hard-coding this policy for every account or inferring
completion from elapsed wall time. Use real participant and feedback evidence;
do not fabricate testers, engagement or application answers.
[New personal account requirements](https://support.google.com/googleplay/android-developer/answer/14151465?hl=en)

## Review, publishing and production

- Inspect exact track identifier, release notes, selected version codes,
  countries, audience, review state, managed publishing and rollout fraction.
  Saving a draft or uploading a bundle does not publish it to a track.
- Before wider distribution, complete the applicable store listing, App content,
  Data safety, app-access/review instructions and policy requirements. Keep any
  review-access credentials in a private supported provider surface.
- Reconcile Publishing overview after saves. Changes can wait for review or
  approval and then await publication; do not call a queued update live.
- Before production, match testing readback and human acceptance to the exact
  candidate, confirm production authorization, and inspect rollout behavior.
  A first production release may publish to all selected users/countries;
  do not assume an update-style percentage rollout is available.
  [Prepare and roll out a release](https://support.google.com/googleplay/android-developer/answer/9859348?hl=en)
- Read track and publishing state after each authorized action, then verify
  requested availability. The API exposes track/version codes and states such
  as `draft`, `inProgress`, `halted` and `completed`; an edit/request response
  alone does not prove users can obtain that candidate.
  [Tracks API](https://developers.google.com/android-publisher/api-ref/rest/v3/edits.tracks)
- Define recovery from the actual rollout surface. Halting a rollout limits
  further delivery; it does not remove or downgrade existing installations.
  Diagnose tester eligibility, opt-in, competing codes and propagation before
  another build. Preserve failed-attempt evidence and state remaining limits.

## Credentials and evidence

Only logical credential references belong in intake; never embed service-account
JSON, keystores, signing private keys, passwords, tokens, cookies, recovery codes,
or private tester/account exports. Keep runtime artifacts and sanitized provider
readbacks outside this public catalog. Screenshots and build logs can expose
sensitive data; inspect capture settings and retain private evidence privately.
No local validator can establish a provider's approval, human acceptance,
real-device behavior or public availability without corresponding evidence.
