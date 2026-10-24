"""Apply the supplied September 15 and October 6 minutes review to public records."""
import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
START = '<!-- autumn-2026-minutes:start -->'
END = '<!-- autumn-2026-minutes:end -->'


def build():
    review = json.loads((ROOT / 'data/council/2026-autumn-minutes-review.json').read_text(encoding='utf-8'))
    for date, meeting in review['meetings'].items():
        url = meeting['minutesUrl']
        cards = []
        for item in meeting['items']:
            vote = f' · {item["vote"]}' if item['vote'] else ''
            cards.append(f'<article class="card" id="minutes-{escape(item["item"], quote=True)}"><div class="meta">{escape(item["item"] + vote)}</div>'
                         f'<h3>{escape(item["title"])}</h3><p>{escape(item["summary"])}</p>'
                         f'<p class="source-note"><strong>Evidence limit:</strong> {escape(item["limit"])}</p></article>')
        issues = ''.join(f'<p><strong>{escape(issue["item"])}:</strong> {escape(issue["text"])}</p>' for issue in meeting['discrepancies'])
        block = ('<section id="minutes-review" aria-labelledby="minutes-review-title"><h2 id="minutes-review-title">Decisions checked against the supplied minutes</h2>'
                 '<p class="source-note">Reviewed October 24, 2026. The user-supplied City minutes are retained unchanged as Word originals. '
                 'Agenda recommendations and transcript-derived details remain distinguishable from the recorded minutes. Minutes establish recorded authorizations, not actual expenditures or completed work.</p>'
                 f'<p>{escape(meeting["attendance"])}</p><p><a class="btn" href="{escape(url, quote=True)}">Open supplied minutes (Word original)</a></p>'
                 '<details class="card" open><summary>Source differences and clarifications</summary>' + issues + '</details>'
                 + ''.join(cards) + '</section>')
        path = DOCS / f'briefings/{date}.html'
        page = path.read_text(encoding='utf-8')
        page = re.sub(re.escape(START) + '.*?' + re.escape(END), '', page, flags=re.S)
        if date == '2026-09-15':
            marker = '<section class="section compact"><div class="wrap narrow">'
            page = page.replace(marker, START + '<section class="section compact"><div class="wrap narrow">' + block + '</div></section>' + END + marker, 1)
            page = page.replace('Outcomes and timestamps verified against the meeting transcript', 'Minutes checked; video timestamps remain transcript-based')
            page = page.replace('with transcript-verified outcomes, item video timestamps, and complete voting-calendar documents.', 'with supplied minutes, source discrepancies, item video timestamps, and complete voting-calendar documents.')
            page = page.replace('Transcript-verified actions and video timestamps', 'Minutes-checked actions and transcript video timestamps')
            page = page.replace('G.16 was pulled for discussion and then passed 5–0.', 'G.16 was pulled for discussion; the transcript records 5–0 adoption, while the supplied minutes omit an explicit result or vote total.')
            page = page.replace('Pulled for discussion and adopted 5–0 after a discussion of education and enforcement.', 'The transcript records adoption 5–0 after discussion; the supplied minutes record the motion but omit its result and vote total.')
            page = page.replace('<strong>Vote</strong><span>5–0</span>', '<strong>Vote</strong><span>Unanimous in supplied minutes; 5–0 in transcript</span>')
        else:
            marker = '<section aria-labelledby="meeting-video-title">'
            if marker not in page:
                raise ValueError('Missing October 6 meeting-video anchor')
            page = page.replace(marker, START + block + END + marker, 1)
            page = page.replace('Meeting video available · Outcome review in progress', 'Supplied minutes reviewed · Recorded outcomes available')
            page = page.replace('Meeting held · Outcome review in progress', 'Minutes reviewed · Martinez absent')
            page = page.replace('All amounts and actions below are proposals, not approvals.', 'This pre-meeting material preserves the original proposals. Recorded decisions are now documented separately in the minutes review.')
            page = page.replace('The pre-meeting summaries below are retained as proposals; they do not establish what Council approved.', 'The pre-meeting summaries below remain proposals; the separate minutes review records the Council decisions.')
            page = page.replace('October 6, 2026 Beaumont City Council agenda, proposed actions, meeting details, and official supporting documents.', 'October 6, 2026 Beaumont City Council minutes-reviewed decisions, attendance, vote results, and preserved agenda documents.')
        path.write_text(page, encoding='utf-8')
        source_path = DOCS / f'briefings/{date}-sources.html'
        source = source_path.read_text(encoding='utf-8')
        source = re.sub(r'<!-- autumn-minutes-link:start -->.*?<!-- autumn-minutes-link:end -->', '', source, flags=re.S)
        source = source.replace('<div class="agenda-toolbar">', '<!-- autumn-minutes-link:start --><p><a href="' + date + '.html#minutes-review">Read the minutes-checked decisions and source differences</a> · <a href="' + escape(url, quote=True) + '">Supplied minutes (Word original)</a></p><!-- autumn-minutes-link:end --><div class="agenda-toolbar">', 1)
        source_path.write_text(source, encoding='utf-8')

    path = DOCS / 'council-intelligence.html'
    page = path.read_text(encoding='utf-8')
    def update_card(match):
        card = match[0]
        if '<strong>October 6, 2026 City Council Meeting</strong>' in card:
            card = card.replace('Meeting held · Outcome review in progress', 'Minutes reviewed · Martinez absent')
            card = card.replace('The meeting video and official supporting documents are available; motions, votes, and outcomes remain under review.', 'The supplied minutes confirm 4–0 roll-call approvals with Martinez absent; the legislative recap was received by consensus. The final Trevino procurement motion includes a later funding-source budget adjustment.')
        elif '<strong>September 15, 2026 City Council Meeting</strong>' in card:
            card = card.replace('Meeting complete</span>', 'Minutes checked · Source caveats noted</span>')
        return card
    page = re.sub(r'<details class="briefing-card.*?</details>', update_card, page, flags=re.S)
    path.write_text(page, encoding='utf-8')
    path = DOCS / 'council-briefings-2026.html'
    page = path.read_text(encoding='utf-8')
    def update_archive_card(match):
        card = match[0]
        if '<h3>October 6, 2026</h3>' in card:
            card = card.replace('Meeting held · Video available', 'Supplied minutes reviewed').replace('Meeting held · Outcome review in progress', 'Supplied minutes reviewed')
            card = card.replace('Open meeting record and video', 'Open minutes-checked meeting record')
        return card
    page = re.sub(r'<article class="story-card">.*?</article>', update_archive_card, page, flags=re.S)
    path.write_text(page, encoding='utf-8')

    path = DOCS / 'search-index.js'
    prefix = 'window.BI_SEARCH_INDEX = '
    records = json.loads(path.read_text(encoding='utf-8')[len(prefix):].strip().removesuffix(';'))
    for date, meeting in review['meetings'].items():
        url = f'briefings/{date}.html'
        description = f'{meeting["label"]} Council decisions checked against supplied minutes, with attendance, recorded votes and source differences.'
        replacement = dict(title=f'{meeting["label"]} Council Meeting Record', url=url, description=description, category='Council Intelligence',
                           text=description + ' ' + ' '.join(item['summary'] + ' ' + item['limit'] for item in meeting['items']) + ' ' + ' '.join(issue['text'] for issue in meeting['discrepancies']))
        found = False
        for record in records:
            for row in record.get('value', []) if 'value' in record else [record]:
                if row.get('url') == url:
                    row.update(replacement)
                    found = True
        if not found:
            records.append(replacement)
    path.write_text(prefix + json.dumps(records, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
    print('Published September 15 and October 6 minutes review')


if __name__ == '__main__':
    build()
