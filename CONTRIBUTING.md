# Contributing

Contribute a focused improvement or new public skill through a pull request to
`Ginylil/context-templates:main`. Use the downloadable
[Context Templates skill](skills/context-templates/SKILL.md) to have your agent
complete that workflow. Requests, bugs, and questions can also be discussed in
GitHub issues. Use
[`ct-product-request-skill-change`](skills/ct-product-request-skill-change/SKILL.md)
to request a new skill, an update to an existing CT skill, or a catalog feature.
It checks for duplicates and supports authorized follow-up comments. Issues and
comments are public; submitting a request does not promise implementation.
Maintainers review PRs before merging.
For an explicitly authorized merge or release, use `ct-devops-release-project`
and the repository's actual publication procedure. Contribution submission alone
does not authorize that next step or local skill installation.

Website changes use the same focused PR workflow. The entry is `index.html`;
`website/` owns its CSS and clipboard enhancement, and `build-notes/` contains
reviewed public prose. Keep private sessions, screenshots of desktop/account
surfaces, traffic analytics and raw command captures out of journal entries.
Use `make website-serve` for local preview and `make website-check` with an
existing Playwright/browser for narrow/wide interaction proof. These checks are
local; domain configuration and publication require separate scoped approval.

The website catalog is generated from each canonical skill's heading and
frontmatter. Edit `website/templates/` for its HTML, then run `make website-catalog`.
Do not hand-edit `catalog/**/*.html` or `sitemap.xml`. `make check` and CI reject
drift, including newly added skills without website pages. The generated website
contains browsing and installation guidance; it is not a downloadable skill package.

## Public suitability and canonical source

Keep one canonical source per skill. A new skill needs a clear user task and a
precise description of when it should apply. Private preferences, experiments,
credentials, personal paths, and customer material belong outside this public
repository. Review provenance and permission before incorporating third-party
content. Do not migrate another library wholesale or remove an original before
its reviewed replacement is installed and verified.

Use `skills/<name>/SKILL.md`, with lowercase hyphenated names matching the folder,
up to 64 characters. Avoid platform-reserved names such as `con`, `nul`, `com1`,
`synced`, and `anthropic-skills`. New skills use
`ct-<department>-<expertise>` with a concrete action and subject, such as
`ct-product-define-project` or `ct-rnd-build-feature`. The Dynamic UML family uses
`ct-dynamic-uml` and `ct-dynamic-uml-<type>`.
Catalog maintenance uses `context-templates` and `ct-context-templates-update`.
The current dependency-free validator deliberately
accepts only these two frontmatter fields, one per line:

```markdown
---
name: useful-skill
description: "Describe the task and the specific request that should activate it."
---
```

Use a single-line JSON-quoted string for descriptions (valid YAML), and a plain
hyphenated name or JSON-quoted name. There are no custom nested metadata blocks.
The Markdown body contains the instructions; keep it concise and grounded in
real commands and capabilities. Add only resources that the workflow uses:

- `references/`: supporting guidance loaded when relevant.
- `assets/`: reusable context or output templates.
- `scripts/`: deterministic helpers with meaningful behavior checks.
- `agents/openai.yaml`: optional Codex UI metadata; keep the main workflow portable.
- `LICENSE` or `LICENSE.md`: third-party attribution/license text when needed.

Top-level per-skill README files, hidden/generated files, links, and arbitrary
resource directories are rejected. The installer does not execute skill scripts.
Bundled resources are context for the task, not permission to broaden it.

Keep maintained coding files and packaged scripts at most 300 physical lines,
including comments and blanks. Split modules by responsibility rather than
compressing code. This includes tests, HTML templates, CSS and JavaScript.
Only the eight generated standalone HTML examples are exempt; their maintained
inputs remain checked. `python scripts/check_code_size.py` checks tracked and
nonignored new source files; Make and CI run it, and package assembly also checks
every delivered coding file before creating output.

## Secret protection

