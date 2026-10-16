"""Split the supplied bookmarked packet; retain an auditable page-range map."""
import json
import re
import shutil
from pathlib import Path
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path.home() / 'Downloads/Agenda Package - City Council Closed and Regular Session_Oct20_2026.pdf'
TARGET = ROOT / 'docs/official-documents/2026-10-20'
PACKET_KEY = 'records/agenda-packets/2026-10-20/2026-10-20-city-council-agenda-package.pdf'
reader = PdfReader(SOURCE)
marks = [(reader.get_destination_page_number(x), x.title) for x in reader.outline if not isinstance(x, list)]
assert len(reader.pages) == 706 and len(marks) == 79
agenda = json.loads((ROOT / 'data/council/2026-10-20-agenda.json').read_text(encoding='utf-8'))
TARGET.mkdir(parents=True, exist_ok=True)
packet = ROOT / 'docs' / PACKET_KEY
packet.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(SOURCE, packet)
documents = []
for index, (start, title) in enumerate(marks):
    end = marks[index+1][0] if index+1 < len(marks) else len(reader.pages)
    assert 0 <= start < end <= len(reader.pages)
    filename = re.sub(r'[^a-z0-9]+', '-', title.removesuffix('.pdf').lower()).strip('-')[:180]+'.pdf'
    writer = PdfWriter()
    for page in reader.pages[start:end]:
        writer.add_page(page)
    with (TARGET / filename).open('wb') as stream:
        writer.write(stream)
    check = PdfReader(TARGET / filename)
    assert len(check.pages) == end-start
    if index:
        item, label = re.match(r'^([GIJ]\.\d+)\.\s*(.*)', title).groups()
        original = [d for d in agenda['documents'] if d['item']==item]
        offset = sum(d['item']==item for d in documents)
        record = dict(original[offset], title=label.removesuffix('.pdf'), packet_page_start=start+1, packet_page_end=end, archiveUrl=f'https://documents.beaumontintelligence.com/official-documents/2026-10-20/{filename}')
        documents.append(record)
assert len(documents)==78
result = dict(packetPages=706, packetArchiveUrl='https://documents.beaumontintelligence.com/'+PACKET_KEY, documents=documents)
(ROOT / 'data/council/2026-10-20-packet-map.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('Verified 706 pages: 5-page agenda and 78 supporting documents; full packet retained.')
