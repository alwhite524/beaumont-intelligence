"""Archive the supplied November 17 Council packet without changing its contents."""
import gc
import json
import re
import shutil
from pathlib import Path
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[1]
DATE = '2026-11-17'
SOURCE = Path.home() / 'Downloads/Agenda Package - City Council Closed and Regular Session_Nov17_2026.pdf'
BASE = 'https://documents.beaumontintelligence.com/'

def main():
    reader = PdfReader(SOURCE)
    first = reader.pages[0].extract_text() or ''
    if 'CITY COUNCIL' not in first or 'November 17, 2026' not in first:
        raise ValueError('Source does not identify the November 17 Council meeting')
    marks = [(reader.get_destination_page_number(b), b.title) for b in reader.outline if not isinstance(b, list)]
    assert len(reader.pages) == 1786 and len(marks) == 88
    target = ROOT / f'docs/official-documents/{DATE}'
    target.mkdir(parents=True, exist_ok=True)
    packet_key = f'records/agenda-packets/{DATE}/{DATE}-city-council-agenda-package.pdf'
    packet = ROOT / 'docs' / packet_key
    packet.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, packet)
    documents = []
    for i, (start, title) in enumerate(marks):
        end = marks[i+1][0] if i+1 < len(marks) else len(reader.pages)
        assert 0 <= start < end <= len(reader.pages)
        filename = re.sub(r'[^a-z0-9]+', '-', title.removesuffix('.pdf').lower()).strip('-')[:180] + '.pdf'
        path = target / filename
        writer = PdfWriter()
        for page in reader.pages[start:end]:
            writer.add_page(page)
        with path.open('wb') as stream:
            writer.write(stream)
        assert len(PdfReader(path).pages) == end-start
        if i:
            item, label = re.match(r'^([GJ]\.\d+)\.\s*(.*)', title).groups()
            documents.append(dict(item=item, section='Consent' if item.startswith('G.') else 'Action', title=label.removesuffix('.pdf'), packet_page_start=start+1, packet_page_end=end, archiveUrl=BASE+f'official-documents/{DATE}/{filename}', officialUrl='https://pub-beaumont.escribemeetings.com/', sourceBasis='Supplied City agenda package; original individual City URL not independently verified.'))
        print(f'[{i+1}/{len(marks)}] {filename}: pages {start+1}-{end}', flush=True)
        del writer
        gc.collect()
    result = dict(date=DATE, packetPages=len(reader.pages), packetArchiveUrl=BASE+packet_key, agendaArchiveUrl=BASE+f'official-documents/{DATE}/agenda.pdf', sourceFilename=SOURCE.name, documents=documents)
    (ROOT / f'data/council/{DATE}-packet-map.json').write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')

if __name__ == '__main__':
    main()
