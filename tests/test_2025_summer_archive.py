import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


class SummerArchiveTests(unittest.TestCase):
    def test_source_coverage_and_storage(self):
        reviews = read('data/council/2025-summer-meeting-review.json')
        stored = {d['url'] for d in read('data/document-storage-manifest.json')['documents']}
        pages = items = 0
        urls = set()
        for date, count in [('2025-06-03', 124), ('2025-06-17', 100), ('2025-07-15', 99), ('2025-08-19', 130)]:
            agenda = read(f'data/council/{date}-agenda.json')
            self.assertEqual(len(agenda['documents']), count)
            self.assertTrue(agenda['audit']['officialHtmlAuditComplete'])
            self.assertEqual(agenda['audit']['expectedDocuments'], count)
            self.assertEqual({i['item'] for i in agenda['items']}, set(reviews[date]['items']))
            pages += agenda['packetPages']
            items += len(agenda['items'])
            urls.update([agenda['agendaUrl'], agenda['packetArchiveUrl']])
            for doc in agenda['documents']:
                self.assertTrue(doc['officialUrl'].startswith('https://pub-beaumont.escribemeetings.com/'))
                self.assertLessEqual(doc['packet_page_start'], doc['packet_page_end'])
                self.assertLessEqual(doc['packet_page_end'], agenda['packetPages'])
                urls.add(doc['archiveUrl'])
            transcript = (ROOT / f'docs/transcripts/{date}-city-council-transcript.txt').read_text(encoding='utf-8')
            self.assertIn('adjourn', transcript.lower())
            self.assertRegex(transcript, r'\(\d{2}:\d{2}:\d{2}\)')
        self.assertEqual(pages, 9917)
        self.assertEqual(items, 160)
        self.assertEqual(len(urls), 461)
        self.assertFalse(urls - stored)

    def test_minutes_exceptions_remain_visible(self):
        reviews = read('data/council/2025-summer-meeting-review.json')
        july = reviews['2025-07-15']['items']
        august = reviews['2025-08-19']['items']
        self.assertIn('tabled', july['G.11']['minutesRecord'].lower())
        self.assertIn('3-2', august['J.8']['minutesRecord'])
        self.assertRegex(august['J.4']['minutesRecord'].lower(), r'three|3.year')


if __name__ == '__main__':
    unittest.main()
