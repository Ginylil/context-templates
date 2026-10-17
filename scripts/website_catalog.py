#!/usr/bin/env python3
"""Render the public website catalog from canonical skill metadata."""
from __future__ import annotations

import argparse
from html import escape
from pathlib import Path
import re
import sys

from skill_tools.common import ROOT, metadata
from skill_tools.packages import catalog

SITE = "https://contexttemplates.com"
TEMPLATE = ROOT / "website/templates"
AGENTS = {"codex": "Codex", "cursor": "Cursor", "claude": "Claude Code"}
CATEGORIES = {
    "product": "Product", "rnd": "Development", "design": "Design",
    "qa": "Testing", "security": "Security", "devops": "Operations & releases",
    "dynamic": "Dynamic UMLs", "context": "Getting started", "marketing": "Marketing",
}


def render(template: str, **values: str) -> str:
    text = (TEMPLATE / template).read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    if re.search(r"\{\{[a-z_]+\}\}", text):
        raise ValueError(f"Unfilled website template: {template}")
    return text


def skills(root: Path) -> list[dict[str, str]]:
    result = []
    for folder in catalog(root).values():
        item = metadata(folder)
        heading = re.search(r"^# (.+)$", (folder / "SKILL.md").read_text(encoding="utf-8"), re.M)
        if not heading:
            raise ValueError(f"Missing title: {folder}")
        item["title"] = heading[1]
        key = "context" if item["name"] == "context-templates" else item["name"].split("-")[1]
        item["category"] = CATEGORIES.get(key, "Other skills")
        # The first sentence is the canonical concise explanation; the detail
        # page preserves the complete description, including use boundaries.
        item["short"] = re.split(r"(?<=\.)\s", item["description"], maxsplit=1)[0]
        result.append(item)
    return result


def codebox(identifier: str, label: str, command: str) -> str:
    return (
        '<div class="command-box">\n'
        f'<div class="command-toolbar"><span>{escape(label)}</span>'
        f'<button hidden type="button" data-copy="{identifier}" '
        f'aria-label="Copy {escape(label)}">Copy</button></div>\n'
        f'<pre id="{identifier}" tabindex="0">{escape(command)}</pre>\n'
        '<p class="command-status" role="status">Select and copy the text, or use the Copy button.</p>\n'
        '</div>'
    )


def installation(name: str) -> str:
    panels = []
    for agent, label in AGENTS.items():
        python = f"python3 scripts/skills.py install --agent {agent} --skill {name}"
        panels.append(
            f'<section data-agent="{agent}" aria-label="Install for {label}">\n'
            f'<h3>{label}</h3>\n'
            + codebox(f"preview-{agent}", f"{label} preview", python + " --dry-run") + "\n"
            + codebox(f"install-{agent}", f"{label} installation", python) + "\n"
            + '<details class="make-alternative"><summary>Using Make instead?</summary>\n'
            + codebox(f"make-{agent}", f"{label} Make commands",
                      f"make install-{agent} SKILL={name} INSTALL_ARGS=--dry-run\n"
                      f"make install-{agent} SKILL={name}") + "\n</details>\n</section>"
        )
    return "\n".join(panels)


def pages(root: Path = ROOT) -> dict[Path, str]:
    entries = skills(root)
    cards = []
    outputs = {}
    for item in entries:
        safe = {key: escape(value) for key, value in item.items()}
        cards.append(render("card.html", **safe))
        example = ""
        if item["name"].startswith("ct-dynamic-uml"):
            kind = item["name"].removeprefix("ct-dynamic-uml").lstrip("-") or "index"
            example = (f'<a class="text-link" href="../../examples/dynamic-umls/{kind}.html">'
                       'Try the interactive example <span aria-hidden="true">→</span></a>')
        outputs[Path("catalog") / item["name"] / "index.html"] = render(
            "skill.html", **safe, installation=installation(item["name"]), example=example,
            clone=codebox("clone", "Repository setup",
                          "git clone https://github.com/Ginylil/context-templates.git\ncd context-templates"),
        )
    options = "\n".join(f'<option>{escape(category)}</option>'
                        for category in sorted({item["category"] for item in entries}))
    outputs[Path("catalog/index.html")] = render(
        "catalog.html", cards="\n".join(cards), options=options, count=str(len(entries)),
    )
    urls = ["/", "/catalog/", "/build-notes/"]
    urls += [f'/catalog/{item["name"]}/' for item in entries]
    urls += [f"/examples/dynamic-umls/{p.name}"
             for p in sorted((root / "examples/dynamic-umls").glob("*.html"))]
    outputs[Path("sitemap.xml")] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(f"  <url><loc>{SITE}{escape(url)}</loc></url>" for url in urls)
        + "\n</urlset>\n"
    )
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail on stale generated pages")
    args = parser.parse_args()
    outputs = pages()
    expected = {ROOT / path for path in outputs}
    stale = [path for path in (ROOT / "catalog").rglob("*.html") if path not in expected]
    # Do not silently delete removed skill pages or any unrecognized content.
    if stale:
        print("Unexpected catalog pages; reconcile explicitly: " + ", ".join(str(p) for p in stale))
        return 1
    drift = []
    for relative, content in outputs.items():
        target = ROOT / relative
        if args.check:
            if not target.is_file() or target.read_bytes() != content.encode("utf-8"):
                drift.append(str(relative))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content.encode("utf-8"))
    if drift:
        print("Website catalog drift; run make website-catalog: " + ", ".join(drift))
        return 1
    print(f"{'Checked' if args.check else 'Rendered'} {len(outputs)} website files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
