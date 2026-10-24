"""Synchronize current narratives and source catalogs from reviewed Council records.

October outcomes remain transcript-based; supplied minutes support earlier actions.
Trevino is a related temporary skate project, never a Stewart Phase II award.
"""
import json
import re
import csv
from html.parser import HTMLParser
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
START = '<!-- downtown-stewart-update:start -->'
END = '<!-- downtown-stewart-update:end -->'
DOWNTOWN = ['downtown-revitalization' + suffix for suffix in
            ['', '-history', '-plan', '-business', '-funding', '-council-actions', '-questions', '-evidence']]
STEWART = ['stewart-park' + suffix for suffix in
           ['', '-history', '-features', '-funding', '-council-actions', '-questions', '-evidence']]


def load_records():
    minutes = json.loads((ROOT / 'data/council/2026-autumn-minutes-review.json').read_text(encoding='utf-8'))['meetings']
    outcomes = json.loads((ROOT / 'data/council/2026-10-20-outcomes.json').read_text(encoding='utf-8'))
    design = next(r for r in outcomes['items'] if r['item'] == 'J.3')
    result = []
    for date, item, center, slug in [('2026-09-15', 'J.1', 'downtown-revitalization', 'cluck-and-moo'),
                                     ('2026-10-06', 'J.5', 'stewart-park', 'trevino-skate')]:
        record = next(r for r in minutes[date]['items'] if r['item'] == item)
        result.append(dict(record, date=date, center=center, id=slug,
                           evidence='Supplied City minutes',
                           sourceUrl=minutes[date]['minutesUrl'],
                           recordUrl=f'briefings/{date}.html#minutes-review'))
    result.append(dict(design, date='2026-10-20', center='downtown-revitalization', id='phase-i-design',
                       evidence='Transcript-based outcome; approved October 20 minutes not collected',
                       limit=design['evidenceLimit'] + ' Corrected executed STB amendment and final design deliverables not collected.',
                       sourceUrl='transcripts/reader.html?date=2026-10-20',
                       recordUrl='briefings/2026-10-20.html#outcome-J.3'))
    result.append(dict(date='2026-10-20', item='J.3 discussion', center='stewart-park', id='bid-forecast',
                       title='Later Stewart Park bid forecast', vote=None,
                       summary='During the Downtown discussion, staff forecast a Stewart Park bid going out by the end of 2026 and returning early in 2027. This is later than July’s anticipated late-September Phase II advertising.',
                       limit='Transcript-based staff forecast, not a Council approval, issued solicitation or award. The remark does not expressly identify the phase or package; obtain the bid documents before treating it as a revised formal Phase II schedule. July’s Phase I March 2027 completion forecast is not independently refreshed by this remark.',
                       evidence='Automatic captions at 3:05:43–3:06:01; audiovisual playback not independently checked',
                       sourceUrl='https://www.youtube.com/watch?v=UVsGQHIcdkA&t=11143s',
                       recordUrl='transcripts/reader.html?date=2026-10-20'))
    return result


def source_links(record):
    return (f'<a href="{escape(record["recordUrl"], quote=True)}">Meeting record</a> · '
            f'<a href="{escape(record["sourceUrl"], quote=True)}">{escape(record["evidence"])}</a> · '
            f'<a href="briefings/{record["date"]}-sources.html">Agenda and supporting documents</a>')


def cards(records):
    return '<div class="story-grid center-action-grid">' + ''.join(
        f'<article class="story-card" id="sync-{r["id"]}"><div class="eyebrow">{r["date"]} · {escape(r["item"])}'
        + (f' · {escape(r["vote"])}' if r.get('vote') else '')
        + f'</div><h3>{escape(r["title"])}</h3><p>{escape(r["summary"])}</p>'
        + f'<p class="source-note"><strong>Evidence limit:</strong> {escape(r["limit"])}</p><p>{source_links(r)}</p></article>'
        for r in records) + '</div>'


