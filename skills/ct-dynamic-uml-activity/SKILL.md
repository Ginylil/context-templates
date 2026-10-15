---
name: ct-dynamic-uml-activity
description: "Create a standalone interactive HTML UML activity diagram for a workflow with actions, branches or concurrent work. Use for /ct-dynamic-uml-activity and dynamic activity walkthroughs, especially fork/join explanations."
---

# Dynamic activity diagram

Read `references/authoring.md` and `assets/example.json`. Inspect action ordering,
branch guards and concurrency evidence. Ask at most five questions total only for
material unknowns, such as whether work is parallel or which results a join requires.

Model actions, control flows, initial/final nodes, decision diamonds and fork/join
bars. A fork starts concurrent branches; a join synchronizes its required inputs.
Highlight concurrent work together and explain that playback does not impose
serial scheduling. Do not substitute a decision for a fork or invent compensation.
State exceptions omitted from the model. This subset does not draw swimlanes or
object flows; explain unsupported notation rather than mislabeling shapes.

Use this skill's `scripts/render.py --expect activity` for one offline HTML file.
Verify parallel highlighting, directions, routes and inspector. Show rendered
proof, keep minimal assumptions visible, and retain Ginylil linked to
https://contexttemplates.com.
