# Dynamic UMLs design contract

These are portable artifact templates. A generated page is one HTML file; the
example gallery works locally and through the repository's existing GitHub Pages
hosting. No separate website application is built. The user's supplied
sequence page informed the dark canvas, warm accent and light explanatory notes.
The renderer is repo-owned. The Ginylil coffee-and-sun logo is the PNG supplied
by the owner, stored at `assets/ginylil.png` in the canonical skill and embedded
unchanged as a data URL. Its transparent background remains visible; use a quiet
40px mark (32px on narrow screens), 80% opacity and no bright backing tile.

## Visual and interaction rules

- Keep the system itself dominant: a dark green/charcoal diagram canvas and a
  full-width canvas by default. Keep step details and the element inspector in
  a paper-colored modal opened by the info icon or an element selection. Offer
  an explicit Sidebar toggle for persistent details; it consumes diagram width.
- Use copper `#efa86d` for the current step and mint `#a5cdb3` for structure and
  branding. Background `#191b19`, canvas `#202420`, paper `#f2eee5`.
- Titles use system Georgia/serif; UI uses system sans; labels/code use system
  monospace. No font download, CDN, icon library, telemetry or network dependency.
- Use the supplied Ginylil coffee-and-sun logo, linked to
  `https://contexttemplates.com` in both masthead and footer. The footer uses a
  32px transparent mark at the same 80% opacity beside the visible destination.
- Scenario menus belong to the page theme and open below their trigger on desktop
  and mobile. Support keyboard selection, typeahead, Escape/Tab dismissal and
  outside click; preserve focus and distinguish selection from keyboard focus.
- Flowcharts read downward, with at most seven nodes per view. This is a project
  readability limit, not a notation standard. Use double-bar subprocess nodes
  linking to smaller embedded flows. Back restores parent context; changing
  views pauses playback. Use orthogonal explicit ports and separate routes.
  Returns use outer side rails and enter side ports. Reject connector crossings,
  overlaps, routes through nodes, insufficient node spacing and invalid child links.
  State diagrams share this policy, allow horizontal or vertical forward paths,
  and offer expandable state detail views. Their return rails run outside the
  node area along the chosen axis. Transition causes sit directly on a chosen
  straight arrow segment, with a canvas-colored backing and space for arrowheads;
  reject floating state labels. Keep state text at its logical size on mobile
  rather than shrinking the entire diagram. State diagrams fit the available
  width while event text stays at least 10px; otherwise allow horizontal panning.
  Follow the active destination when a transition spans more than one viewport.
  The Python verifier uses conservative
  bounding boxes and label estimates; browser inspection checks actual text.
  See the authoring guide for the numeric geometry policy.
- Play is opt-in. Previous/next, reset, speed, overview, scenario selection and
  direct step navigation share one model. Stop at the end and when the page is
  hidden. Opening details saves the playing/paused state and remaining step
  duration, then pauses. Closing (button or Escape) resumes only a previously
  playing walkthrough from the same step. Reading a modal in another tab must
  not erase the saved intent; timers never run in a hidden page.
  Structural diagram playback explains relationships, not runtime events.
- Make nodes and relationships keyboard-selectable with meaningful labels and
  a text inspector. Announce step changes. Keep keyboard focus on direct step
  buttons when their active state changes. Ignore global shortcuts in controls.
- Honor reduced motion and avoid animated layout/scrolling. On mobile, keep the
  page within the viewport width. The document owns vertical scrolling for all
  six types; diagram canvases expand to their content height and only pan
  horizontally when needed. Do not add a height-limited inner vertical scrollport.
  Follow active messages through document scrolling, accounting for sticky
  controls and participant headers. Keep the sequence header strip outside the
  horizontal overflow container, sticky below playback controls; synchronize its
  horizontal position and width with the lifelines. In sequence walkthroughs, fit
  as many participants as readable boxes and omission markers allow. Always keep
  active message endpoints; prioritize participants from the previous and next
  chronological messages (often four in total), then fill remaining room with
  nearby participants. Show every participant if they fit; collapse only overflow
  groups into selectable `…` in source order. Recalculate on step changes, window
  resize and sidebar toggles. Hide arrows with omitted endpoints. Preserve
  message numbers and chronological
  vertical positions. Keep text at least 10px and the entire active arrow visible
  without horizontal scrolling. Overview restores all participants and messages
  at their original positions; show a pan hint if the full view overflows. Auto-follow
  keeps visible previous/next arrows in view when their combined height fits below
  sticky controls; otherwise prioritize the active exchange. Numeric step
  targets become 40px. Layouts use explicit coordinates, concise
  labels and routing bends; never accept clipping/overlap as an automatic layout.