def render(page, records):
    downtown = page in DOWNTOWN
    center = 'downtown-revitalization' if downtown else 'stewart-park'
    selected = sorted([r for r in records if r['center'] == center], key=lambda r: r['date'], reverse=True)
    details = ''
    if downtown:
        title = 'Phase I design advances; construction returns separately'
        intro = 'October 20 direction advances a smaller streetscape phase within Elevate 2050. The terminated 2025 GHD preliminary-design effort remains history; it is not the latest implementation status.'
        if page.endswith('-plan'):
            details = '<p>The Phase I concept covers trees, gateway features and furnishings along Beaumont Avenue, Sixth Street and Grace Avenue. The report and STB proposal differ on the Beaumont Avenue limits (Fifth–Eighth versus Fifth–Tenth). A full-site survey and electrical engineering are separate services; final limits, parking effects and construction support need confirmation in the executed scope. STB’s roughly 60-day design estimate follows the survey and is not a construction schedule.</p>'
        elif page.endswith('-funding'):
            details = '<div class="project-metrics"><div><span>Corrected concept/study cost</span><strong>$15,450</strong><small>Corrects the packet’s $15,800</small></div><div><span>Additional design services</span><strong>$53,400</strong><small>STB contract amendment directed</small></div><div><span>Combined STB design cost</span><strong>$68,850</strong><small>Corrects the packet’s $69,200</small></div></div><p>Staff identified the Public Works operating budget for design. The $2–3 million Phase I construction estimate is a planning range, not an appropriation or award. Existing downtown CIP resources and future funding options were discussed; the motion did not dedicate construction funding. Survey, electrical and other excluded services require their own scope and cost records. The earlier roughly $27 million public-right-of-way estimate concerns a broader scope and cannot be subtracted from or added to this smaller phase.</p>'
        elif page.endswith('-questions'):
            details = '<p><strong>Is there a final design or funded construction project?</strong> No final design, dedicated construction funding or construction award is established by the reviewed October action. Council directed the discussed Phase I concept and STB amendment. Obtain the corrected executed amendment, design deliverables, scope limits, separate-service budgets and future funding/award decisions.</p>'
        elif page.endswith('-business'):
            selected = [r for r in selected if r['id'] == 'cluck-and-moo']
            title = 'Four recorded 2026 business awards total $150,000'
            intro = 'September 15 adds Cluck and Moo’s $25,000 forgivable loan to Cloud9 ($25,000), Cornerstone ($50,000) and Tuscano’s ($50,000). These are authorization amounts. Disbursement, agreement compliance and final forgiveness remain unverified.'
        elif page.endswith('-evidence'):
            details = '<p><strong>Source reconciliation:</strong> The October packet retains the original $15,800/$69,200 figures; the transcript corrects them to $15,450/$68,850. Keep the original proposal distinguishable from the recorded direction. Approved October 20 minutes, the corrected executed amendment, final design/survey/electrical scope, construction funding and award, project accounting and business-loan performance records remain needed.</p>'
    else:
        title = 'Later bid forecast and separate temporary skate procurement'
        intro = 'The October records add a later Stewart Park bid forecast and related temporary skate amenities at Trevino Park. Trevino’s $120,000 authority is separate from Stewart Park’s P-10 phase estimates and ORLP grant; it does not prove Stewart Phase II was awarded or completed.'
        if page.endswith('-funding'):
            details = '<p><strong>Separate Trevino funding:</strong> $67,462.16 in P-09 savings plus $5,147.82 in P-20 savings totals $72,609.98; adding $47,390.02 from P27-01 gives the $120,000 procurement ceiling. The motion requires a later funding-source budget adjustment. No completed reallocation, payment or contract is established here. Do not add this authority to Stewart P-10 funding or its ORLP grant.</p>'
        elif page.endswith('-features'):
            details = '<p><strong>Temporary equipment versus permanent features:</strong> The October 6 action authorizes competitive procurement of temporary Trevino skate amenities. It does not establish installation, an award to American Ramp, or delivery of the permanent Stewart Park Phase II skate improvements listed below.</p>'
        elif page.endswith('-questions'):
            details = '<p><strong>Did Phase II go to bid in September?</strong> July staff expected late-September advertising; the reviewed record does not confirm it occurred. October staff instead discussed a Stewart bid by year-end and return early in 2027, without naming the package. Obtain the solicitation and phase schedule.</p><p><strong>Are the temporary skate amenities installed?</strong> The supplied October 6 minutes establish up to $120,000 in competitive procurement authority, with a later funding-source adjustment required. A bid result, executed contract, adjustment and installation evidence remain needed.</p>'
        elif page.endswith('-evidence'):
            details = '<p><strong>Records still needed:</strong> an issued Stewart bid with phase/package identification, a revised construction schedule and progress report; Trevino bid results, executed contract, funding-source adjustment and installation records; current P-10 commitments, expenditures and ORLP reimbursements. Approved October 20 minutes remain uncollected. The July restart and March 2027 forecast are dated staff statements, not independently verified current progress.</p>'
    return (START + f'\n<section class="section compact" id="current-actions"><div class="wrap"><div class="section-heading"><div><div class="eyebrow">Recent actions · Reviewed October 24, 2026</div><h2>{title}</h2></div></div><p>{intro}</p>'
            + details + cards(selected) + '</div></section>\n' + END)


