"""Replace the November placeholder with the supplied Council agenda and sources."""
import ast
import json
import re
from html import escape
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
DATE = '2026-11-17'
LABEL = 'November 17, 2026'
DECK = 'Stewart Park Phase II bidding, a sewer cleaning truck, police technology, short-term rental rules, and first-quarter budget adjustments.'

def build():
    review = json.loads((ROOT / f'data/council/{DATE}-review.json').read_text(encoding='utf-8'))
    packet = json.loads((ROOT / f'data/council/{DATE}-packet-map.json').read_text(encoding='utf-8'))
    items = [dict(i, section='Action' if i['item'].startswith('J.') else 'Consent') for i in review['items']]
    by_key = {i['item']:i for i in items}
    documents = [dict(d, itemTitle=by_key[d['item']]['title']) for d in packet['documents']]
    assert len(items) == 22 and len(documents) == 87
    assert set(by_key) == {d['item'] for d in documents}
    manifest = json.loads((ROOT / 'data/document-storage-manifest.json').read_text(encoding='utf-8'))
    stored = {d['url'] for d in manifest['documents'] if d.get('sha256') and d.get('publication_status') != 'pending-upload'}
    verified = all(d['archiveUrl'] in stored for d in documents) and packet['packetArchiveUrl'] in stored and packet['agendaArchiveUrl'] in stored
    agenda = dict(packet, documents=documents, items=items, meetingStatus='upcoming', officialAgendaUrl='https://pub-beaumont.escribemeetings.com/', officialPdfUrl=None, closedSessionTime='5:00 PM', regularSessionTime='6:00 PM', nextMeeting=dict(date='2026-12-15',time='6:00 PM',basis='Supplied November 17 agenda, packet page 5; unless otherwise posted.'), review=dict(reviewedOn=review['reviewedOn'],scope=review['scope']), audit=dict(checkedOn=review['reviewedOn'],expectedDocuments=87,linkedDocuments=87,votingItems=22,packetInventoryComplete=True,officialHtmlAuditComplete=False,archiveComplete=verified,basis='87 supporting document ranges inventoried from the supplied 1,786-page City packet bookmarks. Separate City HTML agenda inventory and individual City document URLs remain unverified.'))
    (ROOT / f'data/council/{DATE}-agenda.json').write_text(json.dumps(agenda,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    tree = ast.parse((ROOT / 'scripts/build_simple_interactive_agendas.py').read_text(encoding='utf-8'))
    template = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PAGE' for t in n.targets))
    page = template.format(label=LABEL,date=DATE,variable='BI_NOVEMBER_17_SOURCES')
    page = page.replace('Archived interactive agenda','Upcoming interactive agenda').replace('complete voting calendars','3 action items · 19 consent items · 87 supporting documents')
    page = page.replace('return staff.title.replace','return files[0].itemTitle||staff.title.replace').replace('${x.item} ${x.title}','${x.item} ${x.itemTitle} ${x.title}')
    page = page.replace('<div class="agenda-toolbar">','<p>Tuesday, November 17 · Closed session 5:00 PM · Regular meeting 6:00 PM · 550 E. Sixth Street.</p><p>All 87 bookmarked supporting documents are linked. No public hearing items are listed. Consent appears last here for browsing; the official meeting order places it before action items. <a href="2026-11-17.html#document-checks">Read the targeted document checks</a>. Proposed actions await Council decisions.</p><div class="agenda-toolbar">')
    page = page.replace(f'<a class="btn secondary" href="{packet["packetArchiveUrl"]}" target="_blank" rel="noopener">Full agenda packet ↗</a>','<button class="btn secondary" id="view-packet" type="button">View full agenda packet</button>')
    page = page.replace('render()})();','document.querySelector("#view-packet").addEventListener("click",()=>openViewer('+json.dumps(packet['packetArchiveUrl'])+',"November 17 agenda packet"));render()})();')
    transcript = DOCS / f'transcripts/{DATE}-city-council-transcript.txt'
    if transcript.exists():
        recording = ('<div class="status-actions"><a class="btn" href="https://www.youtube.com/watch?v=4ZI2N54mCRU">'
                     'Watch November 17 meeting</a><a class="btn secondary" href="../transcripts/reader.html?date=2026-11-17">'
                     'Search meeting transcript</a></div>')
        page = re.sub(r'(</h1>)', lambda match: match.group(0) + recording, page, count=1)
        page = page.replace('Upcoming interactive agenda', 'Interactive agenda')
    (DOCS / f'briefings/{DATE}-sources.html').write_text(page,encoding='utf-8')
    (DOCS / f'briefings/{DATE}-sources.js').write_text('window.BI_NOVEMBER_17_SOURCES='+json.dumps(documents,ensure_ascii=False)+';\n',encoding='utf-8')

    def viewer(url,title,page=None):
        return '../documents/viewer.html?'+('page='+str(page)+'&amp;' if page else '')+'url='+quote(url,safe='')+'&amp;title='+quote(title,safe='')
    def packet_page(p):
        d = next(d for d in documents if d['packet_page_start']<=p<=d['packet_page_end'])
        return f'<a href="{viewer(d["archiveUrl"],d["title"],p-d["packet_page_start"]+1)}">Packet p. {p}</a>'
    header_source = (DOCS / 'briefings/2026-10-20.html').read_text(encoding='utf-8')
    header = re.search(r'<header class="app-header">.*?</header>',header_source,re.S).group(0)
    head = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>November 17, 2026 Council Agenda Briefing | Beaumont Intelligence</title><meta name="description" content="November 17 Beaumont City Council agenda: Stewart Park Phase II, sewer truck, police technology, short-term rentals and budget adjustments."><link rel="stylesheet" href="../styles.css"><script defer src="../app.js"></script></head><body data-page="briefing"><a class="skip-link" href="#main">Skip to content</a>'+header
    body = '<main id="main"><section class="section"><div class="wrap narrow"><div class="eyebrow">Meeting held · Pre-meeting agenda analysis</div><h1>November 17, 2026 Council agenda briefing</h1><p class="lead-copy">'+DECK+'</p><p><strong>Tuesday, November 17 · Closed session 5:00 PM · Regular meeting 6:00 PM</strong><br>550 E. Sixth Street, Beaumont, CA</p>'
    body += '<div class="status-actions"><a class="btn" href="2026-11-17-sources.html">Open interactive agenda</a><a class="btn secondary" href="'+viewer(packet['agendaArchiveUrl'],'November 17 agenda')+'">View five-page agenda</a><a class="btn secondary" href="'+viewer(packet['packetArchiveUrl'],'November 17 full agenda packet')+'">View full 1,786-page packet</a></div>'
    body += '<p class="source-note">Prepared November 13, 2026 from the supplied City agenda package. All 87 bookmarked supporting documents across 22 voting items are linked. '+escape(review['scope'])+' Council actions described here are proposed; reported invoices, asset values and budget results are not proof of payment or newly approved spending.</p>'
    body += '<h2>Attend and comment</h2><p>The notice provides in-person attendance and the <a href="https://beaumont-ca.municodemeetings.com/livestream">City livestream</a>. Send comments to <a href="mailto:nicolew@beaumontca.gov">nicolew@beaumontca.gov</a> with “Public Comment” in the subject before or during the meeting, up to the end of the item; call (951) 922-4845 before the item; or submit an in-person Request to Speak form. The notice generally allows three minutes. Contact the Clerk at (951) 572-3196 for accessibility assistance; 48 hours’ advance notice is requested.</p>'
    body += '<details class="card"><summary>Closed session, presentations and reports</summary><p>B.1 concerns a potential purchase at Edgar Avenue and East 5th Street, APN 418-091-017. B.2 lists one potential case by Carmen Hall Revocable Trust; B.3 lists Henry Valencia v. City of Beaumont, case CVRI2505484. B.4 concerns City Hall lease negotiations with T-Mobile. These are agenda descriptions, not reported outcomes. Presentations cover Waste Management recycling awards and FY2024–25 financial-reporting awards. Youth Council, legislative, City Manager and Council reports are also listed.</p></details>'
    flagged = [i for i in items if i.get('checks')]
    body += '<section class="card" id="document-checks"><h2>Document checks and questions</h2><p>Targeted comparisons identify scope, schedule and labeling questions. They do not establish Council decisions.</p><ul>'+''.join(f'<li><a href="#{i["item"].lower().replace(".","-")}">{i["item"]} · {escape(c["title"])}</a></li>' for i in flagged for c in i['checks'])+'</ul></section>'
    for section,anchor in [('Action','actions'),('Consent','consent')]:
        body += f'<section class="agenda-section" id="{anchor}"><h2>{section} '+('items' if section=='Action' else 'calendar')+'</h2>'
        for i in items:
            if i['section']!=section: continue
            refs = [d for d in documents if d['item']==i['item']]
            body += f'<article class="card" id="{i["item"].lower().replace(".","-")}"><h3>{i["item"]} · {escape(i["title"])}</h3><p>{escape(i["summary"])}</p>'
            if i.get('funding'): body += '<p><strong>Funding and fiscal context:</strong> '+escape(i['funding'])+'</p>'
            for c in i.get('checks',[]):
                body += '<details class="item-documents"><summary>'+escape(c['title'])+'</summary><div class="attachment-check-content"><p>'+escape(c['text'])+'</p><p class="source-note">'+' · '.join(packet_page(p) for p in c['packetPages'])+'</p></div></details>'
            d=next((d for d in refs if 'staff report' in d['title'].lower()),refs[0])
            body += f'<p><a href="{DATE}-sources.html">Open interactive agenda and supporting documents ({len(refs)})</a></p><p class="source-note"><a href="{viewer(d["archiveUrl"],d["title"])}">Read source document</a> · Packet pages {d["packet_page_start"]}–{d["packet_page_end"]}</p></article>'
        body += '</section>'
    body += '<p>No public hearing items are listed in the supplied agenda. The next regular meeting named in the packet is December 15, 2026, at 6:00 PM, unless otherwise posted.</p><p><a href="https://pub-beaumont.escribemeetings.com/">City meeting portal</a> · <a href="../council-intelligence.html">Council Intelligence</a></p></div></section></main></body></html>'
    (DOCS / f'briefings/{DATE}.html').write_text(head+body,encoding='utf-8')
    actions = '<div class="status-actions"><a class="btn" href="briefings/2026-11-17.html">Read November 17 briefing</a><a class="text-link" href="briefings/2026-11-17-sources.html">Open interactive agenda →</a><a class="text-link" href="briefings/2026-10-20.html#meeting-outcomes">October 20 outcomes &amp; transcript →</a></div>'
    archive = DOCS / 'council-briefings-2026.html'
    s = archive.read_text(encoding='utf-8')
    card = '<article class="story-card"><div class="pill pending">Meeting held · Agenda briefing</div><h3>November 17, 2026</h3><p>Closed session 5:00 PM · Regular meeting 6:00 PM</p><p>'+DECK+'</p>'+actions+'</article>'
    s = re.sub(r'<article class="story-card">(?:(?!</article>).)*<h3>November 17, 2026</h3>.*?</article>',lambda m:card,s,count=1,flags=re.S)
    archive.write_text(s,encoding='utf-8')
    path = DOCS / 'search-index.js'
    prefix = 'window.BI_SEARCH_INDEX = '
    records = json.loads(path.read_text(encoding='utf-8')[len(prefix):].strip().removesuffix(';'))
    for url,title,description in [(f'briefings/{DATE}.html',LABEL+' Council Agenda Briefing',DECK),(f'briefings/{DATE}-sources.html',LABEL+' Interactive Agenda','87 supporting documents across 22 consent and action items, with the full 1,786-page agenda packet.')]:
        row = dict(title=title,url=url,description=description,category='Council Intelligence',text=description+' '+' '.join(i['title']+' '+i['summary'] for i in items))
        found=False
        for record in records:
            for value in record.get('value',[]) if 'value' in record else [record]:
                if value.get('url')==url: value.update(row);found=True
        if not found: records.append(row)
    path.write_text(prefix+json.dumps(records,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
    if (ROOT / f'data/council/{DATE}-outcomes.json').exists():
        from build_november_2026_outcomes import build as publish_outcomes
        publish_outcomes()
    print('Built November 17 briefing, 22-item interactive agenda and 87-document inventory; archive verified:',verified)

if __name__=='__main__':
    build()
