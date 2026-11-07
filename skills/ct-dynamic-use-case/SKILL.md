---
name: ct-dynamic-use-case
description: "Create or update an interactive actor-first use-case diagram from an existing project, with subject groups and focused scenario flows. Use for /ct-dynamic-use-case all and requests to add, edit, remove, describe, or refresh use cases."
---

# Dynamic use-case diagram

Investigate the current project and create one offline HTML explorer plus its
editable JSON model. Read `references/authoring.md` and `assets/example.json`.
Use this skill's complete resources; another diagram skill is not required.

`/ct-dynamic-use-case all` means discover all actors and reachable use cases
within the agreed project scope. It does not expand everything at once: begin
with actor figures stacked vertically in the center. Selecting an actor moves
it left and reveals outgoing arrows to oval use cases, grouped by subject.
Selecting a subject narrows that group; selecting a goal reveals its scenario
choices. Keep a small clickable trace and an overview for returning or changing
branches. Each exploration focuses on one actor, goal, or scenario at a time.

## Investigate and describe

Inspect available requirements, routes/screens, authorization rules, services,
tests, and documentation. Screens organize subjects; use cases name actor goals,
not every button or internal function. Record scope, assumptions, evidence status
and supporting source IDs. Separate verified, inferred, proposed and illustrative
behavior. A code inspection does not establish runtime success or exhaustive
coverage. If no project is available, ask for its location; a sample must be
explicitly requested or clearly labeled illustrative. Ask at most five material
questions total, reusing supplied decisions.

Describe each goal's actor trigger, prerequisites, successful outcome and actual
main, alternative, error and recovery scenarios. Do not invent the same generic
errors for every goal. Keep error details inside scenarios. At that level label
the view **Scenario flow** and use ordered action boxes with actor/system owners
and a final outcome. Do not turn steps into included use cases or label every
error `extend`. Actor arrows indicate a trigger, not event order in formal UML.
This renderer deliberately omits UML include/extend/generalization relationships.

## Create or update

For an existing explorer, recover its JSON from the supplied model or embedded
model before changing it. Preserve stable IDs, evidence, scope, unrelated content
and manual edits. Add/update/remove only the requested scope; inspect dependent
actor, subject, scenario and recovery references when removing items. A refresh
reconciles new source evidence without silently deleting an unverified manual
entry. Change the visualization/model, not application behavior, unless separately
requested. Never edit an installed skill to update the user's diagram.

Use the standard-library helper from the installed/assembled skill:

```text
python3 scripts/render_use_case.py validate model.json
python3 scripts/render_use_case.py render model.json --output use-cases.html
python3 scripts/render_use_case.py extract use-cases.html --output recovered.json
```

Python 3.10+ is required (use `py -3` on Windows when appropriate). Output creation
refuses an existing path; use a new revision to preserve user work. Rendering and
extraction do not execute the inspected project, contact services or modify it.

Verify actor selection, subject narrowing, scenario choices, error recovery,
breadcrumbs, overview and narrow-screen layout in the rendered output. Keep
arrows attached during motion, respect reduced motion, and retain the embedded
Ginylil logo and contexttemplates.com link. Show the actual rendered explorer and
return both HTML and the editable model. Report source coverage and any unverified
runtime or browser behavior. Local rendering is not proof that a host discovered
or invoked this skill.
