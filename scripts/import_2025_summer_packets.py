"""Import supplied packets after matching every bookmark to the official HTML agenda."""
import argparse
import json
import re
import shutil
import unicodedata
from pathlib import Path
from urllib.parse import urljoin
from lxml import html
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://documents.beaumontintelligence.com/'
MEETINGS = {
    '2025-06-03': ('Jun03_2025', 'f0fbc3fe-8d21-4382-a457-58dd85cf91ca'),
    '2025-06-17': ('Jun17_2025', '5d62692a-da14-427c-8fef-54899aa4e54c'),
    '2025-07-15': ('Jul15_2025', '38778a76-c481-4fc3-b36e-a0ff6b27102a'),
    '2025-08-19': ('Aug19_2025', 'bd556926-e74d-4440-bee8-97d471eb806c'),
}


def clean(value):
    return re.sub(r'\s+', ' ', value).strip()


def norm(value):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', value).lower())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--meeting', action='append', choices=MEETINGS)
    args = parser.parse_args()
    for day in args.meeting or MEETINGS:
        token, meeting_id = MEETINGS[day]
        source = Path.home() / 'Downloads' / f'Agenda Package - City Council Closed and Regular Session_{token}.pdf'
        reader = PdfReader(source)
        marks = [(reader.get_destination_page_number(x), x.title) for x in reader.outline if not isinstance(x, list)]
        assert marks[0] == (0, 'Agenda')
        official = html.fromstring((ROOT / f'tmp/2025-summer/{day}-official.html').read_text(encoding='utf-8'))
        items, links = [], {}
        for node in official.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," AgendaItem ")]'):
            counters = node.xpath('.//*[@class="AgendaItemCounter"]/text()')
            if not counters or not re.fullmatch(r'[A-Z]\.\d+', counters[0]):
                continue
            number = counters[0]
            title = clean(node.xpath('.//*[@class="AgendaItemTitle"]')[0].text_content())
            recommendation = ' '.join(clean(n.text_content()) for n in node.xpath('.//*[contains(concat(" ",normalize-space(@class)," ")," MotionText ")]'))
            section = {'B':'Closed Session','E':'Presentation','G':'Consent','I':'Public Hearing','J':'Action'}.get(number[0], 'Reports')
            items.append(dict(item=number, section=section, title=title, recommendation=recommendation))
            for anchor in node.xpath('.//a[contains(@href,"DocumentId=")]'):
                key = (number, norm(anchor.text_content()))
                assert key not in links, key
                links[key] = urljoin('https://pub-beaumont.escribemeetings.com/', anchor.get('href'))
        by_item = {i['item']: i for i in items}
        packet_key = f'records/agenda-packets/{day}/{day}-city-council-agenda-package.pdf'
        packet = ROOT / 'docs' / packet_key
        packet.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, packet)
        target = ROOT / 'docs/official-documents' / day
        target.mkdir(parents=True, exist_ok=True)
        documents, matched, counts = [], set(), {}
        for index, (start, title) in enumerate(marks):
            end = marks[index+1][0] if index+1 < len(marks) else len(reader.pages)
            assert start < end
            if index == 0:
                name = 'agenda.pdf'
            else:
                match = re.fullmatch(r'([A-Z]\.\d+)\.\s*(.*)', title)
                assert match, title
                number, title = match.groups()
                key = (number, norm(title))
                assert key in links and key not in matched, key
                matched.add(key)
                counts[number] = counts.get(number, 0) + 1
                name = f'item-{number.lower().replace(".", "-")}-{counts[number]:02d}.pdf'
                documents.append(dict(item=number,section=by_item[number]['section'],title=title.removesuffix('.pdf'),itemTitle=by_item[number]['title'],packet_page_start=start+1,packet_page_end=end,archiveUrl=BASE+f'official-documents/{day}/{name}',officialUrl=links[key]))
            writer = PdfWriter()
            for page in reader.pages[start:end]:
                writer.add_page(page)
            with (target/name).open('wb') as stream:
                writer.write(stream)
        assert matched == links.keys(), links.keys() - matched
        result = dict(date=day,sourceFilename=source.name,packetPages=len(reader.pages),agendaPageCount=marks[1][0],packetArchiveUrl=BASE+packet_key,agendaUrl=BASE+f'official-documents/{day}/agenda.pdf',officialAgendaUrl=f'https://pub-beaumont.escribemeetings.com/Meeting.aspx?Id={meeting_id}&Agenda=Agenda&lang=English',meetingStatus='held',audit=dict(checkedOn='2026-10-10',expectedDocuments=len(links),linkedDocuments=len(documents),officialHtmlAuditComplete=True,basis='Every official HTML attachment matched by agenda item and normalized filename to the supplied packet bookmarks. Original City URLs retained.'),items=items,documents=documents)
        (ROOT/f'data/council/{day}-agenda.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(day,len(items),'items;',len(documents),'verified supporting documents',flush=True)


if __name__ == '__main__':
    main()
