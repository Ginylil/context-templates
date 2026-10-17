# Context Templates

- This is the public skill catalog for Codex, Cursor, and Claude Code. GitHub is
  the source of truth. The static website entry is `index.html`, with resources
  under `website/` and an edited public journal under `build-notes/`. Existing
  GitHub Pages hosts static examples; there is no backend, MCP server, or API publisher.
- Keep the website dependency-free and its links relative so project Pages and a
  custom domain both work. Keep raw session material and proof in ignored `dist/`;
  publish only reviewed journal prose. Domain, DNS, and hosting settings need their
  own authorization. `make website-check` is optional rendered browser proof;
  it requires an existing Playwright/browser and a running local preview server.
- Generate `catalog/` pages and `sitemap.xml` with `make website-catalog` from
  canonical skill metadata and `website/templates/`; do not edit those outputs.
  Keep installation guidance on the site, including agent-specific previews and
  Python commands for Windows. `make check` and CI enforce website catalog drift.
  Search Console ownership and sitemap receipts stay private; sitemap submission
  is not proof of indexing. Preserve unrelated DNS records during verification.
- Canonical skills live in `skills/<name>/SKILL.md`. Keep shared instructions
  portable and put substantial supporting content in references, assets, or
  scripts. Agent-specific UI metadata belongs in `agents/`.
- New skill names use `ct-<department>-<expertise>` with a concrete action and
  subject. Dynamic UML skills use `ct-dynamic-uml` and `ct-dynamic-uml-<type>`;
  preserve the existing bootstrap name.
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
- Keep every maintained coding file and packaged script at most 300 physical
  lines, including tests, comments and blanks. Split by responsibility; do not
  compress code to satisfy the limit. Only the eight generated standalone HTML
  examples are exempt; their maintained template, CSS and JavaScript are checked.
  `scripts/check_code_size.py` enforces source limits in `make check` and CI;
  payload assembly independently rejects oversized packaged code.
- `make check` runs source-size and canonical diagram drift checks, catalog
  validation, and isolated installer/package/rendering tests.
  Run `make check` for publishable skill changes; meaningful behavior checks supplement
  metadata checks. Local checks are not CI or proof of discovery in each agent.
- Reconcile README, CONTRIBUTING, and DETAILS with behavior before committing.
  Preserve a focused local commit for skill changes; pushing and merging are separate actions.
- Define a Project's contract and examples live in its complete skill folder.
  Keep its 10-question/2-batch budget in one scope ledger, with negative tests
  and isolated CLI checks under `tests/test_define_project*.py`. Do not copy
  private project definitions or interview histories into the public package.
- Shared Python helpers live once under `shared/lifecycle/` and `shared/dynamic-uml/`.
  Each source skill has a strict v2 `assets/package.json` with a `scripts` list
  of explicit `source` (repository-relative `shared/...`) and `destination`
  (skill-relative `scripts/...`) paths. Include required sibling modules;
  implicit filename maps and duplicate destinations are rejected.
  `assets/contract.json` remains behavioral policy. Never commit assembled script
  copies. `scripts/skills.py` is the CLI; `scripts/skill_tools/` owns the common
  payload, installation and size-limit logic. Never execute selected helpers. Use
  `python3 scripts/skills.py assemble --output <new-directory>` before running
  commands from sparse source skills. Tests use disposable assembled catalogs.
- The interface and manager manifests both select `shared/lifecycle/interface.py`.
  Preserve the interface policy branches in the shared workflow helper.
- `make resources` still regenerates lifecycle guides and synthetic example
  hashes. Do not hand-edit those copies. Every assembled package works independently.
- Public-content checks use `scripts/secret_scan.py`; `make check` and CI reject
  detected credentials and signing files. Keep examples synthetic, runtime evidence
  private, and scan findings redacted. Never treat a heuristic pass as a guarantee.
- Contributor hooks use `.pre-commit-config.yaml` and `make setup-hooks`; they
  inspect staged index blobs with the repository scanner and free Gitleaks CLI.
  Run `make secret-check` for history checks. Keep the separate CI job's Gitleaks
  version and archive checksum in sync; do not replace it with a licensed wrapper,
  weaken findings with broad allowlists, or install hooks during skill installation.
- Keep lifecycle assessments distinct from acceptance: `ready` may mean a
  completed assessment with findings. QA verdicts, candidate identity, human
  staging acceptance, GitHub readbacks and release milestones remain explicit.
- Install through Make or Python from the checkout. Do not reintroduce ZIP
  builds, a generated download catalog or CI skill artifact uploads. Keep
  `assemble` for local inspection and execution; `dist/` stays ignored for local proof.
- Keep `.gitattributes` LF normalization for text and binary handling for PNG
  assets; diagram drift checks and installed payload hashes depend on checkout bytes.
- Dynamic UMLs visual rules and proof requirements live in `DESIGN.md`.
  Shared Python renderer/verifiers are canonical under `shared/dynamic-uml/`;
  HTML shell, CSS/JavaScript fragments, supplied logo, guide and example JSON
  remain under `skills/ct-dynamic-uml/`.
  Regenerate focused-skill resources and HTML review examples with `make examples`; never edit their generated copies manually.
  New diagram types must have a concrete interactive example for template review.

- Store release helpers are canonical under `shared/lifecycle/`, selected by the
  Apple/Android/manager manifests. Use `make resources` to refresh synthetic example
  input hashes; never copy
  private runtime discovery, app/configuration data or credentials into public fixtures.

- Interface correction tests must distinguish confirmed repeated defects, justified
  variants and unanswered corrections. Hold uncertain files unchanged and require
  matched rendered proof; source search alone is not project-wide semantic coverage.

- Prepare Next Session is a standalone utility, outside the lifecycle manager's
  twenty-one-skill graph. Keep its helpers under `shared/lifecycle/handoff*.py`,
  synthetic fixtures in its skill folder, and generated hashes in `make resources`.
  Repository and handoff secret checks share `shared/lifecycle/public_content.py`;
  preserve scanner CLI/index/history behavior when changing that pure module.
