---
name: ct-product-configure-project
description: "Ignite a project by discovering and recording its source control, task trackers, documentation locations and optional validation/release environment. Ask only for missing choices, preview a secret-free project context file, and make repository storage the final question."
---

# Ignite project context

Configure a project's tool choices without redefining its product or building an
application. This standalone utility is outside the lifecycle manager graph. It
produces informational context, not credentials, integrations or permission to
publish. Other CT skills do not automatically consume this new profile yet; their
existing provider restrictions remain in force. Recording Jira does not make a
GitHub-only validator support Jira.

## Discover before asking

Infer the intended project from the current request and conversation. Confirm its
actual root; do not mistake a temporary artifact directory for the project. Work
without Git when the project is documentation-only or has no repository yet.
Read applicable instructions, existing `context-templates/project.json`, nearby
README/contributor/design docs, Git remotes and relevant CI configuration. Use
available read-only connectors to confirm named tracker/docs targets when needed.
Never create an account, repository, board, ticket or document merely for setup.

Separate discovered facts, user-confirmed choices and unverified suggestions.
Detect existing source control, task tracking, docs and environment conventions;
reuse them rather than asking the user to retype discoverable facts. Do not open
secret stores, `.env`, authentication files or signing material. Locations and
provider names suffice; authentication stays in the runtime's existing tooling.

## Ask only about missing choices

Ask one short numbered question at a time, with sensible choices and free text.
Wait for an actual answer. If a native question surface does not appear, repeat
the same question visibly in chat without advancing its number. Preserve partial
answers across turns and reuse the current question on resume; a recommended
option, silence or an elapsed wait is not a decision. A simulation keeps all
profile content in chat and makes no project or external writes.

Resolve these areas only where evidence leaves a material choice:

- Source control: provider and repository, or explicit local/none/undecided.
- Task management: one or several systems, their project/board locations and
  purposes, with a primary tracker. Source hosting and task tracking are separate.
- Documentation: allow multiple locations and explain which holds requirements,
  technical docs, decisions or runbooks. Identify the primary documentation source.
  Jira, Confluence and Bitbucket are distinct tools, not one "Atlassian" setting.
- Optional validation and release context: CI, execution location, documented
  check commands, staging/production references and acceptance rules when relevant.

Do not restart product discovery or reset an existing definition interview ledger.
Carry constraints forward; a profile cannot override user or repository instructions.
The user can explicitly defer a choice, represented as `undecided`, or select
`none`. Do not invent defaults for missing targets. No GitHub-only requirement is
imposed by this profile format. Choosing a provider declares intent, not verified
access or an implemented adapter. Existing projects reuse an existing profile;
show proposed differences and never overwrite it silently.

## Prepare and validate the preview

Read [the profile contract](references/profile.md) and use
`assets/example-project.json` only as a synthetic structural example. The agent
fills the profile; never ask the user to edit a schema. Keep a draft in an existing
private working area outside the project and installed skill when a file is
needed for validation. Do not put a real project's data into catalog examples.

Use Python 3.10+ (or `py -3` on Windows):

```text
python3 <skill>/scripts/project_context.py validate <private-draft.json>
python3 <skill>/scripts/project_context.py render <private-draft.json>
```

Source checkout users must assemble or install the complete package first.
The helper validates data and renders to stdout. It never writes files, reads
remote providers or executes declared commands. Respect execution-location rules;
do not start tests, servers or services just because the profile lists them.

Show the complete proposed JSON, the exact prospective destination, unresolved
choices and any access/integration gaps. Review every value for secrets and for
private information unsuitable for the intended repository audience. Credential-free
does not mean public-safe. Remove access-bearing links, private paths and identifying
details from a public version; an unresolvable disclosure conflict stays local.
The scanner is heuristic and does not authenticate facts, permissions or privacy.

## Make saving the final question

Only after the content questions and preview are complete, ask the final question:
"Do you want this exact project context file added to the repository, kept local
only, or left as a preview?" State that the repository destination is
`<project>/context-templates/project.json`. For local-only storage, propose an
existing private user-owned location outside the repository and report its path.
Show the actual location before asking. If the user changes content at this point,
refresh the preview and ask the saving question again for the revised content.

A repository choice authorizes writing that reviewed file, not staging, committing,
pushing, changing ignore rules or publishing it. Keep-local and preview choices
must not modify the project, Git metadata or global agent instructions. An
existing different file requires a reviewed update decision; identical content
is a no-op. Keep unresolved drafts explicitly marked as drafts. Declining to save
is a successful preview outcome, not an incomplete setup requiring more persuasion.

Return the chosen storage outcome, exact saved path when applicable, what was
discovered versus selected, remaining undecided fields and the profile-consumption
limitation. Do not claim a tool connection, project migration, automatic skill
adaptation or successful runtime discovery merely because the profile is valid.
