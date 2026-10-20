"""Public navigation must bypass a previously cached bare-domain redirect."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://contexttemplates.com/"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.anchors = []
        self.canonical = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "href" in attrs:
            self.anchors.append(attrs["href"])
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical.append(attrs.get("href"))


def cached_home(url):
    """Fragments do not distinguish requests; a new path or query does."""
    parts = urlsplit(url)
    return (parts.scheme in ("http", "https")
            and parts.hostname == "contexttemplates.com"
            and parts.path in ("", "/") and not parts.query)


class HomeNavigationTests(unittest.TestCase):
    def test_public_links_avoid_the_cached_home_request(self):
        pages = [ROOT / "index.html", ROOT / "build-notes/index.html"]
        pages += sorted((ROOT / "catalog").rglob("*.html"))
        pages += sorted((ROOT / "examples/dynamic-umls").glob("*.html"))
        home_links = 0
        for page in pages:
            with self.subTest(page=page.relative_to(ROOT)):
                parsed = Links()
                parsed.feed(page.read_text(encoding="utf-8"))
                base = urljoin(ORIGIN, page.relative_to(ROOT).as_posix())
                for href in parsed.anchors:
                    resolved = urljoin(base, href)
                    self.assertFalse(cached_home(resolved), f"Cached redirect URL: {href}")
                    if urlsplit(resolved)._replace(fragment="").geturl() == ORIGIN + "index.html":
                        home_links += 1
        self.assertGreater(home_links, len(pages))
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        urls = re.findall(r"\[[^\]]+\]\((https?://[^)]+)\)", readme)
        self.assertTrue(any(url == ORIGIN + "index.html" for url in urls))
        self.assertFalse(any(cached_home(url) for url in urls))

    def test_home_canonical_stays_at_the_existing_url(self):
        parsed = Links()
        parsed.feed((ROOT / "index.html").read_text(encoding="utf-8"))
        self.assertEqual(parsed.canonical, [ORIGIN])


if __name__ == "__main__":
    unittest.main()