Install the free [Gitleaks CLI](https://github.com/gitleaks/gitleaks#installing)
and [pre-commit](https://pre-commit.com/#install). On macOS:

```sh
brew install gitleaks pre-commit
make setup-hooks
make secret-check
```

Without Make, use `pre-commit install --allow-missing-config`,
`python3 scripts/secret_scan.py --history` and
`gitleaks git --redact --log-opts="--all" .`. On Windows, use `py -3` in place
of `python3`. Gitleaks must be on PATH. Hooks are opt-in for each clone; installing
skills never installs development hooks. Pre-commit preserves existing hooks in
migration mode and refuses a conflicting `core.hooksPath`; do not force replacement.
Git worktrees share hooks. Older branches without this configuration skip the
hooks; branches containing it enforce both checks and fail if Gitleaks is missing.

The commit hook checks changed staged blobs, including ignored files added with
`git add -f`; cleaning an unstaged working copy does not hide a staged secret.
The repository scanner also rejects signing files and public symlinks. The separate
CI job uses a full checkout, the repository history scanner, and a pinned,
checksum-verified Gitleaks CLI, without a Gitleaks Action license or API key.
Catalog, standalone assembly and installer checks wait for this scan to pass.
All scanner output is redacted; never add raw findings to issues or build artifacts.

Repository administrators should keep GitHub secret scanning and push protection
enabled for this public repository. These protections are free for public repositories;
private repositories have different pricing. CI runs after upload, so it supplements
local hooks and GitHub push protection. Neither scanner guarantees absence of secrets.
History checks cover reachable local refs; fetch the branches and tags you intend
to audit first. They do not cover GitHub discussions, logs, external downloads or
unreachable commits. If a real credential was published, revoke or rotate it first,
then coordinate any history rewrite separately. Do not bypass a finding or add a
blanket allowlist to make a check pass.

## Change and validate

1. Inspect current `main` and existing PRs. Use a clean branch and preserve
   unrelated work. Contributors without upstream write access use their own fork.
2. Implement the canonical skill and its necessary resources. Keep agent-specific
   adaptations limited to actual differences. Document prerequisites, authorized
   side effects, failure states, and observable completion when relevant.
3. Run `make check`. Without Make, run:

   ```text
   python scripts/check_code_size.py
   python scripts/dynamic_umls.py --check
   python scripts/ct_lifecycle.py --check
   python scripts/skills.py check
   python scripts/secret_scan.py
   python -m unittest discover -s tests -v
   ```

4. Check meaningful behavior with a realistic request in an isolated workspace.
   For installation, use `--home <temporary-directory>` so testing never changes
   your real agent directories. Metadata validation alone is not behavioral proof.
   Name unavailable agent or OS checks rather than claiming they passed.
5. Reconcile README, DETAILS, and applicable AGENTS instructions with the final
   behavior. Review the diff for private material, stage only intended paths,
   commit, and push your contribution branch.
6. Open or update a PR targeting public `main`. Explain purpose, behavior,
   validation, and limitations. Do not merge it as part of contribution submission.

CI validates and tests standalone assembly and safe installation on Linux,
macOS, and Windows. It does not build or upload skill downloads. Those checks
do not replace actual skill discovery/invocation checks.
No secrets, MCP connection, or API publishing account are needed for this pipeline.

For skills with structured inputs or outputs, bundle their actual validators and
versioned examples. Exercise valid and deliberately invalid artifacts, resumable
state transitions, and the complete CLI from an isolated installed package.
Keep test suites under repository `tests/`, and package fixtures under `assets/`.
Declare what scripts cannot prove; schema validation is not behavioral acceptance.
Define a Project's focused checks run with
`python -m unittest discover -s tests -p 'test_define_project*.py' -v` and are included
in `make check`.

The twenty-one lifecycle entry points select portable helpers from `shared/lifecycle/`
through source-only `assets/package.json` manifests. Each source skill requires a
v2 manifest, including an empty `scripts` list when no shared helper is needed.
Each entry has exactly `source` and `destination`: source paths start at the
repository root (`shared/<family>/<script>.py`); destination paths start at the
skill root (`scripts/<script>.py`). Destinations must be unique. Legacy implicit
filename maps are rejected; installed ownership receipts remain v1.
`assets/contract.json` remains runtime validation policy. See the strict manifest
format in [DETAILS](DETAILS.md#package-composition). Do not commit generated script
copies. Use `scripts/skills.py assemble` for local execution or review.
Declare every required sibling module in the manifest: definition validation and
workflow input/rules live in separate helpers, and imports do not add them automatically.
Run `make resources` after changing canonical guides or synthetic examples; the
remaining generated guides and example hashes are checked byte-for-byte. Focused
packages use `scripts/definition.py`; generated ledger guides adapt the canonical
`scripts/project.py` command to that filename. Do not edit generated guides manually.
Bundled synthetic
examples deliberately show blocked states when no real proof has been supplied.
Tests must also exercise ready paths using disposable source trees and actual
local command capture, while remote provider behavior uses mocked readbacks.
Do not present either as live provider or human-acceptance proof.

Store release checks select `shared/lifecycle/store_release.py` and
`shared/lifecycle/configuration.py` for Apple, Android and the manager during assembly.
The same generator derives both store example input hashes from their synthetic
input JSON; never copy an application digest or hand-edit those generated fields.
Test discovery/configuration and web-wrapper failure paths with disposable files
and real command evidence, keeping actual native/store proof limitations explicit.
Keep examples synthetic and test phase contradictions, candidate identity, scoped authorization,
review exemptions, tester access and separate device proof. Keep signing keys,
keystores, `.p8` files, service-account JSON and credential values outside packages.
The secret scan reports locations/rules without matched values; do not weaken it
with a blanket fixture allowlist. Use constructed inert strings for scanner tests.

Interface correction checks are canonical in
`shared/lifecycle/interface.py`, selected by the interface and manager manifests.
Test repeated occurrences, intentional exceptions, held uncertain files and resumed
real-answer decisions as well as source/capture/viewport coverage. Synthetic PNGs
can test artifact invariants but are not rendered browser proof. Runtime scans,
screenshots and interview data stay private.

## Dynamic UML contributions

Read [DESIGN](DESIGN.md). Change Python helpers in `shared/dynamic-uml/` and
canonical static resources in `skills/ct-dynamic-uml/`, then run `make examples`
to refresh focused static resources and review HTML files. Script manifests
assemble independent packages. The remaining generated static copies are required resources;
the catalog's hidden/generated-file restriction refers to caches and hidden files,
not these tracked synchronized assets. CI and `make check` reject resource drift.
The renderer inlines `styles.css`, `diagram.js` and `controls.js` into
`template.html`, retaining one offline HTML file per generated walkthrough.
Class diagrams instead inline the canonical `assets/class-camera/` fragments
through `shared/dynamic-uml/class_camera.py`. Keep linked-view coverage complete
and each class at twenty relationships or fewer within each view. The remote
`Class camera demo` workflow renders the assembled standalone class skill and
records camera/gesture proof; its builder must not maintain a separate demo viewer.

A diagram addition or visual change needs a concrete offline example and actual
rendered review. With an existing Playwright installation, run
`node scripts/check_dynamic_umls.cjs` (see DESIGN for environment overrides).
Keep screenshots in ignored `dist/`; do not package environment-specific proof,
private repositories or user's generated diagrams as public skill resources.

Flowchart contributions must pass the bundled Python verifier for every nested
view, including the seven-node cap, orthogonal top-down routes and outer side
loops. Add focused rejection cases when changing geometry policy. Preserve the
owner-supplied Ginylil logo and its contexttemplates.com link.

State diagrams share the seven-node and collision rules but may run horizontally
or vertically. Cause labels must sit on arrow segments (`labelOn`), with room
for their text and arrowheads. Run `scripts/validate_state.py` and inspect the
actual rendered label placement before submitting a state diagram change.
