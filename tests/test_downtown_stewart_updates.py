import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('updates', ROOT / 'scripts/build_downtown_stewart_updates.py')
updates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updates)


class RecentCenterUpdatesTests(unittest.TestCase):
    def test_all_core_pages_have_dated_current_records(self):
        records = updates.load_records()
        for slug in updates.DOWNTOWN + updates.STEWART:
            page = (ROOT / 'docs' / (slug + '.html')).read_text(encoding='utf-8')
            with self.subTest(page=slug):
                self.assertEqual(page.count(updates.START), 1)
                self.assertEqual(page.count('id="current-actions"'), 1)
                self.assertIn('Reviewed October 24, 2026', page)
                if slug in updates.STEWART:
                    self.assertIn('not a direct award', page)
                    self.assertIn('does not expressly identify the phase or package', page)
                    self.assertIn('supplied', page.lower())
                elif not slug.endswith('-business'):
                    self.assertIn(next(r for r in records if r['id'] == 'phase-i-design')['summary'], page)
                    self.assertIn('approved October 20 minutes not collected', page)

    def test_no_stale_business_totals_or_current_status(self):
        for slug in updates.DOWNTOWN:
            page = (ROOT / 'docs' / (slug + '.html')).read_text(encoding='utf-8')
            self.assertNotIn('$125,000', page, slug)
            self.assertNotIn('three verified 2026', page.lower(), slug)
        main = (ROOT / 'docs/downtown-revitalization.html').read_text(encoding='utf-8')
        self.assertNotIn('The adopted vision remains, but its first', main)
        self.assertNotIn('does not establish a replacement design contract', main)
        funding = (ROOT / 'docs/downtown-revitalization-funding.html').read_text(encoding='utf-8')
        for amount in ('$15,450', '$53,400', '$68,850', '$2–3 million', '$150,000'):
            self.assertIn(amount, funding)
        self.assertIn('Earlier broader construction estimate', funding)

    def test_evidence_catalogs_preserve_source_types_and_scope(self):
        catalog = json.loads((ROOT / 'data/center-recent-actions.json').read_text(encoding='utf-8'))['records']
        self.assertEqual(len(catalog), 4)
        self.assertEqual(15450 + 53400, 68850)
        self.assertEqual(round(67462.16 + 5147.82 + 47390.02, 2), 120000)
        for center in ('downtown-revitalization', 'stewart-park'):
            page = (ROOT / 'docs' / (center + '-evidence.html')).read_text(encoding='utf-8')
            for record in catalog:
                if record['center'] == center:
                    for doc in record.get('documents', []):
                        self.assertIn(doc['url'], page)
        legacy = json.loads((ROOT / 'data/stewart-park/source-catalog.json').read_text(encoding='utf-8'))
        forecast = next(r for r in legacy if r['archive_code'] == 'SP-FORECAST-2026-1020')
        self.assertIn('not a Council approval', forecast['summary'])
        self.assertIn('captions', forecast['type'])

    def test_build_is_idempotent_and_search_matches_pages(self):
        paths = [ROOT / 'docs' / (p + '.html') for p in updates.DOWNTOWN + updates.STEWART]
        paths += [ROOT / p for p in ['data/center-recent-actions.json', 'docs/search-index.js',
                                    'docs/data.js', 'data/stewart-park/source-catalog.json',
                                    'data/stewart-park/source-catalog.csv']]
        before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
        updates.main()
        self.assertEqual(before, [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths])
        prefix = 'window.BI_SEARCH_INDEX = '
        raw = (ROOT / 'docs/search-index.js').read_text(encoding='utf-8')
        entries = json.loads(raw[len(prefix):].strip().removesuffix(';'))
        entries = [r for group in entries for r in group.get('value', [group])]
        for slug in updates.DOWNTOWN + updates.STEWART:
            record = next(r for r in entries if r['url'] == slug + '.html')
            self.assertIn('Recent actions', record['text'])


if __name__ == '__main__':
    unittest.main()
