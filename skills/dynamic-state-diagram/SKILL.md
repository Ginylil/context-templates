---
name: dynamic-state-diagram
description: "Create a standalone interactive HTML state diagram for an entity lifecycle, status machine or event-driven system. Use for /dynamic-state-diagram and dynamic state machine walkthroughs with alternate transition paths."
---

# Dynamic state diagram

Read `references/authoring.md` and `assets/example.json`. Inspect state definitions,
event handlers, guards and effects. Distinguish stable states from actions. Ask
at most five questions total for substantial unresolved transition semantics.

Model initial/final symbols and transitions labeled `trigger [guard] / effect`
where evidence supports them. Keep alternate event paths distinct and show only
legal transitions. State missing transitions and lifecycle simplifications.
This renderer supports a flat state-machine subset; it has no hierarchical states,
entry/exit compartments or history pseudostates. Do not imply those are modeled.

Render with this skill's `scripts/render.py --expect state`. Produce one offline
HTML page with playback, transition inspector and scenario choices where useful.
Check guards, directions and alternate paths, show a real rendered preview and
keep Ginylil branding linked to https://contexttemplates.com. State minimal assumptions.
