# Actor-first use-case explorer

Read this for discovery, model authoring and revisions. The sample model is
synthetic; replace it with investigated project behavior rather than retaining
its sample actors or generic exception scenarios.

## Investigation and scope

Start from the supplied project and existing requirements. Trace roles and
permission guards to routes/screens, actor goals, service outcomes and relevant
tests. Include external actors when they initiate a goal. Timer/system events
must be attributed to their actual source rather than to a human role.

Record what was inspected and what remains unknown. `all` means all discovered
goals in the stated scope, not an unsupported claim of completeness. A model
description or an unexecuted test does not prove deployed behavior. Limit material
questions to five total; preserve existing answers. For partial access, proceed
with clearly marked gaps when useful instead of filling them with invented flows.

## JSON contract (schema_version 1)

Top-level fields:

- `title`, `scope`: nonempty text.
- `assumptions`: a list of explicit assumptions or coverage limits (may be empty).
- `sources`: a list of `{id, label, reference}` records. References are inspected
  repository-relative paths or credential-free HTTP(S) URLs. They are displayed
  as evidence; local paths are plain text and are never fetched by the viewer.
- `actors`: ID-keyed objects with `name` and nonempty `subjects` ID lists.
- `subjects`: ID-keyed objects with `name` and nonempty `cases` ID lists.
- `use_cases`: ID-keyed goal records described below.

IDs use lowercase letters, digits and hyphens, begin with a letter, and are at
most 64 characters. Preserve them across revisions. Every subject and goal must
be reachable from an actor; actors may share subjects and goals.

A goal has `id` equal to its key, `name`, `trigger`, `pre` (prerequisites),
`success` (goal outcome), `parts` (the default ordered scenario steps),
`evidence: {status, source_ids}`, and a nonempty `scenarios` list. Evidence status
is `verified`, `inferred`, `proposed` or `illustrative`; verified behavior needs
supporting source IDs. The renderer checks references, not the truth of evidence.

A scenario has `id`, `name`, `condition`, `result`, `category` (`main`,
`alternative`, `error`, `recovery`), `steps` (an ordered list or null to reuse
the goal's `parts`) and `recovery` (possibly empty). An optional scenario `trigger`
overrides the goal trigger, especially for retry/recovery entry. Each step is a
string attributed to System, or `{label, owner}` where owner is `actor`, `System`
or an actual named participant. Avoid internal jargon when describing user-visible
behavior. Recovery options are `{label, to}` links to a scenario ID in that goal.
Cycles such as retry are allowed; the viewer follows one chosen branch without
recursively expanding them. Do not combine a failed action and its successful
retry into one unconditional success path.

## Diagram versus flow

The actor/subject overview contains human-readable actor figures, goal ovals,
group boundaries and triggering associations. Subject boundaries organize goals;
they are not runtime actions or mandatory execution steps. On selection, the
actor moves left and the next choices appear to its right. Clickable breadcrumbs
retain the actor, subject, goal and selected scenario. Overview restores every
actor and goal, without exposing every error as a new goal.

Scenario choices are rectangular path selectors, labeled by category. A selected
**Scenario flow** shows numbered actor/system actions followed by an outcome.
Rows read left to right and wrap on desktop; narrow screens use a vertical flow.
Error scenarios describe the condition, response, retained state, possible retry
or recovery and final outcome. Optional or exceptional behavior is not automatically
a UML `extend` relationship, and internal steps are not `include` relationships.
The supplied renderer omits those formal relationships; use an appropriate
activity/sequence view when more detailed branching or concurrency is needed.

## Editing and proof

Keep a JSON source beside the generated HTML. If only HTML is supplied, the
`extract` command recovers the embedded model without executing it. Compare the
requested scope and dependent links before removing a goal/scenario. Preserve
unrelated entries and manual edits; mark unresolved contradictions rather than
silently replacing them. Render to a new filename and present the revised output.
The helper refuses existing output and does not write into the modeled project.

Check real actor → subject → goal → scenario interactions and a recovery link.
Verify breadcrumbs and overview retain the appropriate actor; inspect arrows and
text at desktop and phone widths. No network should be needed. The supplied logo
and branding links remain visible, with scope, assumptions and evidence sources.
The public contract keeps the charcoal canvas, copper active state, mint
structure and a small transparent owner-supplied logo. Playback is not part of
this explorer: progression is explicitly selected by the reader.
