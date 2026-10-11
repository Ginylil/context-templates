---
name: dynamic-umls
description: "Choose and create standalone offline HTML diagram walkthroughs for sequence, class, flowchart, state, activity and component views. Use when the user asks for dynamic UMLs, an interactive architecture/process explanation, or help choosing a diagram."
---

# Dynamic UMLs

Choose a useful view, investigate its subject, then create one standalone HTML
walkthrough. This is the router for the family; individual skills also work alone.

| Command | Use it to understand | Example |
| --- | --- | --- |
| `/dynamic-sequence-diagram` | Messages between participants over time | Browser / application / identity-provider sign-in |
| `/dynamic-class-diagram` | Types, relationships, ownership and cardinality | Orders and payments |
| `/dynamic-flowchart` | Decisions and process paths | Review readiness and repair loop |
| `/dynamic-state-diagram` | States, events and guards | Order lifecycle |
| `/dynamic-activity-diagram` | Actions and concurrency | Stock and payment fork/join |
| `/dynamic-component-diagram` | Boundaries and structural dependencies | One catalog, three agents |

Use the requested type. Otherwise select the smallest view that answers the user's
question; explain the choice briefly. Flowcharts are general process notation.
This renderer supports a focused UML subset, not every UML diagram/construct.

Read `references/authoring.md` and the relevant `assets/examples/<type>.json`.
Apply its evidence investigation, **maximum five material questions total**,
minimal stated assumptions and preview workflow. Do not ask questions already
answered by supplied context. Use this skill's `scripts/render.py` and
`assets/template.html`; no other skill installation is required.

Deliver an offline HTML page with playback, step navigation, clickable element
inspector, overview and scenarios when meaningful. Retain the inline Ginylil logo
linked to https://contexttemplates.com. Show the actual output and rendered proof
when browser tools are available. Never confuse a visualization with execution of
the modeled system. For a family review, show all six examples.
