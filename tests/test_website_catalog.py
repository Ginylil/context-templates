"""Public pages must stay complete, safe to render and usable with the real CLI."""
from html.parser import HTMLParser
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("website_catalog", ROOT / "scripts/website_catalog.py")
website = importlib.util.module_from_spec(spec)
spec.loader.exec_module(website)


class Commands(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.current = None
        self.commands = {}

    def handle_starttag(self, tag, attrs):
        if tag == "pre":
            self.current = dict(attrs).get("id")
            self.commands[self.current] = ""

    def handle_endtag(self, tag):
        if tag == "pre":
            self.current = None

    def handle_data(self, data):
        if self.current:
            self.commands[self.current] += data


class WebsiteCatalogTests(unittest.TestCase):
    def test_every_skill_has_a_page_and_matching_installer_arguments(self):
        output = website.pages()
        skills = website.skills(ROOT)
        sitemap = ET.fromstring(output[Path("sitemap.xml")])
        urls = [node.text for node in sitemap.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        self.assertEqual(len(urls), len(set(urls)))
        for skill in skills:
            name = skill["name"]
            html = output[Path("catalog") / name / "index.html"]
            self.assertIn(f"https://contexttemplates.com/catalog/{name}/", urls)
            parsed = Commands()
            parsed.feed(html)
            for agent in ["codex", "cursor", "claude"]:
                expected = f"python3 scripts/skills.py install --agent {agent} --skill {name}"
                self.assertEqual(parsed.commands[f"install-{agent}"], expected)
                self.assertEqual(parsed.commands[f"preview-{agent}"], expected + " --dry-run")
        self.assertEqual(len(skills), len(list((ROOT / "skills").glob("*/SKILL.md"))))

    def test_published_commands_preview_and_install_in_an_isolated_home(self):
        output = website.pages()[Path("catalog/ct-design-build-interface/index.html")]
        parsed = Commands()
        parsed.feed(output)
        for agent, folder in [("codex", ".agents"), ("cursor", ".cursor"), ("claude", ".claude")]:
            with tempfile.TemporaryDirectory() as temporary:
                home = Path(temporary)
                for phase in ["preview", "install"]:
                    args = parsed.commands[f"{phase}-{agent}"].split()[1:]
                    result = subprocess.run([sys.executable, *args, "--home", str(home)],
                                            cwd=ROOT, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    target = home / folder / "skills/ct-design-build-interface/SKILL.md"
                    self.assertEqual(target.is_file(), phase == "install")

    def test_clipboard_text_is_html_escaped(self):
        value = website.codebox("sample", "A < B", '<script>alert("x")</script>')
        self.assertNotIn("<script>", value)
        parsed = Commands()
        parsed.feed(value)
        self.assertEqual(parsed.commands["sample"], '<script>alert("x")</script>')


if __name__ == "__main__":
    unittest.main()
