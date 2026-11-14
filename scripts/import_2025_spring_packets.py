"""Match the four supplied spring Council packets to their official HTML agendas."""
import argparse
import gc
import hashlib
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urljoin
from lxml import html
from pypdf import PdfReader, PdfWriter
from import_2025_summer_packets import clean, norm

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://documents.beaumontintelligence.com/'
MEETINGS = {
    '2025-03-04': ('Mar04_2025', '30507ac7-6fbb-4a7d-8173-433bb1bdf809'),
    '2025-03-18': ('Mar18_2025', '20c45b2c-9ff8-4b6c-8648-b2f400d042a5'),
    '2025-04-01': ('Apr01_2025', 'bc2c09b2-6d94-4b8e-9d56-bbf9b1f0f12c'),
    '2025-04-15': ('Apr15_2025', 'cfca3c13-895f-4b4b-96ef-8eddf6efed21'),
}

def inventory(day, meetings=None, cache_directory='2025-spring'):
    meetings=MEETINGS if meetings is None else meetings
    token, meeting_id = meetings[day]
    source = Path.home()/'Downloads'/f'Agenda Package - City Council Closed and Regular Session_{token}.pdf'
    reader = PdfReader(source)
    first = reader.pages[0].extract_text() or ''
    from datetime import date
    expected = date.fromisoformat(day)
    label = f'{expected:%B} {expected.day}, {expected.year}'
    if 'CITY COUNCIL' not in first or label not in first:
        raise ValueError(f'Packet contents do not identify {label} Council meeting')
    marks = [(reader.get_destination_page_number(b), b.title) for b in reader.outline if not isinstance(b, list)]
    assert marks[0] == (0, 'Agenda') and len(marks)>1
    path = ROOT/f'tmp/{cache_directory}/{day}-official.html'
    if not path.exists():
        from urllib.request import Request, urlopen
        url=f'https://pub-beaumont.escribemeetings.com/Meeting.aspx?Id={meeting_id}&Agenda=Agenda&lang=English'
        request=Request(url,headers={'User-Agent':'Mozilla/5.0','Origin':'https://www.beaumontca.gov','Referer':'https://www.beaumontca.gov/212/Agendas-Minutes'})
        path.parent.mkdir(parents=True,exist_ok=True)
        with urlopen(request,timeout=30) as response:path.write_bytes(response.read())
    original = path.read_bytes()
    official = html.fromstring(original)
    assert re.search(rf'{expected:%B}\s+0?{expected.day},\s*{expected.year}',clean(official.xpath('//title')[0].text_content()))
    items, links = [], {}
    current_section='Reports'
    for node in official.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," AgendaItem ")]'):
        counters=node.xpath('.//*[@class="AgendaItemCounter"]/text()')
        if not counters: continue
        attachments=[a for a in node.xpath('.//a[contains(@href,"DocumentId=")]') if a.xpath('ancestor::*[contains(concat(" ",normalize-space(@class)," ")," AgendaItem ")][1]')[0]==node]
        title=clean(node.xpath('.//*[@class="AgendaItemTitle"]')[0].text_content())
        if not re.fullmatch(r'[A-Z]\.\d+',counters[0]):
            # Section letters vary between meetings. Use the City's heading,
            # rather than interpreting G as consent or B as closed session.
            value=title.lower()
            current_section=next((section for label,section in [('closed session','Closed Session'),('consent calendar','Consent'),('public hearings','Public Hearing'),('action items','Action'),('announcements','Presentation'),('presentations','Presentation')] if label in value),'Reports')
            if not attachments:continue
        key=counters[0].rstrip('.')
        section=current_section
        recommendation=' '.join(clean(' '.join(n.itertext())) for n in node.xpath('.//*[contains(concat(" ",normalize-space(@class)," ")," MotionText ")]'))
        description=' '.join(clean(' '.join(n.itertext())) for n in node.xpath('.//*[contains(concat(" ",normalize-space(@class)," ")," AgendaItemDescription ")]'))
        items.append(dict(item=key,title=title,section=section,description=description,recommendation=recommendation))
        for anchor in attachments:
            identity=(key,norm(anchor.text_content()))
            assert identity not in links,(day,identity)
            links[identity]=urljoin('https://pub-beaumont.escribemeetings.com/',anchor.get('href'))
    matched=[]
    for _, title in marks[1:]:
        match=re.fullmatch(r'([A-Z](?:\.\d+)?)\.\s*(.*)',title)
        assert match,title
        identity=(match[1],norm(match[2]))
        assert identity in links and identity not in matched,(day,identity)
        matched.append(identity)
    assert set(matched)==set(links),(day,'Official HTML and packet inventories differ')
    return source,reader,marks,items,links,hashlib.sha256(original).hexdigest()

