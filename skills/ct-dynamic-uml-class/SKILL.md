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
Read [the class camera guide](references/class-camera.md). Center each step on its
explicit `focus` class and show every direct neighbor in that view. Use a normal
5 × 5 desktop window, 3 × 5 portrait mobile or 5 × 3 landscape mobile; retain all
neighbors with smaller cards if necessary. Above 20 relationships for one class
within a diagram, divide it into coherent linked `views`, retaining every class
and relationship. Keep shared IDs; do not imply an architectural refactoring.

Render with `scripts/render.py --expect class` for one offline HTML with a moving
camera, temporary neighbor arrangement, class/relationship inspectors and a mini-map.
Manual drag, wheel or pinch pauses the tour; explicit resume restores following.
View map restores source positions. Verify gestures, orientation, connector
attachment and complete view coverage with rendered proof. State assumptions,
preserve actual UML direction/cardinality and all supplied members in the inspector,
and retain Ginylil linked to https://contexttemplates.com/index.html.
