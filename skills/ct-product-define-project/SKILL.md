---
name: ct-product-define-project
description: "Turn a project idea into an evidence-backed definition of its users, problem, first scope, constraints, and observable success. Use before development planning when these decisions are unclear, with at most 10 questions across 2 batches."
---

# Define a project

Produce a concise project definition and a checked JSON handoff. Investigate
discoverable facts yourself. Ask the user only for consequential choices that
remain unknown. This skill defines the project; it does not build it or publish
tasks. Executable development plans must subsequently use GitHub Issues and
Projects. Unknown GitHub targets may remain explicit at this definition stage.

## Establish the evidence and decision tree

Read the supplied idea, prior answers, and the smallest relevant repository or
document context. Keep facts, user decisions, assumptions, and proposals distinct.
Work without a repository when the project is still an idea. Record source
references and preserve the user's exact constraints. Use current primary sources
for evolving external claims; record uncertainty when access is unavailable.

Read [the contract and command guide](references/contract.md). The agent prepares
the JSON; never make the user fill in a schema. Use `assets/example-input.json`
as a structural example, replacing its project-specific content. Infer reasonable
decision topics from the actual idea rather than running a fixed questionnaire.
Mark only decisions that truly prevent a buildable definition as `blocking`.
Include dependencies between decisions. Record facts and already-given answers
as sourced resolutions so they do not consume questions.

Run this package's `scripts/project.py validate-input` and `start`. Keep the
ledger with the project definition in a user-owned working location, outside the
installed skill. On resuming, inspect `status` and reuse that same ledger. Pass
its path to any collaborating skill or agent; the budget belongs to the scope,
not to an individual skill, agent, or chat. Do not reset it to obtain more questions.
If joining an interview that already asked questions without a ledger, reconstruct
those actual batches and answers first. If their history cannot be established,
report that budget enforcement is blocked rather than claiming a fresh allowance.

## Ask bounded, independent batches

1. Use `status` to inspect unresolved decisions whose prerequisites are settled.
   Choose only the consequential ones that still need a human choice. Four to six
   questions often suffice for the first batch; zero is valid when context is clear.
2. Record an `ask` event **before displaying the batch**. The script enforces
   ten questions total, two batches total, sequential IDs, settled dependencies,
   and no repeated decision or normalized prompt. Count questions when asked,
   including unanswered ones. Each question covers one decision; do not hide
   several questions in a compound prompt or option list.
3. Show the recorded questions together using the runtime's visible question
   surface, or a numbered Markdown batch if none exists. Offer short choices
   and a recommendation when evidence supports one, always allowing free text
   and qualifications. Questions within a batch must be answerable independently.
   Do not ask one question at a time under a shared batch label.
4. Wait for submitted answers. A recommendation, preselected option, silence, or
   elapsed time is not an answer. Record actual answers and their source using
   `answer` events; preserve qualifications. Partial responses remain pending.
   Re-display the same recorded batch after a delivery failure instead of
   creating another batch. Use the same event ID and content for an uncertain retry.
5. Reassess the decision tree. Add newly relevant decisions with `add-decisions`
   and resolve newly discovered facts with `resolve`. Ask a second batch only if
   it materially changes scope, risk, or the path to implementation. Reuse prior
   answers instead of asking again. Stop after the first batch when it suffices.

Never ask an eleventh question or create a third batch. At the limit, carry
nonblocking unknowns as explicit assumptions with their impact; report genuine
blockers and the smallest next action. Do not convert an unanswered question
into an assumed answer or treat the limit as permission for an external action.
If a critical answer changes an already-settled decision, stop and report the
conflict rather than rewriting history; scope amendments need a separately
reviewed follow-up contract, not a fresh budget for this interview.

## Produce and check the definition

Write the users, problem, desired outcome, first useful scope, exclusions,
observable success criteria with verification methods, constraints, sourced
decisions, assumptions, blockers, tracking references, and next action. Keep
features traceable to the problem. Avoid prematurely choosing a technology,
provider, business model, or large roadmap when the evidence does not require it.

Use `status` to obtain current input/ledger digests and settled decisions. Author
the output JSON using [the output contract](references/contract.md#definition).
Run `validate-output` before handing it off; run `render` to produce the readable
Markdown definition from the checked JSON. Both ready and blocked definitions
must preserve constraints and account for all unresolved decisions. Blocked
definitions describe the best current understanding without pretending planning
can proceed. `ready-for-planning` means scope readiness, not customer validation,
GitHub publication, implementation, or acceptance.

Deliver the readable definition, JSON and ledger paths, question/batch usage,
important assumptions or blockers, and the next concrete action. A later task
planner must verify the target GitHub repository and Project, publish the task
graph, and read back its Issues and Project items before claiming planning complete.
No other skill installation or private library is required for this definition.

## Validation boundary

Python 3.10+ is the only script dependency. Commands make no network requests and
execute no project or source-provided commands. Scripts check structure,
decision references, question limits, history consistency and handoff bindings.
They cannot detect every semantic duplicate or compound question, authenticate
an answer's authorship, prove source truth, or prevent deliberate history edits.
The agent owns those judgments. Keep existing user artifacts and secrets out of
the public package. New ledger and Markdown destinations are never overwritten;
only validated events update the selected ledger, with locking and stale-write checks.
