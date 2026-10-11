# Implementation details

The public GitHub repository contains canonical `skills/<name>/SKILL.md` folders.
The README links directly to the self-contained bootstrap skill. There is no
MCP/API publisher or website application. Private skills and personal context
belong in a separate private repository.

## Catalog and packages

`scripts/skills.py` uses Python 3.10+ and only the standard library. `list` reads
names and descriptions directly from canonical skills; no separate editable
catalog duplicates them. `check` validates the restricted frontmatter described
in CONTRIBUTING, names, package layout, and absence of symlinks and hidden or
generated files (including Windows junctions/reparse points). It does not execute
skills or certify their instructions.

`build` creates one ZIP per skill and a SHA-256 catalog in `dist/`. It packages
only skill folders and their supporting resources, with stable ordering,
timestamps, and executable flags. These outputs are ignored by Git. CI keeps
builds as artifacts; publishing a GitHub Release is a separate operation.

## Safe installation

`install` targets the user-level paths listed in README. It explicitly installs
requested agents without guessing whether their apps are installed. `--skill`
selects individual catalog entries; without it the current catalog is selected.
`--home` supports isolated tests and `--dry-run` makes no filesystem changes.

The installer preflights every requested skill and target before making changes.
Each target directory holds `.context-templates-install.json`, identifying this
repository and recording content hashes and executable flags for managed copies.
It refuses same-name files, directories, or links without a valid managed record.
For managed copies it rejects edited, added, removed, or executable-bit-changed
files and directory additions/removals. Unchanged copies are left untouched.

Updates stage a complete copy, verify it, recheck the destination, then replace
it while retaining the previous copy until the ownership receipt is written.
Failure writing that receipt restores the previous copy. Errors stop the run;
if an unexpected I/O failure happens after earlier targets completed, those
completed targets remain installed. A subsequent safe rerun resumes. Run only
one installer process per destination at a time.

No unrelated skill is scanned for removal. Skills removed from the source catalog
are not automatically pruned from machines. Keep the ownership receipt: losing
it makes an existing same-name skill an unmanaged conflict. Never change it to
silence a real local-edit conflict. Installed copies are snapshots, so local edits
do not modify the canonical repository and Git changes do not silently alter
installed instructions.

## Contribution and validation boundary

The bootstrap skill distinguishes local updates from upstream improvements.
Only an authorized contribution creates a branch, commit, push, and PR. It uses
GitHub CLI when available, forks for contributors without upstream write access,
checks for duplicate PRs, and leaves merge decisions to maintainers. It carries
no credentials and does not require another skill or connector.

`make check` runs catalog validation and isolated installer/package tests.
`make build` exercises packaging. The read-only GitHub Actions workflow runs
these checks on Linux, macOS, and Windows. Local results, CI, file installation,
agent discovery, invocation, PR submission, and maintainer acceptance are distinct
proof stages. There is no staging environment for this repository.
