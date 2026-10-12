# Context Templates

Public agent skills for **Codex, Cursor, and Claude Code**. GitHub is the source
of truth. [contexttemplates.com](https://contexttemplates.com) leads here.

## Quick start — copy into your agent

Copy and paste this prompt into Codex, Cursor, or Claude Code:

```text
Please read this skill:
https://raw.githubusercontent.com/Ginylil/context-templates/main/skills/context-templates/SKILL.md

Review the available skills and recommend which ones to install locally for my work.
Briefly explain each recommendation. Wait for me to choose, then preview the
installation before installing the selected skills for this agent.
```

You can also [download the skill](https://raw.githubusercontent.com/Ginylil/context-templates/main/skills/context-templates/SKILL.md)
and attach it to your agent ([view its source](skills/context-templates/SKILL.md)).

The bootstrap file is self-contained. Your agent can read it before installing
anything. It explains discovery, safe local installation, updates, and how to
contribute improvements or new skills through a pull request. The catalog includes the bootstrap and the Dynamic UMLs family described below;
additional skills are reviewed and added individually.

## How skills and scripts work together

Each skill is a complete folder: `SKILL.md` tells your agent when and how to use
it, while optional `references/`, `assets/`, and `scripts/` provide supporting
guidance, templates, and deterministic tools. For Dynamic UMLs, the agent
investigates your question and prepares a diagram model; bundled Python scripts
validate that model and render one interactive HTML file you can open locally.
The page works offline, with no Python runtime needed to view it.

The Makefile is a convenient interface to the Python installer. Choose your
preferred agent with `make install-codex`, `make install-cursor`, or
`make install-claude`; `make install` installs for all three. Add `SKILL=<name>`
to install one skill. Installation copies the complete folder, including any
scripts and resources, into that agent's local skills directory. It does not
run bundled skill scripts; your agent uses them when carrying out the skill.
Python 3.10+ is required for installation and UML generation. Make is optional:
the equivalent Python commands are listed under [Install locally](#install-locally).

## Dynamic UMLs

Use Dynamic UMLs to explain how a system works: messages over time, types and
relationships, decision paths, state changes, parallel activities, or component
boundaries. Ask for a diagram in plain language, for example
`/dynamic-sequence-diagram for a browser, application, and identity-provider login`.
Choose a focused skill below, or use `dynamic-umls` to select a suitable view.

Each produces a standalone HTML page with an interactive
walkthrough. Each skill investigates the supplied context, makes minimal explicit
assumptions, and asks **at most five questions** for material unknowns. Pages include
playback, step navigation, an element inspector, overview, meaningful alternate
scenarios and Ginylil branding linked to [contexttemplates.com](https://contexttemplates.com).
Details open from the info icon in a modal: playback pauses while you read and
resumes on close only if it was playing. The optional Sidebar trades canvas width
for persistent details. All six types use the page for vertical scrolling, with
horizontal panning when needed. Sequence walkthroughs show as many participants
as fit, prioritizing the active exchange and previous/next messages. Only groups
that exceed the available width collapse into `…`. Select the dots or
Overview to see all participants and messages; the full view can pan horizontally.
Playback follows the active message or state, with sticky controls and sequence
participant labels.
Scenario menus open below the trigger in the page theme. Flowcharts read
vertically, keep retries on outer side rails, and compose larger processes as
clickable subprocesses, with a maximum of seven nodes per view. A bundled Python
verifier checks these rules before rendering. State diagrams share the node limit
and routing checks, allow horizontal layouts and expandable state detail views,
and place transition causes directly on their arrows. Pages use the supplied Ginylil
coffee-and-sun logo as a small, subdued transparent mark in both header and footer.
State diagrams fit the available width when readable. Diagram canvases have no inner vertical scrollbar.
Pages open locally and work offline, without a server or external dependencies.

| Skill / command | View example in browser |
| --- | --- |
| [`dynamic-umls`](skills/dynamic-umls/SKILL.md) — choose a view | [Example gallery](https://ginylil.github.io/context-templates/examples/dynamic-umls/index.html) |
| [`dynamic-sequence-diagram`](skills/dynamic-sequence-diagram/SKILL.md) | [Three-party sign-in](https://ginylil.github.io/context-templates/examples/dynamic-umls/sequence.html) · [Long sequence: 32 messages, six participants](https://ginylil.github.io/context-templates/examples/dynamic-umls/sequence-long.html) |
| [`dynamic-class-diagram`](skills/dynamic-class-diagram/SKILL.md) | [Orders and payments](https://ginylil.github.io/context-templates/examples/dynamic-umls/class.html) |
| [`dynamic-flowchart`](skills/dynamic-flowchart/SKILL.md) | [Review readiness](https://ginylil.github.io/context-templates/examples/dynamic-umls/flowchart.html) |
| [`dynamic-state-diagram`](skills/dynamic-state-diagram/SKILL.md) | [Order lifecycle](https://ginylil.github.io/context-templates/examples/dynamic-umls/state.html) |
| [`dynamic-activity-diagram`](skills/dynamic-activity-diagram/SKILL.md) | [Parallel preparation](https://ginylil.github.io/context-templates/examples/dynamic-umls/activity.html) |
| [`dynamic-component-diagram`](skills/dynamic-component-diagram/SKILL.md) | [One catalog, three agents](https://ginylil.github.io/context-templates/examples/dynamic-umls/component.html) |

[Open the interactive example gallery](https://ginylil.github.io/context-templates/examples/dynamic-umls/index.html)
to try all six views and the long sequence in your browser. The repository's
existing GitHub Pages hosting serves these static examples. You can also download
the HTML or open it from your clone to use it offline; GitHub's file view displays
the source. These are a focused UML subset; flowcharts are general process notation.

Install the complete folder for the skill you choose, including its resources:

```sh
make install-codex SKILL=dynamic-sequence-diagram
```

Then ask your agent:

```text
/dynamic-sequence-diagram for 3 way handshake login
/dynamic-class-diagram for this project's billing model
/dynamic-flowchart for the failed-payment recovery process
```

Use `$dynamic-sequence-diagram` or its name in prose if your agent does not expose
slash invocation. Invocation syntax and discovery must be checked in your agent.
The login request should clarify TCP versus browser/app/provider sign-in when
context leaves it ambiguous. Generating a page uses Python 3.10+; the resulting
HTML requires only a browser. Existing output files are never silently replaced.

Each focused skill works independently. Shared resources have one canonical source
under `skills/dynamic-umls/`; synchronized copies make every ZIP self-contained.
Use `make examples` after changing canonical resources or example JSON, then
`make check` to catch drift. See [DESIGN](DESIGN.md) for visual and browser checks.

## Install locally

Requires Git and Python **3.10+**. Installation has no Python package dependencies
and makes no network requests. Clone the repository into an unused directory:

```sh
git clone https://github.com/Ginylil/context-templates.git
cd context-templates
make catalog
make install INSTALL_ARGS=--dry-run
```

Choose the agents you use:

```sh
make install-codex
make install-cursor
make install-claude
make install          # all three
```

Select one skill with `make install-codex SKILL=context-templates`.

| Agent | User-level destination |
| --- | --- |
| Codex | `~/.agents/skills/<name>/` |
| Cursor | `~/.cursor/skills/<name>/` |
| Claude Code | `~/.claude/skills/<name>/` |

The installer copies the complete skill folder, records ownership and content
hashes, and leaves unrelated skills alone. Rerunning it is a no-op for unchanged
managed copies. Updates refuse unmanaged name conflicts, links, and locally
edited managed copies; there is no force-overwrite option or automatic removal.
Keep local modifications, contribute them by PR, or choose a different name
before resolving a conflict. Do not edit the ownership receipt to bypass it.

Each agent may also discover skills through compatibility paths. If the same
name already appears from another library, resolve that duplication deliberately;
this installer does not modify that other library. Start a fresh session or
restart the agent if a new skill is not visible. Verify discovery and invocation
in the agent you use; a copied file alone does not prove either.

### Windows or machines without Make

The Python interface performs the same operations. On Windows use `py -3` (or
an available Python 3.10+ executable); on macOS/Linux use `python3`:

```text
py -3 scripts/skills.py list
py -3 scripts/skills.py install --agent all --dry-run
py -3 scripts/skills.py install --agent codex --skill context-templates
py -3 scripts/skills.py install --agent cursor
py -3 scripts/skills.py install --agent claude
```

### Receive updates on another computer

In a clean checkout tracking this repository's `main`, review upstream changes,
then fast-forward and reinstall:

```sh
git fetch origin
git log --oneline HEAD..origin/main
git diff HEAD..origin/main -- skills scripts/skills.py
git pull --ff-only
make install
```

Inspect branch and worktree state first. Preserve edits or use a separate clean
checkout if the current checkout is dirty or on a contribution branch. This is
an explicit update workflow; automatic cross-computer synchronization is deferred.

## Contribute through a PR

Ask your agent:

> Use the Context Templates skill to improve `<skill-name>` and open a pull
> request against Ginylil/context-templates.

Or:

> Use the Context Templates skill to propose a new skill for `<purpose>`, validate
> it locally, and open a pull request against Ginylil/context-templates.

The agent works on a branch (or your fork), validates the change, and opens a PR
for maintainer review. GitHub authentication is needed for submission; a local
installation request alone does not create a PR. See [CONTRIBUTING](CONTRIBUTING.md)
for the canonical folder format and validation requirements.

## Maintainer checks and downloads

```sh
make check
make build
```

Builds produce a ZIP for each complete skill plus a checksummed `catalog.json`
in `dist/`. These files are reproducible local outputs and are also retained as
CI artifacts. A GitHub Actions artifact download may require signing in; the raw
bootstrap link above is public. Existing GitHub Pages hosting serves the example
files; there is no separate website application or automatic release publication.
Only `skills/` is packaged; private experiments belong in a separate
private repository and must never be copied here as part of an install or build.

The previous YAML template collection and MCP/API publishing flow have been
retired. Existing clones and third-party service data are unaffected by this
repository change. Useful workflows will return as individually reviewed skills.

See [DETAILS](DETAILS.md) for installer behavior and [AGENTS](AGENTS.md) for
repository work rules. Runtime locations follow the official
[Codex skill documentation](https://learn.chatgpt.com/docs/build-skills),
[Cursor skill documentation](https://cursor.com/docs/skills), and
[Claude Code skill documentation](https://code.claude.com/docs/en/skills).
