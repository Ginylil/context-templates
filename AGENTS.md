# Context Templates

- This is the public skill catalog for Codex, Cursor, and Claude Code. GitHub is
  the source of truth. Existing GitHub Pages hosting mirrors static examples;
  there is no separate website application, MCP server, or API publisher.
- Canonical skills live in `skills/<name>/SKILL.md`. Keep shared instructions
  portable and put substantial supporting content in references, assets, or
  scripts. Agent-specific UI metadata belongs in `agents/`.
- New skill names use `ct-<department>-<expertise>` with a concrete action and
  subject. Preserve existing bootstrap and Dynamic UML names.
- Only reviewed public content belongs here. Personal preferences and private
  experiments belong in a separate private repository. Do not migrate from
  another skill library in bulk or retire an original before verifying its replacement.
- Skill contributions use branches and PRs targeting `main`. Preserve unrelated
  work; do not merge, publish a release, or alter repository settings without scope.
- Keep `make install-codex`, `make install-cursor`, `make install-claude`, and
  aggregate `make install` as the supported installation interface. The Python
  equivalents must work without Make on Windows.
- Installer invariants: preflight requested targets, refuse unmanaged conflicts
  and locally edited installed copies, retain unrelated skills and removed catalog
  entries, and never execute packaged scripts during installation. Do not add force
  replacement or automatic pruning.
- `make check` runs canonical diagram drift checks, catalog validation, and
  isolated installer/package/rendering tests.
  `make build` generates skill ZIPs and a checksummed JSON catalog in `dist/`.
  Run both for publishable skill changes; meaningful behavior checks supplement
  metadata checks. Local checks are not CI or proof of discovery in each agent.
- Reconcile README, CONTRIBUTING, and DETAILS with behavior before committing.
  Preserve a focused local commit for skill changes; pushing and merging are separate actions.
- Define a Project's contract and examples live in its complete skill folder.
  Keep its 10-question/2-batch budget in one scope ledger, with negative tests
  and isolated CLI checks under `tests/test_define_project.py`. Do not copy
  private project definitions or interview histories into the public package.
- Lifecycle support has canonical sources: Define a Project owns
  `scripts/project.py` and its definition contract; Manage a Project owns
  `scripts/workflow.py`; Plan Development owns `scripts/plan.py` and its contract.
  Run `make resources` after changing them. Never hand-edit generated copies;
  `make check` and `make build` reject drift. Every package works independently.
- Keep lifecycle assessments distinct from acceptance: `ready` may mean a
  completed assessment with findings. QA verdicts, candidate identity, human
  staging acceptance, GitHub readbacks and release milestones remain explicit.
- Keep `.gitattributes` LF normalization for text and binary handling for PNG/ZIP
  assets; diagram drift checks and package hashes depend on checkout byte consistency.
- Dynamic UMLs visual rules and proof requirements live in `DESIGN.md`.
  Shared renderer, flowchart/state verifiers, template, supplied logo, guide and example JSON are canonical under
  `skills/dynamic-umls/`. Regenerate focused-skill resources and HTML review
  examples with `make examples`; never edit their generated copies manually.
  New diagram types must have a concrete interactive example for template review.
