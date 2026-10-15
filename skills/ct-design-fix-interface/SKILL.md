---
name: ct-design-fix-interface
description: "Understand and reproduce a reported visual or interaction defect, correct the same confirmed problem across related components and screens, and verify matched before/after renders. Use when an existing interface looks or behaves wrong; ask before changing an uncertain variant."
---

# Fix an interface across the project

Turn “this looks wrong” into a clear correction, apply it wherever the same
problem exists, and show rendered proof. Existing projects enter directly;
a new product definition or redesign is not a prerequisite.

## Understand before editing

Inspect the reported screen, matching route/state/viewport and current revision.
Use supplied screenshots as clues, then reproduce in the actual interface.
State briefly what is observed, what should happen, and the proposed correction.
Ground this in the user's report, the existing design contract, or inspected
working examples. This statement is an understanding check, not a compulsory
approval round when the intent is already clear.

If materially different corrections are plausible, show the relevant crop or
concrete alternatives, ask the smallest precise question and wait before changing
that area. “Make it cleaner” does not establish which layout or behavior to use.
Do not invent the answer, copy a neighboring pattern without checking its purpose,
or turn a reported defect into an unrequested redesign. Continue independent,
confirmed corrections while an uncertain area waits.

## Find the full impact

Read [the checked workflow](references/contract.md) before collecting evidence.
Trace the cause through shared components, tokens, utilities, breakpoint rules,
variants, wrappers and callers. Inspect all owned frontend applications, route
families and duplicated implementations relevant to that cause. Use source
search plus rendered inspection; identical text or CSS is not proof of the same
semantic problem. The bundled scan records literal matches without source-line
contents. It supplements component/route tracing and does not find every alias.

Inventory every discovered occurrence as a confirmed correction, an intentional
variant with evidence, or uncertain. Group shared consumers when they genuinely
share the cause and check their contexts. Record excluded areas and why. If a
shared change could affect an uncertain variant, hold that shared change too;
ask about the variant before touching the file. Never silently omit a doubtful
location or normalize a deliberate difference just for consistency.

## Correct and prove

Capture the failing state and a meaningful regression before the fix. Prefer the
shared owner when the rule is genuinely shared; use a narrowly scoped variant
when contexts differ. Repair independent copies with the same cause as well.
Preserve unrelated code, content, branding and behavior. Add or extend regression
coverage for the demonstrated issue and plausible neighboring failures.

Rerun the same regression against the final source. Capture matching before/after
viewport PNGs for affected route/state/viewport combinations, inspect them, and
exercise the relevant interaction. Cover the reported viewport and representative
narrow/wide, locale/direction, theme, focus, content-length and error/loading
variants when relevant. Verify intentional exceptions remain correct. Source-only
checks or screenshots that were captured but not inspected are incomplete proof.
Rerun the occurrence scan after editing and classify remaining/new matches.

Use the repository's existing browser/test/build tools. Do not install or launch
new external services just for the skill. If reproduction, browser access or a
required environment is unavailable, return a specific blocker instead of a
confident visual fix. Keep screenshots/test data private and inspect captures
for personal information before sharing them.

## Questions, tracking and handoff

Reuse the project's shared scope ledger: **at most ten questions in two batches**,
including earlier skills/chats. Inspect evidence first; ask only questions with
settled prerequisites, record each batch before displaying it, and wait for real
answers. Use bundled `scripts/definition.py` if questions are necessary and no
ledger exists; see [the ledger contract](references/definition-contract.md).
Record uncertain occurrences against pending question IDs. Once answered,
refresh the intake and reclassify them using the actual answer. At an exhausted
budget, hold the uncertain correction and name the missing decision; do not
silently guess or reset the interview.

Use existing GitHub Issue/Project tracking for executable repairs and preserve
unrelated work. The agent prepares intake/output JSON and evidence; do not ask
the user to fill a schema. Validate input before work and output before claiming
completion. No validator result authorizes publication, deployment or acceptance.

Deliver the reported problem, understood correction, shared cause, all confirmed
occurrences corrected, justified exceptions, unanswered questions, proof and
remaining coverage limits. Where staging exists, hand the exact deployed staging
candidate to the user for functional testing under that project's release rules;
local/browser/CI proof is engineering evidence. Say when staging does not exist.
Keep local changes and external actions within the user's authority.

This folder is self-contained: Python 3.10+ and Git for validation/discovery, plus
the target project's browser/toolchain for real rendering. `ready` means the
bounded, evidenced correction is complete; it never means human acceptance or
that every frontend in the repository was automatically discovered.
