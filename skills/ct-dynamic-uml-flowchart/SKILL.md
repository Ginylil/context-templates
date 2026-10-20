---
name: ct-dynamic-uml-flowchart
description: "Create a standalone interactive HTML flowchart for a process, decision tree, troubleshooting path or workflow. Use for /ct-dynamic-uml-flowchart and requests for dynamic flowcharts with step playback and branch exploration."
---

# Dynamic flowchart

Read `references/authoring.md` and `assets/example.json`. Inspect the process and
its decision evidence first. Ask at most five questions total only when unknowns
materially change the path, boundaries or outcomes.

Use a vertical main path with processes, decision diamonds and start/end terminals.
Keep at most seven nodes in each view; compose larger flows with clickable
`subprocess` nodes and embedded child `subflows`. Give every edge explicit ports
and an orthogonal route. Retry arrows go around an outer side rail and enter
the earlier node from the side; never cross or overlap connectors. Label branch conditions
explicitly, including what causes an exit or retry. Preserve failures and loops
needed to understand the process; do not invent required approvals or validators.
Give distinct scenarios for meaningful alternative branches. Each scenario must
follow modeled edges, not redefine them. Flowcharts are general process diagrams,
not a formal UML diagram type; say so without distracting from the user's goal.

Run `scripts/validate_flowchart.py` on the model to verify every nested view's
node limit, spacing, routing and references. Rendering enforces these rules too.

Render with this skill's `scripts/render.py --expect flowchart`. Deliver one
standalone offline HTML with stepping, playback and an element inspector. Verify
branch switching and layout, show rendered proof, and retain the Ginylil logo
linked to https://contexttemplates.com/index.html. List minimal assumptions in the page.
