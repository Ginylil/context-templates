---
name: ct-context-templates-update
description: "Update already installed Context Templates skills for the current agent from the public GitHub source behind contexttemplates.com. Use for ct-context-templates-update or explicit requests to refresh installed CT skills; preserve local edits and avoid installing unselected catalog entries."
---

# Update installed Context Templates skills

This is the update-only entrypoint to the
[`context-templates` bootstrap](https://github.com/Ginylil/context-templates/blob/main/skills/context-templates/SKILL.md).
Reuse its **Discover, install, or update** workflow and supported installer. Read
the bootstrap from a verified catalog checkout or its public source; it need not
already be installed. The website presents the catalog; the canonical update
source is `Ginylil/context-templates` on GitHub, not scraped website HTML.

An instruction to run this skill authorizes the requested local update. A question
about whether updates are available, or a preview-only request, authorizes only
inspection and a dry run. Do not open issues or PRs, publish, schedule updates,
remove skills, or install missing catalog entries as part of an ordinary refresh.

## Select the installed set

Infer the current agent and user-level destination; honor an explicit target or
named subset. Read the existing `.context-templates-install.json` ownership
receipt without editing it. Intersect its managed names with the current public
catalog and folders that still exist in that target. Include the bootstrap and
this updater when managed and present in the current catalog. Preserve removed
catalog entries, unmanaged folders and skills the user has removed locally.
If the selection is empty, report that nothing managed is installed and stop;
an empty installer selection would install the entire catalog.

Inspect checkout identity and dirty state, fetch upstream, review incoming
changes, and use current public `main` as the source. Follow the bootstrap's
clean-checkout rules; do not reset or fast-forward a contribution branch to get
updates. An existing clean main checkout or separate clean checkout is sufficient.

## Preview, update and verify

Pass the selected names explicitly to the Python installer with repeated
`--skill <name>` arguments, using the requested agent and a dry run first. On
Windows use the available `py -3` or `python` interpreter. For example, replace
the placeholder with an actually installed managed name:

```text
python3 scripts/skills.py install --agent codex --skill <installed-name> --dry-run
python3 scripts/skills.py install --agent codex --skill <installed-name>
```

Preview all requested targets before any installation. Do not omit the selection
unless it equals the explicitly requested full catalog: omission installs every
current catalog entry. No-op updates should report `unchanged`.

Let the installer reject unmanaged conflicts and edited installed copies. Report
the exact paths; never bypass a conflict by changing the receipt, force replacing,
or deleting the installation. Distinguish generated Python bytecode residue from
authored edits. Preserve any residue outside the installed tree before a scoped,
authorized reconciliation, and recheck that all remaining files match the receipt.
If unresolved conflicts prevent the update, retain the completed preview and
report the smallest next action rather than claiming an update succeeded.

Use the normal installer without executing selected packaged scripts. Compare
installed files and the ownership receipt with the assembled source payload,
and confirm a repeat installation is unchanged. Report the source revision,
target, updated/unchanged skills, preserved conflicts and any excluded entries.
File verification does not prove discovery or invocation in the agent; check
discovery when available and name any remaining runtime gap.
