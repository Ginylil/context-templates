---
name: ct-rnd-prepare-next-session
description: "Prepare a copy-paste next-session prompt or conversation handoff from current decisions and checked project state. Use for next chat, continuation prompt, session summary, wrap-up context, or resuming work later; distinguish verified work, uncertainty, and one immediate objective."
---

# Prepare next session

Turn the relevant conversation into an execution handoff that a fresh agent can
use without hidden chat history. Return one ready-to-paste prompt, or state that
no follow-up is needed when the work is complete. This request authorizes a
handoff, not implementation, commits, publication, deployment or a new chat.

## Refresh the smallest relevant context

Infer the latest requested repo, issue, PR, project or artifact. Reuse the current
decision frame and selected next action; do not restart discovery or invent
cleanup work. Inspect available durable decision artifacts before selecting a
new objective. If there is no defensible next action, make a focused assessment
of the next action the objective. If blocked, prepare a blocker-resolution prompt.

For repository work, read applicable AGENTS instructions, the README and command
definitions, and the files nearest the next task. Check the absolute workspace
path, `git status --short --branch`, `git rev-parse HEAD`, and relevant diffs.
Preserve unrelated edits. Recheck live issues, PRs, Projects, CI or deployments
only when the continuation depends on them. Use available read-only tools; do
not run tests, paid jobs, package installation or external writes just to recap.
Record checks that were not run rather than suggesting they passed.

Treat memory and prior chat claims as leads. Separate implemented, committed,
pushed, merged, deployed, tested and accepted states. A green local test is not
staging acceptance or production readiness. If a source is unavailable, retain
it as unverified with the exact first check for the next agent. Do not silently
drop a blocker or convert silence into an answer or permission.

## Prepare checked artifacts

Read [the input/output contract and commands](references/contract.md). The agent
fills the JSON from evidence; do not ask the user to complete a schema. Keep
runtime input, observations, output and prompt outside the installed skill and
inspected workspace, using an existing private working directory. Include only
the context needed to continue. Never copy private histories into this public
skill, parse `.env` or signing files, or include credentials, cookies, tokens or
authentication URLs. Sanitize captured observations before referencing them.

Create the input and source references. A source marked verified needs a checked
timestamp and an actual file with its computed SHA-256. For GitHub, Git and
conversation observations, that file is sanitized evidence, not authentication
of the observation. If access is unavailable, use an unverified source with no
invented receipt. Validate input, then compute its canonical digest:

```text
python3 <skill>/scripts/handoff.py validate-input input.json
python3 <skill>/scripts/handoff.py hash-input input.json
```

Prepare output with that digest. Preserve every input constraint, carry every
unchecked source with a first verification step, and bind each verified claim
and claimed executed check to verified source IDs. Keep one immediate objective;
preserve an already selected action. Completed scope uses `no-follow-up` with
no objective. Blocked scope requires actionable blockers and a resolution goal.

```text
python3 <skill>/scripts/handoff.py validate-output input.json output.json
python3 <skill>/scripts/handoff.py render input.json output.json --prompt next-session.txt
```

Python 3.10+ is the only validator dependency; on Windows use the available
`py -3` or `python`. No other catalog skill is required. For repository source
folders, use the supported installer or `scripts/skills.py assemble` first so
the manifest-selected helper modules are present.

## Deliver

Return a short lead-in and one copy-paste text block from the validated render.
The prompt names what to read first, verified and unchecked state, the decision
frame, one objective, constraints, exact useful validation instructions, and the
expected final report. Mention material verification gaps before the block and
inside it. For completed scope, return the no-follow-up result instead of
manufacturing another task. Do not create a new conversation automatically.

On repeated requests, reuse unchanged evidence and the same handoff when still
current. Rendering identical content to the same regular file is a no-op;
different existing content is preserved and requires an explicitly chosen new
path or a separately authorized edit. Do not scatter parallel handoff artifacts.

Scripts check structure, declared state consistency, source bytes, input binding,
constraint retention and known secret signatures. They do not verify that prose
matches a source, authenticate approvals or manual observations, contact GitHub,
prove freshness of remote state, or establish that the agent chose the best goal.
Review the rendered prompt for unsupported claims and scope changes before
delivery. A validator pass never authorizes the next session's actions.
