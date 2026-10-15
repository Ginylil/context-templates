# Discover and configure an Apple release lane

Use `discover` for a read-only inventory and actionable setup plan; use
`configure` for requested repository changes and non-destructive local checks.
Keep account creation, memberships, agreements, purchases, certificates, tester
invitations and upload/review/publication actions within their separate authority.
All questions reuse the scope's 10-question/2-batch ledger. Fill the checked
contract from evidence; do not ask the user to complete JSON.

## Discover before selecting a route

Read applicable instructions, package manifest/lockfile, build scripts and release
CI. Locate existing Xcode targets/schemes, native directories, Capacitor config,
Expo app config, React Native dependencies, and any generated-project workflow.
Determine which files own bundle ID, version/build, endpoints, public build
variables, permissions and signing. Inspect loader code and variable names
without printing local secret files. A `.env` filename does not prove it is read.
Run the discovery CLI in [the contract](contract.md) first, with output outside
the checkout. It refuses recognizable tracked/unignored private environment and
signing files before hashing source. Fix storage/ignore rules without opening or
printing values; public `.env.example`/`.env.template` files contain placeholders.
Bind that report into intake, then populate the checked inventory/setup plan.

Set `setup_mode` to `existing-native` when a usable native lane already exists;
retain that framework. Select `wrap-web` only for the agreed web-to-native scope.
Record `requested_capabilities` and actual `build_exposure_prefixes`; do not add
camera, notifications, purchases or other capabilities just to appear native.
Framework rewrites, backend deployment and additional platforms are separate
scope decisions. Preserve unrelated web delivery and handwritten native code.

For a web app, inspect its actual production output. Capacitor is one possible
iOS route: it needs compiled web assets with a root `index.html`; configure
`webDir` to the real output, then build and sync the selected platform using the
repository's pinned tooling. Reuse an existing integration before adding one.
[Capacitor integration](https://capacitorjs.com/docs/getting-started)

An SSR process, API route or server secret cannot be copied into the app as a
web asset. Prove a supported static/client build plus separately reachable
backend, or report the missing architectural work. Do not silently replace SSR
with an empty shell. Capacitor's `server.url` is intended for live reload, not a
production shortcut to a hosted site; do not ship development URL, cleartext or
navigation exceptions. Its local WebView origin is distinct from the API base
URL. [Capacitor configuration](https://capacitorjs.com/docs/config)

macOS requires its own discovered native packaging and distribution route;
an iOS Capacitor target is not proof of a Mac App Store app. Do not substitute a
desktop wrapper, Catalyst migration or unsupported plugin without selecting and
validating that route. Record unavailable macOS tooling as a blocker.

## What to configure, where, and how to verify

These are locations to inspect, not paths to invent. Replace each with the
actual repository file, target and dashboard section in the user's setup plan.

| Existing route or surface | Settings and location | Verification |
| --- | --- | --- |
| Native Xcode | Actual project/target Build Settings or referenced `.xcconfig`: bundle ID, version/build, deployment target; Signing & Capabilities: team, entitlements, profiles | Resolve the selected scheme/configuration and inspect the built bundle; simulator success does not prove distribution signing |
| Capacitor iOS | `capacitor.config.*`: app identity and real `webDir`; generated `ios/` target: signing, capabilities, `Info.plist`, assets | Build web output, sync selected target, inspect copied resources and effective Xcode settings, then launch the native shell |
| Expo | `app.json` or `app.config.*`: iOS identity, version, icons, scheme, permissions/config plugins; `eas.json` only if that is the existing profile owner | Inspect resolved config privately, then the generated/compiled target; never regenerate handwritten `ios/` without checking ownership |
| React Native | Existing app config and native `ios/` project; installed environment/config plugin and Xcode build phases | Trace the actual loader, then inspect compiled values and run the app; plain React Native does not automatically read arbitrary `.env` files |
| Backend and identity provider | Existing API hosting config, CORS/cookie policy, OAuth native client/redirect registration, associated-domain hosting | Exercise HTTPS API/auth from the native runtime, including callback, logout and expired session; keep server secrets server-side |
| CI or build runner | Actual workflow and secret references, selected scheme/profile, environment loading and private signing material injection | Non-mutating credential/role check, resolved configuration and signed artifact inspection; CI secret storage does not make bundled values private |
| Apple dashboards | Developer account app identifiers/capabilities/profiles; App Store Connect app identity, role/access, agreements, privacy/compliance, support URLs | Read back the exact app/role and settings; account owner handles agreements, payment and missing ownership permissions |

Capacitor's native location details are documented in
[iOS configuration](https://capacitorjs.com/docs/ios/configuration).
Expo's [app config guide](https://docs.expo.dev/workflow/configuration/) explains
which resolved settings become public; inspect them without echoing sensitive
values. Its [environment guide](https://docs.expo.dev/guides/environment-variables/)
documents supported loading and inlining. Match the installed version.

## Safe configuration storage

Use a tracked `.env.example` only for variable names and explicit placeholders
such as `<public-api-url>` or `<set-in-secret-store>`. Create an ignored local
file only when the selected loader actually consumes it. Verify its ignore rule
without displaying contents. Document the precise variable name, load point,
environment and precedence. Do not rename an existing application's variables
or assume shell exports override Xcode/wrapper files.

`EXPO_PUBLIC_*`, web bundler public prefixes, Expo runtime `extra`, JavaScript
bundles, `Info.plist` and shipped native resources are public configuration.
Never place server tokens, service-account data or signing credentials there,
even when supplied through CI secrets. Keep API/signing private keys in an
approved Keychain or secret manager and inject them only into the signing/upload
process. Report logical credential references and availability, never values.

## Make the wrapper usable before an upload

Configure real HTTPS endpoints and a safe offline/error state. On a physical
device, `localhost` identifies the device, not the developer's backend. Test the
actual WebView origin, CORS, cookies and secure auth/redirect flow; browser-only
login success does not prove native login. Configure URL schemes/universal links
in the owning app config/target and corresponding server domain files.

Implement only requested native capabilities through supported plugins/native
code. Match usage descriptions, entitlements, privacy manifests and runtime
permission denial/recovery to actual behavior. Set real app icons, launch/splash
assets, display name, safe areas, keyboard handling, back/navigation, file/share
flows and external-link behavior. Verify that payment/account behavior follows
the current applicable store rules rather than inheriting website assumptions.

Build and launch in the matching simulator/native development lane before an
archive or upload. Smoke-test startup, login/logout, primary action, deep link,
permission denial, offline/reconnect and layout on the supported device family.
Then inspect the release build's effective configuration and artifact. Separate
simulator, physical-device, archive/signing and authenticated Apple evidence.

Apple reviews utility and app experience, including minimum functionality;
a thin website wrapper is not guaranteed acceptance. Identify the concrete
app-like value and remaining gaps without adding decorative features solely to
evade review. [App Review Guidelines §4.2](https://developer.apple.com/app-store/review/guidelines/#minimum-functionality)

## Return instructions the user can execute

For every missing setting, provide its exact location, required action, owner,
storage/exposure classification, verification procedure, current status and
blocker/next action. Example: “In the discovered Xcode target's Signing &
Capabilities, select an authorized development team; verify the effective team
and a signing preflight. Status: blocked until account access is supplied.”
Do not replace these steps with “configure signing” or request secret values.
Automate reversible repository configuration already in scope; leave account,
agreement, billing and permission decisions with the authorized operator.

Successful `discover` can return a complete plan with unresolved settings;
successful `configure` requires the applicable configuration and native checks.
Neither result proves Apple approval or authorizes later external actions.
