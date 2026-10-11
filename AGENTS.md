# Context Templates

- This is the public skill catalog for Codex, Cursor, and Claude Code. GitHub is
  the source of truth; there is no website build, MCP server, or API publisher.
- Canonical skills live in `skills/<name>/SKILL.md`. Keep shared instructions
  portable and put substantial supporting content in references, assets, or
  scripts. Agent-specific UI metadata belongs in `agents/`.
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
- Dynamic UMLs visual rules and proof requirements live in `DESIGN.md`.
  Shared renderer, flowchart/state verifiers, template, supplied logo, guide and example JSON are canonical under
  `skills/dynamic-umls/`. Regenerate focused-skill resources and HTML review
  examples with `make examples`; never edit their generated copies manually.
  New diagram types must have a concrete interactive example for template review.
