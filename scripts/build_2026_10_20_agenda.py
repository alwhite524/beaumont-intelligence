"""Publish the October 20 pre-meeting agenda from the verified City inventory."""
import ast
import json
import re
from html import escape
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
DATE = '2026-10-20'
OFFICIAL = 'https://pub-beaumont.escribemeetings.com/Meeting.aspx?Id=8ce94024-faf5-4cb0-89f8-5a598025048d&Agenda=Agenda&lang=English'
PACKET = 'https://pub-beaumont.escribemeetings.com/FileStream.ashx?DocumentId=11352'
# Document IDs and descriptive labels inventoried from the City's HTML agenda.
ROWS = '''G.1|Ratification of warrants|11271:September 11 warrants;11272:September 18 warrants;11273:September 25 warrants
G.2|Approval of minutes|11339:October 6 Council minutes
G.3|September City Attorney invoices|11274:SBEMP September 2026 invoices
G.4|Conflict of interest code update|11275:Staff report;11276:Resolution amending conflict of interest code
G.5|Omnitrans coordinated transit services agreement|11298:Staff report;11299:Omnitrans and Beaumont Transit agreement
G.6|HCN Bank Trunk or Treat deposit and fee waiver|11300:Staff report;11301:Deposit waiver resolution;11302:Special event fee waiver policy;11303:Special event application;11304:Conditions of approval;11305:Fee waiver request;11306:Levine Act statement
G.7|Beaumont Library storm drain performance bond release|11289:Staff report;11290:Library expansion bond release package;11291:Notice of completion
G.8|Executive employment agreement amendments|11314:Staff report;11315:City Engineer and Public Works Director amendment;11316:Community Development Director amendment;11317:Community Services Director amendment;11318:Director of Water Reclamation amendment;11319:Chief of Police amendment
G.9|Public Works Principal Engineer position|11340:Staff report;11341:Existing organizational chart;11342:Proposed organizational chart
G.10|Fehr and Peers citywide traffic analysis|11292:Staff report;11293:Signed Fehr and Peers agreement;11294:First amendment;11295:Fehr and Peers proposal
G.11|Matich street rehabilitation construction contingency increase|11307:Staff report;11308:Contract C26-102
G.12|Fairways storm drain performance bond releases|11280:Staff report;11281:Tract 37697 bond release package;11282:Tract 37698 bond release package;11283:Notice of completion
G.13|September financial reports|11331:Staff report;11332:Governmental funds;11333:Proprietary funds;11334:Fiduciary funds
G.14|FY27 Quarter 1 purchases and contract awards|11335:Staff report;11336:Purchase orders for goods;11337:Purchase orders for Public Works;11338:Purchase orders for professional and general services
G.15|October 14 Planning Commission action report|11348:Staff report
I.1|Religious facility revenue bonds at 1780 Orchard Heights Avenue|11277:Staff report - Calvary Chapel TEFRA hearing;11278:Calvary resolution;11279:TEFRA public notice
I.2|Continued hearing on short-term rentals and fees|11284:Staff report;11285:Short-term rental ordinance;11286:Exhibit A to ordinance;11287:Draft fee resolution;11288:Short-term rental presentation
I.3|Municipal Code provisions for City committees|11343:Staff report;11344:Public Works Advisory Committee ordinance;11345:Economic Development Committee chapter;11346:Parks and Recreation Committee chapter;11347:Financial and Audit Committee amendment
J.1|Tilden-Coil services for the new police station|11309:Staff report;11310:Professional services agreement;11311:Tilden-Coil Levine Act statement;11312:Proposal;11313:Cost proposal
J.2|$80,000 sponsorship request for the 2027 IOA Championship|11327:Staff report;11328:IOA Classic media plan;11329:2027 proposal;11330:Sponsorship application
J.3|Downtown Revitalization Phase I|11323:Staff report;11324:Downtown tree layout;11325:Beaumont downtown study;11326:STB proposal
J.4|Banning agreement for Highland Springs Avenue improvements|11296:Staff report;11297:City of Banning cooperative agreement
J.5|Tyler Technologies three-year enterprise renewal|11320:Staff report;11321:Signed Tyler amendment;11322:Sole source justification'''
SUMMARIES = {
'I.1': 'Consider approval of tax-exempt religious facility revenue bonds for the borrower. The agenda states that the City would have no responsibility or liability for the bonds.',
'I.2': 'Hold the continued public hearing and consider a short-term rental ordinance and a resolution establishing program fees.',
'I.3': 'Introduce ordinances for Parks and Recreation, Economic Development, and Public Works Advisory committees, and amend the Financial and Audit Committee chapter.',
'J.1': 'Consider a professional services agreement with Tilden-Coil Constructors for project program management and owner’s representative services for CIP PS-07, the new police station.',
'J.2': 'Consider FGTA, Inc. / Epson Tour’s request for an $80,000 City sponsorship of the IOA Championship, April 19–25, 2027, at Morongo Golf Club at Tukwet Canyon.',
'J.3': 'Discuss implementation of Phase I of the City’s Downtown Revitalization Plan.',
'J.4': 'Consider a cooperative agreement establishing Beaumont’s and Banning’s roles and responsibilities for Highland Springs Avenue street improvements.',
'J.5': 'Consider a three-year amendment for FY2026–27 through FY2028–29: $631,892.93 in contract services plus $346,144.50 in estimated wastewater billing usage, totaling $978,037.43.',
'G.8': 'Consider executive contract amendments intended to standardize employee benefits following labor negotiations.',
'G.9': 'Consider replacing the Senior Engineer position allocation with a Principal Engineer position.',
'G.10': 'Consider an on-call task order for the citywide traffic study, CIP R27-06.',
'G.11': 'Consider an increase in construction contingency for Matich Corporation’s FY26 annual street rehabilitation project, CIP R26-01.',
}

