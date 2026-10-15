# Discover and configure an Android release lane

Use `discover` for read-only inventory and an actionable setup plan; use
`configure` for requested repository changes and non-destructive local checks.
Account creation, agreements, purchases, signing resets, tester invitations and
upload/review/publication retain their separate authority. All questions reuse
the scope's 10-question/2-batch ledger. Fill the checked contract from evidence;
do not ask the user to complete JSON.

## Discover before selecting a route

Read repository instructions, package manifest/lockfile, Gradle wrapper/config,
build scripts and release CI. Locate existing Android modules/flavors, manifests,
Capacitor config, Expo config and React Native integrations. Determine which
file or service owns application ID, version code/name, endpoints, public build
variables, SDK targets, permissions and signing. Inspect loaders and variable
names without displaying secret files. `.env` is useful only if actually loaded.
Run the discovery CLI in [the contract](contract.md) first, with output outside
the checkout. It refuses recognizable tracked/unignored private environment and
signing files before hashing source. Fix storage/ignore rules without opening or
printing values; public `.env.example`/`.env.template` files contain placeholders.
Bind that report into intake, then populate the checked inventory/setup plan.

Use `setup_mode=existing-native` when a usable native lane exists; preserve it.
Choose `wrap-web` only for the agreed web-to-native scope. Record requested
capabilities and actual public build prefixes. Do not introduce Expo, Capacitor
or a native rewrite merely because it is familiar. Reuse a proven existing
wrapper; keep framework migration, backend work and new platforms separately
scoped. Preserve handwritten native code and current web delivery.

Capacitor is one option for an existing client web build: it needs built assets
with a root `index.html`. Set `webDir` to actual output, build that output and
sync the selected Android target with pinned repository tooling.
[Capacitor integration](https://capacitorjs.com/docs/getting-started)

An SSR server, API route or private server variable is not a distributable web
asset. Establish a supported static/client build and separately deployed backend,
or identify the missing architecture. Do not use a development server URL as
the production wrapper. Capacitor documents `server.url` and cleartext settings
as development/live-reload features; a local WebView origin is separate from
the backend endpoint. [Capacitor configuration](https://capacitorjs.com/docs/config)

## What to configure, where, and how to verify

Replace the locations below with inspected repository paths, modules/flavors,
profile names and dashboard sections; do not invent a standard directory.

| Existing route or surface | Settings and location | Verification |
| --- | --- | --- |
| Native Gradle | Actual app module `build.gradle(.kts)`, shared properties/convention plugins: application ID, version, SDK levels, flavors and signing references | Resolve the requested release variant; inspect bundle identity and signer, not only a successful debug APK |
| Manifest/resources | Owning `AndroidManifest.xml`, merged flavor manifest, `res/` icons/themes/splash and network security config | Inspect merged release manifest/resources; exercise permission denial, exported components, links and network behavior |
| Capacitor | `capacitor.config.*`: app ID and real `webDir`; generated Android project: Gradle, manifest, resources | Build web output, sync selected platform, inspect copied assets and resolved release variant, then launch the shell |
| Expo | `app.json`/`app.config.*`: Android package/version code, icons, schemes, intent filters, permissions/plugins; `eas.json` only if it owns the existing build profile | Inspect resolved config privately and actual generated/compiled values; do not regenerate handwritten native directories without checking ownership |
| React Native | Native `android/` module and installed environment/config integration, Metro/Babel/build scripts | Trace the actual environment loader and variant; plain React Native does not automatically load arbitrary `.env` files |
| Backend/auth | Existing API hosting, CORS/cookie policy, native OAuth registration and hosted app-link association | Exercise HTTPS API and auth/redirect/logout from native runtime; confirm release signing identity where the provider requires it |
| CI/build runner | Existing workflow, Java/SDK/Gradle selection, profile/env loading, secure upload-key injection and uploader references | Resolve the same variant and inspect artifact signer/identity; non-mutating authenticated read verifies provider access separately |
| Play Console | App record/package, account roles/access, App integrity signing certificates, testing tracks/testers, app content/privacy/listing and countries | Read back the exact app and relevant state; account owner handles agreements, billing, ownership and restricted signing-reset actions |

See [Capacitor Android configuration](https://capacitorjs.com/docs/android/configuration).
Expo's [app config guide](https://docs.expo.dev/workflow/configuration/) and
[environment guide](https://docs.expo.dev/guides/environment-variables/) explain
resolved public configuration and supported loading; match installed versions.
Do not dump the full resolved config into public output.

## Safe storage and public build exposure

Track `.env.example` with names and explicit placeholders only, such as
`<public-api-url>` or `<set-in-secret-store>`. Create ignored local files only
when the actual selected loader consumes them; verify the ignore rule without
displaying values. Document each variable's precise name, consumer, environment,
precedence and verification. Do not assume shell exports win over build files.

`EXPO_PUBLIC_*`, web bundler public prefixes, Expo runtime `extra`, JavaScript
bundles, Android `BuildConfig`, manifest metadata and resources are exposed to
app recipients. CI secret injection does not change that. Server tokens stay
server-side. Keystores, private signing keys, keystore passwords, OAuth/service
account secrets and upload credentials belong in approved secure stores and
restricted signing/upload processes. Public certificate fingerprints and native
client identifiers are configuration, not substitutes for private signing keys.
Report logical credential references and access state; never ask for values.

## Native smoke before bundle/upload

Use reachable HTTPS APIs; on a physical device, `localhost` identifies the device,
not the developer's computer. Apply development addressing only to development
profiles. Verify WebView origin, CORS, cookies, login/refresh/logout and secure
auth callbacks on the native runtime. Configure intent filters/app links and
corresponding hosted association files for the actual app/signing identity.

Add only requested capabilities through supported native/plugin integrations.
Match runtime permission requests, denial/recovery, manifest declarations,
privacy disclosures and Data safety to actual behavior. Configure app icons,
splash, display name, system back, keyboard/insets, external links, file/share
flows and safe offline/error behavior. Review purchase/account flows under the
applicable current policies instead of inheriting web-only assumptions.

Launch and smoke-test the chosen emulator/native development variant before
release upload: startup, authentication, primary action, deep links, permission
denial, network loss/recovery and navigation. Then inspect the release bundle's
effective configuration, identity and signer. Separate emulator/device proof,
release signing, authenticated Play access and actual tester availability.

Google forbids unauthorized website WebViews and affiliate spam; it does not
declare every owned-site WebView acceptable. Confirm ownership/permission and
real utility, quality and policy readiness. Packaging success cannot predict
review. [WebViews and spam policy](https://support.google.com/googleplay/android-developer/answer/9899034?hl=en)

## Actionable setup handoff

For every missing setting provide exact location, required action, responsible
operator, storage/exposure classification, verification procedure, current
status and blocker/next action. Example: “In Play Console's App integrity page,
compare the registered upload certificate fingerprint to the locally inspected
release signer. Status: blocked on authorized account access; do not reset the
key or upload another bundle as a probe.” Avoid vague “set up signing” advice.

Automate reversible repository configuration already in scope. Leave account,
agreement, billing and missing role decisions with the authorized operator.
Discovery can finish with a complete plan while settings remain unresolved;
configuration requires the applicable configuration and native checks. Neither
validates Play eligibility/approval or authorizes subsequent external actions.
