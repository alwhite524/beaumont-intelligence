"""Check packet coverage, archived links, and historical item identity."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class AgendaArchiveTests(unittest.TestCase):
    def test_all_packet_pages_are_accounted_for(self):
        manifest = json.loads((ROOT/'data/document-storage-manifest.json').read_text(encoding='utf-8'))
        archived = {d['url'] for d in manifest['documents']}
        total = 0
        for path in sorted((ROOT/'data/council').glob('2022-0[1234]-*-agenda.json')):
            data = json.loads(path.read_text(encoding='utf-8'))
            self.assertIn(data['packetArchiveUrl'], archived)
            self.assertIn(data['agendaUrl'], archived)
            next_page = data['agendaPageCount'] + 1
            for document in data['documents']:
                self.assertEqual(document['packet_page_start'], next_page)
                self.assertGreaterEqual(document['packet_page_end'], next_page)
                self.assertIn(document['archiveUrl'], archived)
                next_page = document['packet_page_end'] + 1
            self.assertEqual(next_page, data['packetPages'] + 1)
            self.assertEqual(data['audit']['linkedDocuments'], len(data['documents']))
            total += len(data['documents'])
        self.assertEqual(total, 308)

    def test_march_reordered_items_keep_agenda_identity(self):
        data = json.loads((ROOT/'data/council/2022-q1-meeting-review.json').read_text(encoding='utf-8'))
        self.assertIn('receive and file presentation', data['2022-03-15']['items']['11']['minutesRecord'])
        self.assertIn('traffic study', data['2022-03-15']['items']['12']['minutesRecord'])
        self.assertIn('City Treasurer', data['2022-03-01']['items']['15']['minutesRecord'])
        self.assertLess(data['2022-03-15']['items']['12']['timestampSeconds'], data['2022-03-15']['items']['11']['timestampSeconds'])

    def test_april_outcome_and_source_limits(self):
        data = json.loads((ROOT/'data/council/2022-04-meeting-review.json').read_text(encoding='utf-8'))['2022-04-05']
        self.assertIn('4-0', data['items']['6']['minutesRecord'])
        self.assertIn('$647,971', data['items']['6']['minutesRecord'])
        self.assertIn('inconsistent', data['items']['12']['minutesRecord'])
        for day in ['2022-03-15', '2022-04-05']:
            transcript = (ROOT/f'docs/transcripts/{day}-city-council-transcript.txt').read_text(encoding='utf-8')
            self.assertIn('automatically generated', transcript)
            self.assertIn('adjourn', transcript[-1200:])

    def test_video_date_correction_is_documented(self):
        videos = json.loads((ROOT/'data/council/video-links.json').read_text(encoding='utf-8'))['videos']
        video = next(v for v in videos if v['url'].endswith('KqzikDSwHGw'))
        self.assertEqual(video['date'], '2022-02-01')
        self.assertIn('February 2', video['dateNote'])

if __name__ == '__main__':
    unittest.main()
