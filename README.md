# Context Templates

Public agent skills for **Codex, Cursor, and Claude Code**. GitHub is the source
of truth. [contexttemplates.com](https://contexttemplates.com) leads here.

## Quick start — copy into your agent

Copy and paste this prompt into Codex, Cursor, or Claude Code:

```text
Please read this skill:
https://raw.githubusercontent.com/Ginylil/context-templates/main/skills/context-templates/SKILL.md

Review the available skills and recommend which ones to install locally for my work.
Briefly explain each recommendation and offer an "Install all skills" option.
Wait for me to choose, then preview the installation before installing the
selected skills or the full catalog for this agent.
```

You can also [download the skill](https://raw.githubusercontent.com/Ginylil/context-templates/main/skills/context-templates/SKILL.md)
and attach it to your agent ([view its source](skills/context-templates/SKILL.md)).

The bootstrap file is self-contained. Your agent can read it before installing
anything. It explains discovery, safe local installation, updates, and how to
contribute improvements or new skills through a pull request. The catalog includes
the bootstrap, twenty project lifecycle skills, and the Dynamic UMLs family below;
additional skills are reviewed and added individually.

## How skills and scripts work together

Each installed skill or built ZIP is a complete folder. `SKILL.md` tells your agent
when and how to use it; optional `references/`, `assets/`, and `scripts/` provide supporting
guidance, templates, and deterministic tools. For Dynamic UMLs, the agent
investigates your question and prepares a diagram model; bundled Python scripts
validate that model and render one interactive HTML file you can open locally.
The page works offline, with no Python runtime needed to view it.

The Makefile is a convenient interface to the Python installer. Choose your
preferred agent with `make install-codex`, `make install-cursor`, or
`make install-claude`; `make install` installs for all three. Add `SKILL=<name>`
to install one skill. Installation assembles the complete folder from its source
resources and JSON package manifest into that agent's local skills directory. It does not
run bundled skill scripts; your agent uses them when carrying out the skill.
Python 3.10+ is required for installation and UML generation. Make is optional:
the equivalent Python commands are listed under [Install locally](#install-locally).

## Project lifecycle skills

Start with `ct-product-manage-project` to find the next useful step, or invoke a
focused skill directly. Existing scope, source evidence and GitHub tracking are
reused; the guide does not force every project through all twenty skills.

```text
Use ct-product-manage-project to help me define and build a small web app.
Inspect what already exists and take the next useful step toward my goal.
```

| Skill | Job |
| --- | --- |
| [`ct-product-manage-project`](skills/ct-product-manage-project/SKILL.md) | Guide the next project step using checked handoffs |
| [`ct-product-define-project`](skills/ct-product-define-project/SKILL.md) | Define users, scope, constraints and success |
| [`ct-product-review-product`](skills/ct-product-review-product/SKILL.md) | Assess customer value and product outcomes |
| [`ct-rnd-design-architecture`](skills/ct-rnd-design-architecture/SKILL.md) | Design components, interfaces and tradeoffs |
| [`ct-rnd-plan-development`](skills/ct-rnd-plan-development/SKILL.md) | Plan complete GitHub-tracked development slices |
| [`ct-rnd-set-up-project`](skills/ct-rnd-set-up-project/SKILL.md) | Establish a runnable, checked repository |
| [`ct-rnd-build-feature`](skills/ct-rnd-build-feature/SKILL.md) | Implement one complete admitted feature |
| [`ct-rnd-fix-bug`](skills/ct-rnd-fix-bug/SKILL.md) | Reproduce, diagnose and repair a defect |
| [`ct-rnd-review-code`](skills/ct-rnd-review-code/SKILL.md) | Review behavior and repository standards |
| [`ct-rnd-improve-agent-setup`](skills/ct-rnd-improve-agent-setup/SKILL.md) | Improve agents from observed workflow problems |
| [`ct-design-build-interface`](skills/ct-design-build-interface/SKILL.md) | Design and verify a usable interface |
| [`ct-qa-plan-tests`](skills/ct-qa-plan-tests/SKILL.md) | Define behavioral coverage and verification |
| [`ct-qa-test-user-flows`](skills/ct-qa-test-user-flows/SKILL.md) | Execute flows and report actual results |
| [`ct-security-review-project`](skills/ct-security-review-project/SKILL.md) | Assess demonstrated security risks and uncertainty |
| [`ct-devops-release-project`](skills/ct-devops-release-project/SKILL.md) | Verify the requested release milestone |
| [`ct-devops-release-apple-app`](skills/ct-devops-release-apple-app/SKILL.md) | Discover setup, wrap web apps and release through TestFlight and the App Store |
| [`ct-devops-release-android-app`](skills/ct-devops-release-android-app/SKILL.md) | Discover setup, wrap web apps and release through Play testing and production |
| [`ct-devops-maintain-project`](skills/ct-devops-maintain-project/SKILL.md) | Review health, spend, changes and recovery |
| [`ct-marketing-research-market`](skills/ct-marketing-research-market/SKILL.md) | Research audiences, competitors and positioning |
| [`ct-marketing-launch-product`](skills/ct-marketing-launch-product/SKILL.md) | Prepare or execute an authorized launch |

Each installed folder and ZIP works independently. The guide checks which specialists
are installed. The agent prepares JSON, while bundled Python tools validate
structure, scope/source bindings, proof references and domain-specific rules.
Explicit command capture records actual argv, output, exit status and source
fingerprints without shell execution or inferred retries. Capturing a command
does not authorize it; use only actions already in scope.

All specialists share the same **ten-question/two-batch** scope ledger. Development
plans require GitHub Issues and Projects with authoritative readback before
execution. Local-only preparation is supported and remains explicitly blocked at
that tracking gate. Completed assessments can expose failed tests or risks;
they do not imply acceptance or permission to deploy/publish.

The Apple and Android release skills also work directly for an existing app.
They keep upload, processing, tester access, device proof, review and public
release separate, bind the exact app/build/export and audience, and accept only
logical credential-store references. Both store skills include configuration
discovery, exact setup locations and a checked web-to-native wrapping workflow.
Their example input hashes are generated from the included synthetic JSON.
Actual signing keys, tokens, service-account files, tester details and runtime
evidence stay outside this public catalog.

These packages have local contract, negative-control, standalone-installation
and disposable-workspace tests. Mocked remote readbacks and source fixtures do
not establish live provider behavior, actual agent discovery or human staging
acceptance. There is no staging environment for this catalog itself.

### Define a project

Use [`ct-product-define-project`](skills/ct-product-define-project/SKILL.md) to
turn an idea into a clear definition of its users, problem, first scope,
constraints, and observable success before development planning:

```text
Use ct-product-define-project to define a small browser app for tracking client
follow-ups. Investigate what you can, then ask only the decisions you need from me.
```

The agent prepares the structured artifacts. A bundled Python tool validates
inputs, keeps one resumable interview ledger, and validates the output before
rendering a readable Markdown brief. The interview allows **at most ten questions
across two batches**, shared across agents working on the same scope. Questions
in a batch must have their prerequisites settled; recommendations never become
answers automatically. Clear requests can finish without questions. Missing
critical answers produce an explicit blocked definition.

Install the complete folder with
`make install-codex SKILL=ct-product-define-project`, selecting the target agent
you use. The skill runs independently with Python 3.10+ and no package or service
dependencies. See its [contract and commands](skills/ct-product-define-project/references/contract.md)
and [synthetic output example](skills/ct-product-define-project/assets/example-definition.json).
GitHub Issues and Projects are required for subsequent executable task planning;
this definition skill neither publishes tasks nor verifies remote tracking objects.
Validated JSON proves contract consistency, not customer demand or user acceptance.

## Dynamic UMLs

Use Dynamic UMLs to explain how a system works: messages over time, types and
relationships, decision paths, state changes, parallel activities, or component
boundaries. Ask for a diagram in plain language, for example
`/ct-dynamic-uml-sequence for a browser, application, and identity-provider login`.
Choose a focused skill below, or use `ct-dynamic-uml` to select a suitable view.

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
| [`ct-dynamic-uml`](skills/ct-dynamic-uml/SKILL.md) — choose a view | [Example gallery](https://ginylil.github.io/context-templates/examples/dynamic-umls/index.html) |
| [`ct-dynamic-uml-sequence`](skills/ct-dynamic-uml-sequence/SKILL.md) | [Three-party sign-in](https://ginylil.github.io/context-templates/examples/dynamic-umls/sequence.html) · [Long sequence: 32 messages, six participants](https://ginylil.github.io/context-templates/examples/dynamic-umls/sequence-long.html) |
| [`ct-dynamic-uml-class`](skills/ct-dynamic-uml-class/SKILL.md) | [Orders and payments](https://ginylil.github.io/context-templates/examples/dynamic-umls/class.html) |
| [`ct-dynamic-uml-flowchart`](skills/ct-dynamic-uml-flowchart/SKILL.md) | [Review readiness](https://ginylil.github.io/context-templates/examples/dynamic-umls/flowchart.html) |
| [`ct-dynamic-uml-state`](skills/ct-dynamic-uml-state/SKILL.md) | [Order lifecycle](https://ginylil.github.io/context-templates/examples/dynamic-umls/state.html) |
| [`ct-dynamic-uml-activity`](skills/ct-dynamic-uml-activity/SKILL.md) | [Parallel preparation](https://ginylil.github.io/context-templates/examples/dynamic-umls/activity.html) |
| [`ct-dynamic-uml-component`](skills/ct-dynamic-uml-component/SKILL.md) | [One catalog, three agents](https://ginylil.github.io/context-templates/examples/dynamic-umls/component.html) |

The UML skills now use the `ct-dynamic-uml` prefix. Install them by their new
names. Existing installations with `dynamic-*` names remain untouched; the
installer does not rename, replace or remove those folders. Both versions can
therefore appear until you explicitly remove the old copies. Hosted example
URLs remain under `examples/dynamic-umls/`.

[Open the interactive example gallery](https://ginylil.github.io/context-templates/examples/dynamic-umls/index.html)
to try all six views and the long sequence in your browser. The repository's
existing GitHub Pages hosting serves these static examples. You can also download
the HTML or open it from your clone to use it offline; GitHub's file view displays
the source. These are a focused UML subset; flowcharts are general process notation.

Install the complete folder for the skill you choose, including its resources:

```sh
make install-codex SKILL=ct-dynamic-uml-sequence
```

Then ask your agent:

```text
/ct-dynamic-uml-sequence for 3 way handshake login
/ct-dynamic-uml-class for this project's billing model
/ct-dynamic-uml-flowchart for the failed-payment recovery process
```

Use `$ct-dynamic-uml-sequence` or its name in prose if your agent does not expose
slash invocation. Invocation syntax and discovery must be checked in your agent.
The login request should clarify TCP versus browser/app/provider sign-in when
context leaves it ambiguous. Generating a page uses Python 3.10+; the resulting
HTML requires only a browser. Existing output files are never silently replaced.

Each focused skill works independently after assembly. Shared Python helpers live
once under `shared/dynamic-uml/`; JSON manifests select the installed scripts.
Static diagram assets and guides remain canonical under `skills/ct-dynamic-uml/`,
with synchronized focused copies.
Use `make examples` after changing canonical resources or example JSON, then
`make check` to catch drift. See [DESIGN](DESIGN.md) for visual and browser checks.

## Source folders and standalone packages

Repository skill folders select shared helpers through `assets/package.json`;
copying a raw source folder with a generic folder-copy installer is insufficient.
Use the supported installer or a built ZIP. To inspect or run a skill locally
without installing it, assemble a new directory first:

```sh
python3 scripts/skills.py assemble --skill ct-rnd-fix-bug --output dist/review-skills
```

The output must not already exist. It contains a complete `ct-rnd-fix-bug/`
folder; run its documented commands there. Omit `--skill` to assemble the full
catalog. On Windows, use `py -3` instead of `python3`. Installation, assembly,
and ZIP builds use the same payload logic and never execute packaged scripts.
The existing `assets/contract.json` files still define validation policy;
package manifests only select helpers. See [package composition](DETAILS.md#package-composition).

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

The installer assembles the complete skill folder, records ownership and content
hashes of the assembled output, and leaves unrelated skills alone. Rerunning it is a no-op for unchanged
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
git diff HEAD..origin/main -- skills shared scripts
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

Before contributing, install the free Gitleaks CLI and pre-commit, then run
`make setup-hooks` once per clone to check staged files before commits. Run
`make secret-check` to check current public files and reachable Git history.
See [contributor security setup](CONTRIBUTING.md#secret-protection)
for installation, Windows commands, coverage and recovery steps.

Builds produce a ZIP for each complete skill plus a checksummed `catalog.json`
in `dist/`. These files are reproducible local outputs and are also retained as
CI artifacts. A GitHub Actions artifact download may require signing in; the raw
bootstrap link above is public. Existing GitHub Pages hosting serves the example
files; there is no separate website application or automatic release publication.
Packages contain skill-local resources plus explicitly selected scripts from
`shared/`. Source-only `assets/package.json` manifests are excluded. Private
experiments belong in a separate private repository and must never be copied here.

The previous YAML template collection and MCP/API publishing flow have been
retired. Existing clones and third-party service data are unaffected by this
repository change. Useful workflows will return as individually reviewed skills.

See [DETAILS](DETAILS.md) for installer behavior and [AGENTS](AGENTS.md) for
repository work rules. Runtime locations follow the official
[Codex skill documentation](https://learn.chatgpt.com/docs/build-skills),
[Cursor skill documentation](https://cursor.com/docs/skills), and
[Claude Code skill documentation](https://code.claude.com/docs/en/skills).
