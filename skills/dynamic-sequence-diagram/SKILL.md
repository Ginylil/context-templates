---
name: dynamic-sequence-diagram
description: "Create a standalone interactive HTML sequence diagram for a protocol, login flow, API exchange or other participant interaction. Use for dynamic sequence diagram requests, including /dynamic-sequence-diagram for three-way handshake login."
---

# Dynamic sequence diagram

Read `references/authoring.md` and `assets/example.json`, then investigate the
requested interaction before modeling it. For a longer exchange or more
participants, `assets/long-example.json` demonstrates 32 messages across six
participants with readable labels and page auto-follow. Walkthroughs fit active
participants to the canvas, replacing inactive groups with selectable `…`;
Overview restores the complete diagram. Preserve participant order and message
numbers; hide arrows with omitted endpoints. Verify the whole active arrow and
participant boxes fit without horizontal scrolling on desktop and phone.
Ask at most five questions total, only for material unknowns; otherwise proceed
with minimal visible assumptions.

For “three-way handshake login”, distinguish TCP connection establishment from
browser/app/identity-provider sign-in. Ask if context does not resolve the meaning.
Do not label a three-participant flow as a three-message handshake.

Create chronological message edges between participant lifelines. Model actual
request, return and asynchronous-signal semantics: a dashed open arrow is a return,
not a generic “does not wait” message. Include response validation and failure
branches only when supported by evidence; do not invent an authentication design.
State collapsed interactions and the focused UML subset (no activation bars or
combined fragments). A self-call can expose validation within a participant.

Use this skill's `scripts/render.py` with `--expect sequence` and its own template
to produce one offline HTML file. Preserve existing user output. Verify playback,
inspector, navigation and mobile layout, then show a rendered example/preview.
Retain the small transparent Ginylil logo and link to https://contexttemplates.com
in both header and footer.
