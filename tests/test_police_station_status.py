import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('station', ROOT / 'scripts/build_police_station_status.py')
station = importlib.util.module_from_spec(spec)
spec.loader.exec_module(station)


class StationStatusTests(unittest.TestCase):
    def test_all_police_pages_share_conditional_authority_and_gaps(self):
        for page in station.PAGES:
            text = (ROOT / 'docs' / f'{page}.html').read_text(encoding='utf-8')
            with self.subTest(page=page):
                self.assertEqual(text.count(station.START), 1)
                self.assertIn(station.render(page), text)
                for phrase in ('$5,437,851', '$241,727', 'each phase',
                               'approved October 20 minutes', 'corrected executed agreement',
                               'was excluded', 'transcript-based'):
                    self.assertIn(phrase, station.render(page))

    def test_estimates_and_authority_are_distinct(self):
        self.assertEqual(219752 + 21975, 241727)
        self.assertEqual(88475000 - 8462372, 80012628)
        text = (ROOT / 'docs/police-facilities.html').read_text(encoding='utf-8')
        self.assertIn('Earlier capital-plan snapshot · June 2026', text)
        self.assertIn('$80.0M', text)
        self.assertNotIn('Current capital plan', text)
        for value in ('$88,475,000', '$8,462,372', '$80,012,628'):
            self.assertIn(value, station.render('police-facilities'))
        self.assertIn('$237,752', station.render('police-evidence'))

    def test_rebuild_is_idempotent(self):
        paths = [ROOT / 'docs' / f'{page}.html' for page in station.PAGES]
        before = [p.read_bytes() for p in paths]
        station.main()
        self.assertEqual(before, [p.read_bytes() for p in paths])


if __name__ == '__main__':
    unittest.main()