def main(meetings=None, cache_directory='2025-spring'):
    meetings=MEETINGS if meetings is None else meetings
    parser=argparse.ArgumentParser()
    parser.add_argument('--meeting',action='append',choices=meetings)
    parser.add_argument('--audit-only',action='store_true')
    args=parser.parse_args()
    for day in args.meeting or meetings:
        source,reader,marks,items,links,html_sha=inventory(day,meetings,cache_directory)
        if args.audit_only:
            print(day,len(items),'items;',len(links),'exact attachment matches',flush=True)
            del reader;gc.collect();continue
        target=ROOT/f'docs/official-documents/{day}';target.mkdir(parents=True,exist_ok=True)
        packet_key=f'records/agenda-packets/{day}/{day}-city-council-agenda-package.pdf'
        packet=ROOT/'docs'/packet_key;packet.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,packet)
        by_item={i['item']:i for i in items}
        counts={};documents=[]
        for i,(start,title) in enumerate(marks):
            end=marks[i+1][0] if i+1<len(marks) else len(reader.pages)
            assert 0<=start<end<=len(reader.pages)
            name='agenda.pdf'
            if i:
                key,label=re.fullmatch(r'([A-Z](?:\.\d+)?)\.\s*(.*)',title).groups()
                counts[key]=counts.get(key,0)+1
                name=f'item-{key.lower().replace(".","-")}-{counts[key]:02d}.pdf'
                documents.append(dict(item=key,section=by_item[key]['section'],title=label.removesuffix('.pdf'),itemTitle=by_item[key]['title'],packet_page_start=start+1,packet_page_end=end,archiveUrl=BASE+f'official-documents/{day}/{name}',officialUrl=links[(key,norm(label))],packetBookmarkTitle=title))
            writer=PdfWriter()
            for page in reader.pages[start:end]:writer.add_page(page)
            with (target/name).open('wb') as stream:writer.write(stream)
            check=PdfReader(target/name);assert len(check.pages)==end-start
            del check,writer;gc.collect()
            print(day,f'[{i+1}/{len(marks)}]',name,f'pages {start+1}-{end}',flush=True)
        official_url=f'https://pub-beaumont.escribemeetings.com/Meeting.aspx?Id={meetings[day][1]}&Agenda=Agenda&lang=English'
        result=dict(date=day,sourceFilename=source.name,packetPages=len(reader.pages),agendaPageCount=marks[1][0],packetArchiveUrl=BASE+packet_key,agendaUrl=BASE+f'official-documents/{day}/agenda.pdf',officialAgendaUrl=official_url,meetingStatus='held',audit=dict(checkedOn='2026-11-13',expectedDocuments=len(links),linkedDocuments=len(documents),officialHtmlAuditComplete=True,archiveComplete=False,officialHtmlSha256=html_sha,basis='Every official HTML attachment matched by agenda item and normalized filename to a unique supplied packet bookmark. Original City URLs and contiguous packet page ranges retained. Outcomes are not inferred from agenda recommendations.'),items=items,documents=documents)
        result['packetBytes']=source.stat().st_size
        (ROOT/f'data/council/{day}-agenda.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        del reader;gc.collect()

if __name__=='__main__':main()