def build():
    items, documents = [], []
    for row in ROWS.splitlines():
        item, title, refs = row.split('|')
        section = {'G':'Consent','I':'Public Hearing','J':'Action'}[item[0]]
        items.append(dict(item=item, title=title, section=section, summary=SUMMARIES.get(item, 'Consider the listed consent-calendar item; consult the supporting documents for the proposed action and details.')))
        for ref in refs.split(';'):
            ident, label = ref.split(':', 1)
            documents.append(dict(item=item, itemTitle=title, section=section, title=label, officialUrl=f'https://pub-beaumont.escribemeetings.com/filestream.ashx?DocumentId={ident}'))
    assert len(items) == 23 and len(documents) == 78
    review_path = ROOT / f'data/council/{DATE}-review.json'
    review = json.loads(review_path.read_text(encoding='utf-8')) if review_path.exists() else None
    if review:
        for item in items:
            item.update(review['items'][item['item']])
    agenda = dict(date=DATE, officialAgendaUrl=OFFICIAL, officialPdfUrl=PACKET, meetingStatus='upcoming', audit=dict(checkedOn='2026-10-16', expectedDocuments=78, linkedDocuments=78, votingItems=23, officialHtmlAuditComplete=True, archiveComplete=False, basis='All 78 unique supporting-document URLs inventoried item by item from the official City HTML agenda. Links use City-hosted originals; archive copies have not been verified.'), items=items, documents=documents)
    packet_map = ROOT / f'data/council/{DATE}-packet-map.json'
    packet_url = PACKET
    if packet_map.exists():
        archived = json.loads(packet_map.read_text(encoding='utf-8'))
        documents = archived['documents']
        agenda.update(archived)
        packet_url = archived['packetArchiveUrl']
        agenda['audit'].update(archiveComplete=True, basis='All 78 City-listed supporting documents matched by item and sequence to the supplied 706-page packet bookmarks. Page ranges retained; archived copies verified by checksum and size during upload. Original City URLs retained as provenance.')
    if review:
        agenda['review'] = dict(reviewedOn=review['reviewedOn'], scope=review['scope'])
        if review.get('attachmentReview'):
            agenda['review']['attachmentReview'] = review['attachmentReview']
    (ROOT / f'data/council/{DATE}-agenda.json').write_text(json.dumps(agenda, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    # Reuse the established searchable agenda and in-page document viewer.
    tree = ast.parse((ROOT / 'scripts/build_simple_interactive_agendas.py').read_text(encoding='utf-8'))
    template = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id=='PAGE' for t in n.targets))
    page = template.format(label='October 20, 2026', date=DATE, variable='BI_OCTOBER_20_SOURCES')
    page = page.replace('Archived interactive agenda','Upcoming interactive agenda').replace('complete voting calendars','3 hearings · 5 action items · 15 consent items')
    page = page.replace(f'https://documents.beaumontintelligence.com/records/agenda-packets/{DATE}/{DATE}-city-council-agenda-package.pdf', escape(packet_url, quote=True))
    page = page.replace('d.archiveUrl', '(d.archiveUrl||d.officialUrl)').replace('return staff.title.replace', 'return files[0].itemTitle||staff.title.replace').replace('${x.item} ${x.title}', '${x.item} ${x.itemTitle} ${x.title}')
    page = page.replace('<div class="agenda-toolbar">','<p>Tuesday, October 20 · Closed session 5:00 PM · Regular meeting 6:00 PM · 550 E. Sixth Street.</p><p>Proposed actions await Council decisions. All 78 City-listed supporting documents are linked across 23 items, checked October 16. Documents use original City URLs. Consent appears last here for browsing; the official meeting considers consent before hearings and action items.</p><div class="agenda-toolbar">')
    if packet_map.exists():
        page = page.replace('Documents use original City URLs.', 'Documents open from the Beaumont Intelligence archive, extracted from the supplied 706-page packet. Original City URLs are retained in the source register.')
        page = page.replace(f'<a class="btn secondary" href="{packet_url}" target="_blank" rel="noopener">Full agenda packet ↗</a>', '<button class="btn secondary" id="view-packet" type="button">View full agenda packet</button>')
        page = page.replace('render()})();', 'document.querySelector("#view-packet").addEventListener("click",()=>openViewer('+json.dumps(packet_url)+',"October 20 agenda packet"));render()})();')
    if review and any(check.get('attention') for item in items for check in item.get('checks', [])):
        page = page.replace('<div class="agenda-toolbar">', f'<p><strong>Attachment review:</strong> Some staff reports and draft documents differ. <a href="{DATE}.html#document-checks">Read the document comparisons and open questions</a> before relying on a proposed amount or rule.</p><div class="agenda-toolbar">')
    (DOCS / f'briefings/{DATE}-sources.html').write_text(page, encoding='utf-8')
    (DOCS / f'briefings/{DATE}-sources.js').write_text('window.BI_OCTOBER_20_SOURCES='+json.dumps(documents,ensure_ascii=False)+';\n',encoding='utf-8')
    previous = (DOCS / 'briefings/2026-10-06.html').read_text(encoding='utf-8')
    head = previous[:previous.index('<main id="main">')].replace('October 6','October 20').replace('2026-10-06','2026-10-20').replace('Council Meeting Record','Council Agenda Briefing').replace('Meeting video available · Outcome review in progress','Upcoming meeting · Proposed actions').replace('Council meeting record','Council agenda briefing')
    head = head.replace('</style>', '.attachment-check-content{display:block;padding:0 15px 15px}.attachment-check-content h4{margin:20px 0 8px}.attachment-check-content p{margin:8px 0 14px}</style>')
    head = head[:head.index('<nav class="briefing-tools"')] + '<nav class="briefing-tools" aria-label="Briefing sections"><div class="wrap"><a href="#overview">Overview</a><a href="#document-checks">Document checks</a><a href="#hearings">Hearings</a><a href="#actions">Action items</a><a href="#consent">Consent</a></div></nav>'
    body = '<main id="main"><section class="section compact"><div class="wrap narrow" id="overview"><div class="eyebrow">Pre-meeting briefing</div><h1>October 20, 2026 City Council meeting</h1><p class="lead-copy">Short-term rentals, a new police station services agreement, downtown improvements, an $80,000 golf sponsorship request, and a proposed $978,037.43 technology renewal.</p><span class="pill pending">Upcoming · Council action pending</span><p><strong>Tuesday, October 20, 2026</strong><br>Closed session: 5:00 PM · Regular meeting: 6:00 PM<br>550 E. Sixth Street, Beaumont, CA</p>'
    body += f'<div class="status-actions"><a class="btn" href="{DATE}-sources.html">Open interactive agenda</a><a class="btn secondary" href="{escape(OFFICIAL)}">Official City agenda</a><a class="btn secondary" href="../documents/viewer.html?url={quote(packet_url,safe="")}&amp;title=October%2020%20agenda%20packet">View full agenda packet</a></div>'
    body += '<p class="source-note">Prepared October 16 from the supplied five-page agenda and the City’s HTML agenda. All actions and amounts are proposals, not approvals. The interactive agenda links all 78 City-listed supporting documents across 23 items. Document-link inventory is complete; archived copies and a substantive review of every attachment are not complete.</p><h2>Attend and comment</h2><p>Attend in person or watch the <a href="https://beaumont-ca.municodemeetings.com/livestream">City livestream</a>. Email <a href="mailto:nicolew@beaumontca.gov">nicolew@beaumontca.gov</a> with “Public Comment” in the subject before or during the meeting, up to the end of the corresponding item; call <a href="tel:9519224845">(951) 922-4845</a> before the item; or submit an in-person Request to Speak form. Comments generally have a three-minute limit. For accessibility assistance, contact the Clerk at (951) 572-3196; the notice requests 48 hours’ advance notification.</p><details class="card"><summary>Closed session, presentation, and reports</summary><p>B.1–B.4 list existing litigation, one potential case, Police Officers Association labor negotiations, and price and terms for a potential purchase of Oak Valley property from Beaumont Unified School District. E.1 introduces Grant Analyst Jenny Espinosa. The agenda also includes public comment, Youth Council, legislative updates, City Manager and Council reports, and future agenda items.</p></details>'
    flagged = [(item, check) for item in items for check in item.get('checks', []) if check.get('attention')]
    flagged.sort(key=lambda pair: ['Public Hearing', 'Action', 'Consent'].index(pair[0]['section']))
    if flagged:
        body += '<section class="card" id="document-checks"><h2>Documents needing clarification</h2><p>The supplied packet contains differences between staff reports and proposed documents, plus financial-report presentation questions. The comparisons below identify the versions and page references; they do not establish what Council will approve.</p><ul>'
        for item, check in flagged:
            anchor = item['item'].lower().replace('.', '-')
            body += f'<li><a href="#{anchor}">{item["item"]} · {escape(check["title"])}</a></li>'
        body += '</ul><p>Expand “Attachment checks” under each item to read the evidence and open the relevant packet pages.</p></section>'

    def packet_page_link(page):
        source = next((d for d in documents if d.get('packet_page_start', 0) <= page <= d.get('packet_page_end', 0)), None)
        if source is None:
            raise ValueError(f'No source document for reviewed packet page {page}')
        url = source.get('archiveUrl') or source['officialUrl']
        local_page = page - source['packet_page_start'] + 1
        return f'<a href="../documents/viewer.html?url={quote(url,safe="")}&amp;page={local_page}&amp;title={quote(source["title"],safe="")}">Packet p. {page}</a>'

    for section, anchor, heading in [('Public Hearing','hearings','Public hearings'),('Action','actions','Action items'),('Consent','consent','Consent calendar')]:
        body += f'<section class="agenda-section" id="{anchor}"><h2>{heading}</h2>'
        for item in items:
            if item['section'] != section: continue
            refs = [d for d in documents if d['item']==item['item']]
            body += f'<article class="card" id="{item["item"].lower().replace(".","-")}"><h3>{item["item"]} · {escape(item["title"])}</h3><p>{escape(item["summary"])}</p><p><a href="{DATE}-sources.html">Open interactive agenda and supporting documents ({len(refs)})</a></p></article>'
            extra = ''
            if item.get('funding'):
                extra += f'<p><strong>Funding and fiscal context:</strong> {escape(item["funding"])}</p>'
            if item.get('question'):
                extra += f'<p><strong>Question for consideration:</strong> {escape(item["question"])}</p>'
            if item.get('checks'):
                extra += f'<details class="item-documents"><summary>Attachment checks ({len(item["checks"])})</summary><div class="attachment-check-content">'
                for check in item['checks']:
                    extra += f'<h4>{escape(check["title"])}</h4><p>{escape(check["text"])}</p><p class="source-note">' + ' · '.join(packet_page_link(page) for page in check['packetPages']) + '</p>'
                extra += '</div></details>'
            source = next((d for d in refs if 'staff report' in d['title'].lower()), None)
            if source:
                url = source.get('archiveUrl') or source['officialUrl']
                extra += f'<p class="source-note"><a href="../documents/viewer.html?url={quote(url,safe="")}&amp;title={quote(source["title"],safe="")}">Read the staff report</a> · Packet pages {source.get("packet_page_start", "") }–{source.get("packet_page_end", "")}</p>'
            body = body.removesuffix('</article>') + extra + '</article>'
        body += '</section>'
    body += '<p class="source-note">The next regular meeting listed in this agenda is Tuesday, November 17, 2026, at 6:00 PM, unless otherwise posted.</p><p><a href="../council-intelligence.html">Return to Council Intelligence</a></p></div></section></main></body></html>'
    if packet_map.exists():
        body = body.replace('the supplied five-page agenda and the City’s HTML agenda', 'the supplied 706-page agenda packet, with supporting documents matched to the City agenda inventory').replace('Document-link inventory is complete; archived copies and a substantive review of every attachment are not complete.', 'All 78 supporting documents and the full packet are available from the Beaumont Intelligence archive. Page ranges and original City source URLs are retained. A substantive review of every attachment is not complete.')
    if review:
        body = body.replace('All actions and amounts are proposals, not approvals.', 'Council actions described here are proposed; financial-statement and invoice figures are reported amounts.')
        body = body.replace('A substantive review of every attachment is not complete.', escape(review['scope']) + ' Questions below identify points for staff clarification; Council decisions will be recorded separately after the meeting.')
    (DOCS / f'briefings/{DATE}.html').write_text(head+body, encoding='utf-8')
    deck = 'Short-term rentals, the new police station, downtown revitalization, Highland Springs improvements, golf sponsorship, and City technology services.'
    actions = '<div class="status-actions"><a class="btn" href="briefings/2026-10-20.html">Read October 20 briefing</a><a class="text-link" href="briefings/2026-10-20-sources.html">Open interactive agenda →</a></div>'
    home = DOCS / 'index.html'
    text = home.read_text(encoding='utf-8')
    text = re.sub(r'<p class="council-deck">.*?</p>', f'<p class="council-deck">{deck}</p>', text, count=1)
    text = re.sub(r'(<h2 id="latest-council-title">.*?</h2>.*?)(<div class="status-actions">.*?</div>)', lambda m:m[1]+actions, text, count=1)
    text = text.replace('Next scheduled meeting</span>', 'Agenda available</span>')
    home.write_text(text, encoding='utf-8')
    council = DOCS / 'council-intelligence.html'
    text = council.read_text(encoding='utf-8')
    text = re.sub(r'<section class="section compact alt"><div class="wrap"><div class="eyebrow">Upcoming meeting</div>.*?</section>', '<section class="section compact alt"><div class="wrap"><div class="eyebrow">Upcoming meeting · Agenda available</div><h2>October 20, 2026</h2><p>Closed session 5:00 PM · Regular meeting 6:00 PM</p><p>'+deck+'</p>'+actions+'</div></section>', text, count=1)
    council.write_text(text, encoding='utf-8')
    archive = DOCS / 'council-briefings-2026.html'
    text = archive.read_text(encoding='utf-8')
    if 'href="briefings/2026-10-20.html"' not in text:
        text = text.replace('<div class="story-grid">', '<div class="story-grid"><article class="story-card"><div class="pill pending">Upcoming · Agenda available</div><h3>October 20, 2026</h3><p>Closed session 5:00 PM · Regular meeting 6:00 PM</p><p>'+deck+'</p>'+actions+'</article>', 1)
    archive.write_text(text, encoding='utf-8')
    print('Built October 20 briefing, interactive agenda, and 78-document inventory')
    if (ROOT / f'data/council/{DATE}-outcomes.json').exists():
        from build_october_2026_update import build as publish_outcomes
        publish_outcomes()

if __name__ == '__main__':
    build()
