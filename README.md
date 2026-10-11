# Context Templates

Public agent skills for **Codex, Cursor, and Claude Code**. GitHub is the source
of truth. [contexttemplates.com](https://contexttemplates.com) leads here.

## Start with the downloadable skill

[Download the Context Templates skill](https://raw.githubusercontent.com/Ginylil/context-templates/main/skills/context-templates/SKILL.md)
([view its source](skills/context-templates/SKILL.md)). Give that file or its URL
to your agent and ask:

> Use this skill to list the available Context Templates skills and install the
> ones I choose for this agent. Preview the installation first.

The bootstrap file is self-contained. Your agent can read it before installing
anything. It explains discovery, safe local installation, updates, and how to
contribute improvements or new skills through a pull request. It is currently
the first published skill; additional skills are reviewed and added individually.

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
bootstrap link above is public. There is no website build or automatic release
publication. Only `skills/` is packaged; private experiments belong in a separate
private repository and must never be copied here as part of an install or build.

The previous YAML template collection and MCP/API publishing flow have been
retired. Existing clones and third-party service data are unaffected by this
repository change. Useful workflows will return as individually reviewed skills.

See [DETAILS](DETAILS.md) for installer behavior and [AGENTS](AGENTS.md) for
repository work rules. Runtime locations follow the official
[Codex skill documentation](https://learn.chatgpt.com/docs/build-skills),
[Cursor skill documentation](https://cursor.com/docs/skills), and
[Claude Code skill documentation](https://code.claude.com/docs/en/skills).
