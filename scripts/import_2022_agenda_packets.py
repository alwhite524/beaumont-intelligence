"""Import the six supplied January-March 2022 bookmarked Council packets."""
import argparse
import json
import re
import shutil
from pathlib import Path
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[1]
DATES = ['2022-01-04', '2022-01-18', '2022-02-01', '2022-02-15', '2022-03-01', '2022-03-15']
BASE = 'https://documents.beaumontintelligence.com/'

def clean(text):
    return re.sub(r'\s+', ' ', text).strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', choices=DATES + ['2022-04-05'])
    args = parser.parse_args()
    for date in ([args.date] if args.date else DATES):
        token = date[5:7] + '.' + date[8:10]
        source = Path.home() / 'Downloads' / f'Agenda Packet {token}.2022.pdf'
        if date == '2022-04-05':
            source = Path.home() / 'Downloads' / 'CC 04 05 2022.pdf'
        reader = PdfReader(source)
        def walk(entries, depth=1):
            rows = []
            for entry in entries:
                if isinstance(entry, list):
                    rows.extend(walk(entry, depth + 1))
                else:
                    rows.append((depth, entry.title, reader.get_destination_page_number(entry) + 1))
            return rows
        toc = walk(reader.outline)
        parents = [(i, row) for i, row in enumerate(toc) if row[0] == 1 and row[1].startswith('Item ')]
        agenda_end = min(row[2] for _, row in parents) - 1
        agenda_text = '\n'.join(reader.pages[i].extract_text() for i in range(agenda_end))
        agenda_text = re.sub(r'(?m)^\s*\d+\s*$', '', agenda_text)
        regular = agenda_text.split('ANNOUNCEMENTS/ RECOGNITION / PROCLAMATIONS / CORRESPONDENCE', 1)[1]
        sections = [(m.start(), name) for label, name in [
            ('CONSENT CALENDAR', 'Consent'), ('PUBLIC HEARINGS', 'Public Hearing'),
            ('ACTION ITEMS', 'Action'), ('LEGISLATIVE UPDATES AND DISCUSSION', 'Reports')]
            for m in re.finditer(label, regular)]
        starts = []
        expected = 1
        for m in re.finditer(r'(?m)^[ \t]*(\d{1,2})\.[ \t]+([^\n]+)', regular):
            if int(m.group(1)) == expected:
                starts.append((expected, m.start(), m.end(1) + 1))
                expected += 1
        items = []
        for idx, (number, start, body_start) in enumerate(starts):
            end = starts[idx + 1][1] if idx + 1 < len(starts) else len(regular)
            body = regular[body_start:end]
            # Section headings following an item are navigation, not its recommendation.
            body = re.split(r'\n(?:PUBLIC HEARINGS|ACTION ITEMS|LEGISLATIVE UPDATES AND DISCUSSION|CITY MANAGER REPORT|CITY ATTORNEY REPORT|FUTURE AGENDA ITEMS|COUNCIL REPORTS|PUBLIC COMMENT PERIOD)', body)[0]
            title, _, recommendation = body.partition('Recommended Action:')
            section = next((name for pos, name in sorted(sections, reverse=True) if pos < start), 'Presentation')
            items.append({'item': str(number), 'section': section, 'title': clean(title),
                          'recommendation': clean(recommendation), 'outcomeStatus': 'See 2022-04-meeting-review.json' if date == '2022-04-05' else 'See 2022-q1-meeting-review.json'})
        known = {x['item']: x for x in items}
        packet_key = f'records/agenda-packets/{date}/{date}-city-council-agenda-package.pdf'
        packet = ROOT / 'docs' / packet_key
        packet.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, packet)
        dest = ROOT / 'docs/official-documents' / date
        dest.mkdir(parents=True, exist_ok=True)
        def save(start, end, filename):
            assert 1 <= start <= end <= len(reader.pages)
            writer = PdfWriter()
            for page in reader.pages[start-1:end]:
                writer.add_page(page)
            with (dest / filename).open('wb') as stream:
                writer.write(stream)
        save(1, agenda_end, 'agenda.pdf')
        documents = []
        for pidx, (toc_index, parent) in enumerate(parents):
            number = re.match(r'Item (\d+)\.', parent[1]).group(1)
            assert number in known, (date, number)
            limit = parents[pidx + 1][1][2] - 1 if pidx + 1 < len(parents) else len(reader.pages)
            next_index = parents[pidx + 1][0] if pidx + 1 < len(parents) else len(toc)
            children = [(i, row) for i, row in enumerate(toc[toc_index + 1:next_index], toc_index + 1)
                        if row[1] != 'Bottom' and (i+1 == len(toc) or toc[i+1][0] <= row[0])]
            leaves = [row for _, row in children] or [parent]
            assert leaves[0][2] == parent[2], (date, number, 'uncovered first page')
            for j, (_, title, start) in enumerate(leaves):
                end = leaves[j+1][2]-1 if j+1 < len(leaves) else limit
                filename = f'item-{number}-{j+1:02d}.pdf'
                save(start, end, filename)
                documents.append({'item': number, 'section': known[number]['section'], 'title': clean(title),
                                  'itemTitle': known[number]['title'], 'packet_page_start': start,
                                  'packet_page_end': end, 'archiveUrl': BASE + f'official-documents/{date}/{filename}',
                                  'officialUrl': None})
        result = {'date': date, 'sourceFilename': source.name, 'packetPages': len(reader.pages),
                  'packetArchiveUrl': BASE + packet_key, 'agendaUrl': BASE + f'official-documents/{date}/agenda.pdf',
                  'agendaPageCount': agenda_end, 'meetingStatus': 'held',
                  'audit': {'basis': 'Supplied PDF bookmarks; historical City HTML agenda not independently audited',
                            'packetDocuments': len(documents), 'linkedDocuments': len(documents),
                            'officialHtmlAuditComplete': False}, 'items': items, 'documents': documents}
        (ROOT / 'data/council' / f'{date}-agenda.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(date, len(items), 'items;', len(documents), 'supporting documents', flush=True)

if __name__ == '__main__':
    main()
