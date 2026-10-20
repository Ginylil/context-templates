---
name: ct-dynamic-uml-component
description: "Create a standalone interactive HTML component diagram from inspected architecture, code or requirements. Use for /ct-dynamic-uml-component and dynamic architecture views explaining component responsibilities and dependencies."
---

# Dynamic component diagram

Read `references/authoring.md` and `assets/example.json`. Inspect actual module,
package and service boundaries and their dependencies. Identify whether this is
current architecture or a proposal. Ask at most five questions total only when
material unknowns cannot be resolved through evidence.

Use component boxes with clear responsibilities. A dashed dependency points from
the dependent component (`from`) to its supplier (`to`); it does not represent
message or data-transfer direction. Do not invent services, ports or deployment
boundaries. This focused subset omits interfaces and ports. Use a sequence view
when the question is about runtime messages instead.

Render with this skill's `scripts/render.py --expect component`. Deliver one
offline HTML with a structural walkthrough, inspector and overview. State source
files, simplifications and unverified boundaries. Verify direction and layout,
show a real rendered preview, and keep the Ginylil logo linked to
https://contexttemplates.com/index.html.
