---
name: context-templates
description: "Find, install, and update skills from Ginylil/context-templates, request new skills or improvements through GitHub issues, or contribute implemented changes through pull requests to that repository."
---

# Context Templates

Use the public repository at https://github.com/Ginylil/context-templates as the
source of truth. Help the user choose useful skills, install them for their local
agent, and contribute improvements. This file is self-contained so it can be
downloaded and given to an agent before anything is installed.

## Establish the task

Identify whether the user wants to discover skills, install/update their local
copies, request a change, improve a published skill, or contribute a new skill.
A request is a GitHub issue or follow-up comment; an implemented upstream
contribution opens a PR. A local update does neither.

For requests for new skills, changes to existing CT skills, or catalog features,
read [`ct-product-request-skill-change`](https://github.com/Ginylil/context-templates/blob/main/skills/ct-product-request-skill-change/SKILL.md).
It supports drafts, duplicate discovery, authorized issue submission and follow-up
comments in this repository. A question about sending messages is not itself
permission to post. Reading the skill requires no installation or local clone.

Resolve the actual operating system, available Git/Python/Make commands, target
agent (Codex, Cursor, Claude Code, or all three), checkout location, and selected
skill names from the user's request and local evidence. Ask only for choices
that cannot be inferred safely. Keep checkout paths specific to this computer.

For local installation or implementation, use an existing checkout only after
checking its remote, branch, worktree, and dirty state. Otherwise clone the public
repository into an unused user-owned directory. Do not clone over an existing
folder or change an unrelated checkout.
Git and Python 3.10+ are needed for local installation; Make is optional. An
authenticated GitHub account is needed to submit issues, comments or PRs.
Requests can use an available connector or browser; contribution commands below
use GitHub CLI.

## Discover, install, or update

1. Read the checkout's current README, CONTRIBUTING, and AGENTS instructions.
   List installable skills with `make catalog` or
   `python3 scripts/skills.py list --json`. Briefly explain the skills and
   recommend those relevant to the user's work. Offer both individual selections
   and an explicit "Install all skills" option for the requested agent. If the
   user already chose individual skills or the full catalog, honor that choice
   without asking them to choose again. "All skills" means the full catalog for
   that agent; installing for all three agents is a separate target choice.
   Read the selected `SKILL.md` and supporting files before executing their
   instructions or bundled scripts.
2. Use the supported installer, not a hand-written recursive copy or symlink:

   ```text
   make install-codex SKILL=<name> INSTALL_ARGS=--dry-run
   make install-codex SKILL=<name>
   make install-cursor SKILL=<name>
   make install-claude SKILL=<name>
   make install-codex INSTALL_ARGS=--dry-run
   make install-codex
   make install
   ```

   Select the command matching the requested agent. Omitting `SKILL` installs
   the current public catalog; `make install` installs it for all three agents.
   Preview every requested target before an actual install. Without Make, use
   `python3 scripts/skills.py install --agent codex --skill <name> --dry-run`,
   then the same command without `--dry-run`. For the full catalog, omit
   `--skill` from both commands; do not pass `--skill all`. Agents are `codex`,
   `cursor`, `claude`, and `all`. On Windows, use the available `py -3` or `python`
   interpreter for the same script; native Make is not required.
3. The installer assembles complete skill folders using the source-only
   `assets/package.json` manifests and shared helpers. Use the Make or
   Python installer; copying a raw source folder may omit required scripts.
   Installation never executes packaged scripts. It records assembled-file hashes and
   ownership in the documented user-level directories, leaves unrelated skills alone,
   and refuses unmanaged conflicts, links, and edited installed copies. Do not
   bypass a conflict with force, deletion, or an unreviewed replacement. Report
   the exact conflict; let the user preserve it or choose a distinct skill name.
4. For updates, first inspect Git state. Fetch the public upstream and review the
   incoming changes. Fast-forward a clean checkout tracking upstream `main`,
   using its verified remote name. Do not reset, stash, merge into a contribution
   branch, or discard edits to obtain a newer version. Use a separate clean
   checkout when the existing one has local work. Rerun the selected installer;
   it updates only managed copies whose recorded hashes still match local files.
5. Confirm the installed `SKILL.md` and resources match the assembled payload
   and ownership receipt. For local inspection, use
   `python3 scripts/skills.py assemble --skill <name> --output <new-directory>`.
   The output directory must not exist. Check actual
   discovery in the requested agent when that runtime is available. If it does
   not appear, start a fresh session or restart the agent. File installation
   alone is not proof of discovery or successful invocation. Report the source
   commit, destinations, checks performed, and any unverified runtime behavior.

## Improve or add a skill: create a PR

When the user asks to implement an improvement to a published skill or contribute
a new one, carry that exact contribution through a PR. Do not stop with an issue,
an installed local edit, or an unsubmitted patch when PR creation is available
and authorized.
Requests to install or update local copies alone do not authorize a PR.

1. Check `gh auth status` without printing credentials. Read the current public
   contribution rules and inspect existing PRs for the same change. Reuse an
   appropriate existing PR instead of creating duplicates. If authentication or
   push access is unavailable, finish the local patch and validation, then report
   the missing access and exact next action. Never claim a PR exists without its
   returned URL.
2. Work from current public `main` in a clean contribution branch such as
   `codex/improve-<skill-name>` or `codex/add-<skill-name>`. Preserve unrelated
   dirty work using a separate checkout or worktree. Verify the branch name is
   unused before creating it. For users without upstream write access, use their
   own GitHub fork and branch; retain the public repository as upstream.
3. Edit the canonical `skills/<name>/SKILL.md` and only its necessary resources.
   Review the purpose and public suitability before adding a skill. Give it a
   clear lowercase name, a precise trigger description, and instructions that
   work across agents where possible. Keep private preferences, credentials,
   personal paths, and unpublished skill content out of commits and PR bodies.
   Use `references/`, `assets/`, or `scripts/` only when they serve the workflow;
   keep agent-specific adaptations small. Follow the current frontmatter and
   package validation contract in CONTRIBUTING.
4. Run `make check` (or the documented Python equivalents) and any checks
   specific to the changed skill. Test meaningful behavior in an isolated workspace; do not submit paid jobs, messages, or production changes
   merely to test a skill. Reconcile docs and catalog links affected by the change.
5. Review the full diff for scope and private content. Stage only the intended
   paths, commit, and push the contribution branch to the verified upstream or
   the user's fork. Open a PR targeting `Ginylil/context-templates:main`, for
   example with `gh pr create --repo Ginylil/context-templates --base main` and
   an explicit `--head <fork-owner>:<branch>` when using a fork. Supply a concise
   title and a body file containing the purpose, behavior changes, validation,
   and remaining limitations. Do not push to `main`, merge the PR, or alter
   repository settings as part of this contribution workflow.
6. Return the PR URL and distinguish local checks, CI status, and maintainer
   acceptance. In Codex, attach the created PR to the current chat when the host
   provides an artifact-attachment tool. Maintainers decide whether to merge.

## Completion

Discovery returns the available choices and a recommendation relevant to the
user's task. Requests return a verified issue/comment URL or an explicitly unsent
draft, plus a blocker when submission was requested but unavailable. Installation
returns the selected skills, source revision, destinations, and verification.
Contributions return a real PR URL or a concrete access blocker together with
the completed local patch and its validation.
