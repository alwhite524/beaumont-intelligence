"""Convert rolling YouTube WebVTT captions to timestamped, searchable text."""
import argparse
import html
import re
from pathlib import Path

def convert(source):
    previous = []
    lines = []
    for block in re.split(r'\n\n+', source.replace('\r', '')):
        cue = re.search(r'(?m)^(\d{2}:\d{2}:\d{2})\.\d+ -->[^\n]*\n(.*)', block, re.S)
        if not cue:
            continue
        words = html.unescape(re.sub(r'<[^>]*>', '', cue[2])).split()
        if not words:
            previous = []
            continue
        overlap = 0
        for size in range(min(len(previous), len(words)), 0, -1):
            if previous[-size:] == words[:size]:
                overlap = size
                break
        if words[overlap:]:
            lines.append(f'({cue[1]}) ' + ' '.join(words[overlap:]))
        previous = words
    return '\n'.join(lines) + '\n'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--date', required=True)
    parser.add_argument('--video-id', required=True)
    args = parser.parse_args()
    body = convert(args.input.read_text(encoding='utf-8'))
    header = (f'City of Beaumont City Council - {args.date}\n'
              f'Source: https://www.youtube.com/watch?v={args.video_id}\n'
              'Source type: YouTube automatically generated English captions.\n'
              'Caption wording retained; rolling-caption repetitions removed. Names, numbers and quotations require checking against the recording. This is not official minutes.\n\n')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(header + body, encoding='utf-8', newline='\n')
    print(args.output, len(body.splitlines()), 'caption lines')
