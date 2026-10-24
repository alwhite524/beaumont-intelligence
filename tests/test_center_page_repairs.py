"""Guard against truncated center pages and incorrect root-level viewer links."""
import importlib.util
import re
import sys
import unittest
from unittest.mock import patch
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
REPAIRED = ('animal-control-sheltering.html', 'animal-control-municipal-code.html', 'potrero-interchange-history.html')


class Structure(HTMLParser):
    tracked = {'html', 'body', 'main', 'section', 'article', 'div', 'p', 'footer', 'nav', 'ul', 'li'}

    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag in self.tracked:
            self.stack.append(tag)
        if tag == 'a':
            self.links.append(dict(attrs).get('href', ''))

    def handle_endtag(self, tag):
        if tag in self.tracked:
            if not self.stack or self.stack[-1] != tag:
                self.errors.append(f'Unexpected closing {tag}; open stack: {self.stack}')
            else:
                self.stack.pop()


class CenterPageRepairs(unittest.TestCase):
    def test_repaired_documents_have_complete_structure_and_navigation(self):
        for filename in REPAIRED:
            with self.subTest(page=filename):
                text = (DOCS / filename).read_text(encoding='utf-8')
                parser = Structure()
                parser.feed(text)
                self.assertEqual(parser.errors, [])
                self.assertEqual(parser.stack, [])
                self.assertEqual(text.count('</main>'), 1)
                self.assertIn('class="footer"', text)
                self.assertIn('class="page-nav"', text)
                self.assertIn('<script src="app.js"></script>', text)
                for link in parser.links:
                    target = urlsplit(link)
                    if not target.scheme and not target.netloc and target.path:
                        self.assertTrue((DOCS / target.path.lstrip('/')).exists(), link)

    def test_root_pages_do_not_link_to_the_missing_viewer(self):
        checked = 0
        for page in DOCS.glob('*.html'):
            text = page.read_text(encoding='utf-8')
            for href in re.findall(r'href=["\']([^"\']+)["\']', text):
                target = urlsplit(href)
                self.assertNotIn(target.path, ('viewer.html', '/viewer.html'), f'{page.name}: {href}')
                if target.path == 'documents/viewer.html':
                    checked += 1
                    self.assertTrue((DOCS / target.path).is_file())
        self.assertGreater(checked, 69)

    def test_regenerating_findings_keeps_the_minutes_viewer_route(self):
        spec = importlib.util.spec_from_file_location('center_findings', ROOT / 'scripts/build_recent_center_findings.py')
        module = importlib.util.module_from_spec(spec)
        with patch.object(sys, 'path', [str(ROOT / 'scripts'), *sys.path]):
            spec.loader.exec_module(module)
        html = module.render_findings('police-facilities.html')
        parser = Structure()
        parser.feed(html)
        minutes_links = [link for link in parser.links if 'viewer.html' in link]
        self.assertTrue(minutes_links)
        for link in minutes_links:
            self.assertEqual(urlsplit(link).path, 'documents/viewer.html')


if __name__ == '__main__':
    unittest.main()