- The educational UML subset must be stated; diamonds, triangles, direction,
  returns and parallel branches must retain their documented meaning.
- Show scope, assumptions, provenance and inspected sources on every page. Treat
  model strings as data, never executable HTML. Branding links work online;
  rendering and controls work with no network.

## Canonical sources and generated copies

`skills/dynamic-umls/` owns `assets/template.html`, `assets/ginylil.png`,
`scripts/render.py`, `scripts/validate_flowchart.py`, `scripts/validate_state.py`,
`references/authoring.md`, `assets/examples/<type>.json` and the additional
`assets/examples/sequence-long.json`. The six focused skills
have generated copies of the shared resources plus their own `assets/example.json`
so every downloadable skill works alone. Edit shared resources at the router,
then run `python scripts/dynamic_umls.py`. Do not hand-edit generated copies or
`examples/dynamic-umls/*.html`. The check mode detects drift; all generated bytes
are deterministic. Type-specific SKILL.md and agent metadata remain authored.

## Proof path

Run `make check` and `make build`. Optional `node scripts/check_dynamic_umls.cjs`
uses an already available Playwright package/browser (no auto-install). Override
module resolution with `DYNAMIC_UMLS_PLAYWRIGHT` and browser executable with
`DYNAMIC_UMLS_CHROME` if needed. Screenshots go to ignored
`dist/dynamic-umls-proof/` or `DYNAMIC_UMLS_PROOF`.

The browser check loads all seven examples through `file://` offline, tests navigation,
scenarios, inspector, keyboard focus, playback to end, restart, reduced motion,
mobile page overflow and node text bounds, modal pause/resume and optional
sidebar width, and captures desktop/mobile proof. Sequence density checks require
readable active/neighboring endpoints, use of available space, source order and
accurate omission groups; filler participant identities may vary with actual
canvas width and scrollbar gutter. Regression proof at 1440×760
checks actual active-message viewport bounds (including during playback),
document movement, the absence of inner vertical canvas overflow for all six
types, and sequence header/lifeline alignment during horizontal panning. A changed
scroll offset alone is insufficient. Dialog semantics follow the native
[HTML dialog element](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog),
with a named title, close control, keyboard dismissal and focus restoration.
Participant strips follow the native
[CSS sticky positioning rules](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/position);
an overflowing ancestor would make them stick to that container instead of the page.
The scenario menu keyboard/below-trigger checks and subprocess drill-down/return
checks supplement these regressions. State label checks compare label centers
against the actual SVG connector path and verify readable mobile sizing;
matched state before/after captures use 1440×960. Short-window state checks at
1250×673 verify width fit, the absence of inner vertical scrolling, page auto-follow,
quiet transparent branding and horizontal-only panning on mobile. Matched
before/after captures use 1440×960 for the flowchart; route inspection also uses a narrower, taller viewport.
The long-sequence regression traverses all 32 messages across six participants
at 1271×658, 800×658 and 390×844, checks whole active arrows and participant
headers fit without horizontal overflow, room-filling participant selection,
previous/next messages with four participants, collapse/expansion during resize,
labelled omission groups, pointer/keyboard expansion, canonical Overview
restoration, all 32 mobile sidebar steps,
multi-screen page movement, reset/jump, pause/resume and final-step playback.
It also checks the repeated embedded logo and captures matched footer proof.
Human inspection still checks routing and visual hierarchy. The initial reference
was rendered separately before implementation; only sequence shares that reference
subject. Other types have no prior shipped visual baseline. This repository has no
staging environment. Browser proof and isolated installation are not actual agent
invocation or acceptance of the template design.
