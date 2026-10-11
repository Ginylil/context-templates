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
Use at most seven nodes per view, including initial/final symbols. Horizontal
left-to-right and vertical top-to-bottom layouts are supported. Use orthogonal
explicit ports, separate connectors with no crossings or overlaps, and outer
return rails. Place each cause label **on its arrow** with `labelOn`; never use
floating `labelAt` coordinates. Give the label a straight segment long enough
for its text and preserve arrowheads. Run `scripts/validate_state.py` on JSON or
emitted HTML; rendering also enforces these rules.

Use a state's `subflow` reference and embedded `subflows` to expose a smaller
state detail view when needed. Back restores the parent context and playback
stays paused. These are explanatory drill-down views, not a simulation of
hierarchical state execution, entry/exit actions or history pseudostates.

Render with this skill's `scripts/render.py --expect state`. Produce one offline
HTML page with playback, transition inspector and scenario choices where useful.
Check guards, directions and alternate paths, show a real rendered preview and
keep Ginylil branding linked to https://contexttemplates.com. State minimal assumptions.