def update_narrative(page, text):
    replacements = {
        'The 2025 preliminary-design contract was terminated after its CIP budget was redirected. Council later directed staff to develop short-term goals.': 'October 20: Council directed Phase I streetscape design and an STB amendment. Construction funding and award return separately; the outcome remains transcript-based.',
        'The adopted vision remains, but its first preliminary-design effort was stopped.': 'Phase I streetscape design advances within the adopted vision.',
        'Short-term scope and project accounting': 'Executed STB amendment, construction funding and project accounting',
        '<dt>Verified actions</dt><dd>10</dd>': '<dt>Latest design direction</dt><dd>October 20, 2026 · transcript-based</dd>',
        'The record does not establish a replacement design contract or funded construction program.': 'That January direction is historical; October 20 later directed the Phase I concept and an STB amendment. Construction funding and award remain separate.',
        'and Council\'s January 2026 direction to pursue short-term goals while the larger vision remains in place.': 'Council’s January 2026 short-term direction, and October 20 Phase I design direction while the larger vision remains in place.',
        'Three verified 2026 awards total $125,000 in stated forgivable-loan authority.': 'Four recorded 2026 awards total $150,000 in stated forgivable-loan authority, including September 15’s $25,000 Cluck and Moo action.',
        'three downtown business incentives totaling $125,000': 'four downtown business incentives totaling $150,000',
        'The three verified 2026 actions authorized forgivable loans totaling $125,000.': 'The four recorded 2026 actions authorized forgivable loans totaling $150,000, including September 15’s Cluck and Moo award.',
        '<strong>$125,000</strong>': '<strong>$150,000</strong>',
        '<span>$125,000</span>': '<span>$150,000</span>',
        '<span>3 verified awards</span>': '<span>4 recorded awards</span>',
        'and any later design, funding, mobility, or construction actions.': 'the corrected executed October STB amendment and its deliverables, and future construction funding and award records.',
        'Latest verified construction update': 'Dated construction report · July 21, 2026',
        'Dated construction report · Later bid forecast below': 'Dated construction report · July 21, 2026',
        'Phase I construction restarted; staff anticipated completion around March 2027.': 'July restart reported; October adds a later bid forecast.',
        '<dd>Phase I construction restarted</dd>': '<dd>Restart reported July 21; current progress record needed</dd>',
        '<dt>Phase I target reported</dt>': '<dt>Phase I target · July forecast</dt>',
        'Construction restart and anticipated schedule': 'July construction restart and historical schedule forecast',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    if page == 'downtown-revitalization-questions':
        text = text.replace('In January 2026, Council directed staff to develop short-term goals. No final construction award is established.', 'In January 2026, Council directed short-term goals; on October 20 it directed Phase I design and an STB amendment. Construction funding and award return separately. The October outcome is transcript-based.')
        text = text.replace('Not in the records currently published by this center. Gateways,', 'October 20 advanced the discussed Phase I concept and design services, not a completed final design. Broader gateways,')
        text = text.replace('No single figure represents the complete cost of Elevate 2050.', 'October’s $68,850 combined STB design cost and $2–3 million Phase I construction estimate cover a smaller phase; no single figure represents the complete cost of Elevate 2050.')
    if page == 'downtown-revitalization':
        text = text.replace('Council directed a measured, smaller-step implementation approach.</p></article>', 'Council directed a measured, smaller-step implementation approach. On October 20, Council directed the Phase I streetscape concept and STB amendment: $53,400 in added design services and $68,850 combined design cost after correction. Construction funding and award return separately; the October outcome remains transcript-based.</p></article>')
    if page == 'downtown-revitalization-funding':
        text = text.replace('<h3>Future construction</h3>', '<h3>Earlier broader construction estimate · January 2026</h3>')
    if page == 'stewart-park':
        text = text.replace('These are staff-reported schedule expectations, not completion guarantees.', 'These are historical staff forecasts. On October 20, staff discussed a Stewart bid by year-end and return early in 2027 without identifying its phase/package; the record does not confirm September advertising or refresh the Phase I completion target.')
    return text


def catalog(records):
    """Publish a source register and include actual packet documents, not only summaries."""
    entries = []
    for r in records:
        entries.append(dict(r))
        if r['id'] in ('phase-i-design', 'trevino-skate'):
            agenda = json.loads((ROOT / f'data/council/{r["date"]}-agenda.json').read_text(encoding='utf-8'))
            entries[-1]['documents'] = [dict(title=d['title'].strip(), url=d.get('archiveUrl') or d['officialUrl'],
                                            officialUrl=d['officialUrl']) for d in agenda['documents'] if d['item'] == r['item']]
    (ROOT / 'data/center-recent-actions.json').write_text(json.dumps({'reviewedOn': '2026-10-24', 'records': entries}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return entries


def sync_stewart_catalog(records):
    additions = []
    for r in records:
        if r['center'] != 'stewart-park':
            continue
        prefix = 'SP-RELATED-TREVINO' if r['id'] == 'trevino-skate' else 'SP-FORECAST-2026-1020'
        additions.append(dict(archive_code=prefix, title=r['title'], date=r['date'],
                              type=r['evidence'], url=r['sourceUrl'], publisher='City of Beaumont',
                              evidence='A' if r['id'] == 'trevino-skate' else 'C', status='reviewed',
                              summary=r['summary'] + ' ' + r['limit'], topics='Related temporary skate amenities; Schedule; Evidence limits'))
        for index, doc in enumerate(r.get('documents', []), 1):
            additions.append(dict(archive_code=prefix + '-DOC-' + str(index), title=doc['title'], date=r['date'],
                                  type='Agenda proposal', url=doc['url'], publisher='City of Beaumont', evidence='A',
                                  status='reviewed',
                                  summary='Related Trevino project; separate from Stewart P-10. The American Ramp proposal is not evidence of an award.',
                                  topics='Related temporary skate amenities; Procurement'))
    path = ROOT / 'data/stewart-park/source-catalog.csv'
    with path.open(encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        previous = list(reader)
    codes = {r['archive_code'] for r in additions}
    rows = [r for r in previous if r['archive_code'] not in codes] + additions
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    (path.with_suffix('.json')).write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # The legacy searchable Stewart inventory also needs these sources, not just the new cards.
    path = DOCS / 'data.js'
    prefix = 'window.MBF_DATA = '
    raw = path.read_text(encoding='utf-8').strip()
    assert raw.startswith(prefix)
    data = json.loads(raw[len(prefix):].removesuffix(';'))
    data['documents'] = [d for d in data['documents'] if d['archive_code'] not in codes] + [
        dict(archive_code=r['archive_code'], title=r['title'], document_date=r['date'],
             document_type=('Meeting minutes' if r['archive_code'] == 'SP-RELATED-TREVINO'
                            else 'Meeting transcript' if r['archive_code'] == 'SP-FORECAST-2026-1020'
                            else 'Agenda proposal'), official_url=r['url'], publisher=r['publisher'],
             evidence_level=r['evidence'], verification_status=r['status'], summary=r['summary']) for r in additions]
    path.write_text(prefix + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')


class PageText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def sync_search():
    path = DOCS / 'search-index.js'
    prefix = 'window.BI_SEARCH_INDEX = '
    records = json.loads(path.read_text(encoding='utf-8')[len(prefix):].strip().removesuffix(';'))
    for page in DOWNTOWN + STEWART:
        text = (DOCS / (page + '.html')).read_text(encoding='utf-8')
        parser = PageText()
        parser.feed(text)
        body = re.sub(r'\s+', ' ', ' '.join(parser.parts)).strip()
        record = dict(title=re.search(r'<title>(.*?)</title>', text, re.S)[1], url=page + '.html',
                      category='Intelligence Center', description='Recent actions reviewed October 24, 2026; authorizations, forecasts and source limits distinguished.', text=body)
        found = False
        for group in records:
            for current in group.get('value', [group]):
                if current.get('url') == record['url']:
                    current.update(record)
                    found = True
        if not found:
            records.append(record)
    path.write_text(prefix + json.dumps(records, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')


def main():
    records = catalog(load_records())
    for page in DOWNTOWN + STEWART:
        path = DOCS / (page + '.html')
        text = path.read_text(encoding='utf-8')
        text = re.sub(r'\s*' + re.escape(START) + '.*?' + re.escape(END) + r'\s*', '', text, flags=re.S)
        text = update_narrative(page, text)
        block = render(page, records)
        if page.endswith('-evidence'):
            links = ''.join(f'<li><a href="{escape(d["url"], quote=True)}">{escape(d["title"])}</a> · Original agenda proposal; final action and limits above</li>'
                            for r in records if r['center'] == ('downtown-revitalization' if page in DOWNTOWN else 'stewart-park') for d in r.get('documents', []))
            block = block.replace('</div></section>\n' + END, '<h3>Archived supporting documents</h3><ul class="evidence-list">' + links + '</ul></div></section>\n' + END)
        # Promote current status within the core page, ahead of the historical record.
        assert text.count('<main id="main">') == 1, page
        text = text.replace('<main id="main">', '<main id="main">\n' + block + '\n', 1)
        path.write_text(text, encoding='utf-8', newline='\n')
    sync_stewart_catalog(records)
    sync_search()


if __name__ == '__main__':
    main()
