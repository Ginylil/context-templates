# Contributing

Contribute a focused improvement or new public skill through a pull request to
`Ginylil/context-templates:main`. Use the downloadable
[Context Templates skill](skills/context-templates/SKILL.md) to have your agent
complete that workflow. Requests, bugs, and questions can also be discussed in
GitHub issues. Maintainers review PRs before merging.

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
`ct-product-define-project` or `ct-rnd-build-feature`. The Dynamic UML family uses `ct-dynamic-uml` and `ct-dynamic-uml-<type>`;
only the bootstrap retains its existing name. The current dependency-free validator deliberately
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

## Change and validate

1. Inspect current `main` and existing PRs. Use a clean branch and preserve
   unrelated work. Contributors without upstream write access use their own fork.
2. Implement the canonical skill and its necessary resources. Keep agent-specific
   adaptations limited to actual differences. Document prerequisites, authorized
   side effects, failure states, and observable completion when relevant.
3. Run `make check` and `make build`. Without Make, run:

   ```text
   python scripts/dynamic_umls.py --check
   python scripts/ct_lifecycle.py --check
   python scripts/skills.py check
   python -m unittest discover -s tests -v
   python scripts/skills.py build
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

CI validates and tests on Linux, macOS, and Windows and builds downloadable skill
archives. Those checks do not replace actual skill discovery/invocation checks.
No secrets, MCP connection, or API publishing account are needed for this pipeline.

For skills with structured inputs or outputs, bundle their actual validators and
versioned examples. Exercise valid and deliberately invalid artifacts, resumable
state transitions, and the complete CLI from an isolated installed package.
Keep test suites under repository `tests/`, and package fixtures under `assets/`.
Declare what scripts cannot prove; schema validation is not behavioral acceptance.
Define a Project's focused checks run with
`python -m unittest discover -s tests -p test_define_project.py -v` and are included
in `make check`.

The eighteen lifecycle entry points share portable support through synchronized
copies. Canonical sources are under Define a Project (definition validation),
Manage a Project (domain validation and explicit command capture), and Plan
Development (task graph and tracking validation). Run `make resources` after a
canonical change, or `python scripts/ct_lifecycle.py` without Make. The generated
files are required standalone resources; they are included in packages and
checked byte-for-byte. Do not edit their copies manually. Bundled synthetic
examples deliberately show blocked states when no real proof has been supplied.
Tests must also exercise ready paths using disposable source trees and actual
local command capture, while remote provider behavior uses mocked readbacks.
Do not present either as live provider or human-acceptance proof.

## Dynamic UML contributions

Read [DESIGN](DESIGN.md). Change shared resources only in
`skills/ct-dynamic-uml/`, then run `make examples` to refresh the focused packages
and review HTML files. The generated copies are required standalone resources;
the catalog's hidden/generated-file restriction refers to caches and hidden files,
not these tracked synchronized assets. CI and `make check` reject resource drift.

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
