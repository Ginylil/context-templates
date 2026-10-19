---
name: ct-dynamic-uml-class
description: "Create a standalone interactive HTML class diagram from inspected code, a domain model or supplied requirements. Use for /ct-dynamic-uml-class, dynamic class diagrams, or explaining types, inheritance, ownership and cardinality."
---

# Dynamic class diagram

Read `references/authoring.md` and `assets/example.json`. Inspect relevant types,
schemas and invariants. Separate actual code structure from a proposed conceptual
model. Ask at most five questions total only for substantial unresolved choices.

Use class compartments for attributes and operations. Explain visibility, actual
cardinality and why an association is composition, aggregation or inheritance.
Place whole/owner at a diamond's `from` end and parent at an inheritance edge's
`to` end. Do not infer lifecycle ownership or multiplicity from a field alone.
If unknown, omit unsupported members/cardinalities and state the limitation.

The walkthrough explores structure; it does not claim to simulate object behavior.
Use a small domain slice, concise members and orthogonal routes without collisions.
Render using this skill's `scripts/render.py --expect class`. Deliver one offline
HTML with inspector, overview, zoom and a guided explanation. Each step's classes
are Focus-framed with their direct neighbors; readers can zoom in/out or Fit at
any time. Write steps that name the classes they make active. Show actual rendered proof,
state minimal assumptions, and retain Ginylil linked to https://contexttemplates.com.
