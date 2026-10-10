import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('captions', Path(__file__).resolve().parents[1] / 'scripts/import_youtube_vtt.py')
captions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(captions)

class CaptionTests(unittest.TestCase):
    def test_spacer_line_preserves_first_cue(self):
        self.assertEqual(captions.convert('WEBVTT\n\n00:02:04.079 --> 00:02:28.750\n \ncan<00:02:04.240><c> I</c>\n\n'), '(00:02:04) can I\n')

    def test_rolling_overlap_is_removed(self):
        source = '00:00:01.000 --> 00:00:02.000\nfirst sentence\n\n00:00:02.000 --> 00:00:03.000\nfirst sentence\nnext sentence\n\n'
        self.assertEqual(captions.convert(source), '(00:00:01) first sentence\n(00:00:02) next sentence\n')

    def test_silence_allows_repeated_words(self):
        source = '00:00:01.000 --> 00:00:02.000\nyes\n\n00:00:02.000 --> 00:00:03.000\n \n\n00:00:03.000 --> 00:00:04.000\nyes\n\n'
        self.assertEqual(captions.convert(source), '(00:00:01) yes\n(00:00:03) yes\n')

if __name__ == '__main__':
    unittest.main()
