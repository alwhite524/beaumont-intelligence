"""Publish the reviewed October 20 transcript and November meeting placeholder.

Run after build_2026_10_20_agenda.py to retain the original proposal review.
"""
import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
DATE = '2026-10-20'
START = '<!-- october-20-outcomes:start -->'
END = '<!-- october-20-outcomes:end -->'


def build():
    review = json.loads((ROOT / f'data/council/{DATE}-outcomes.json').read_text(encoding='utf-8'))
    next_meeting = review['nextMeeting']
    video = review['videoUrl']
    transcript = f'../transcripts/reader.html?date={DATE}'
    cards = []
    for item in review['items']:
        seconds = item['videoSeconds']
        timestamp = f'{seconds//3600}:{seconds%3600//60:02}:{seconds%60:02}'
        vote = f' · Transcript roll call {item["vote"]}' if item['vote'] else ''
        cards.append(f'<article class="card" id="outcome-{escape(item["item"], quote=True)}">'
                     f'<div class="meta">{escape(item["item"] + vote)}</div><h3>{escape(item["title"])}</h3>'
                     f'<p>{escape(item["summary"])}</p><p class="source-note"><strong>Evidence limit:</strong> {escape(item["evidenceLimit"])}</p>'
                     f'<p><a href="{escape(video, quote=True)}&amp;t={seconds}s" target="_blank" rel="noopener">Video at {timestamp} ↗</a>'
                     f' · <a href="{transcript}">Search the transcript</a></p></article>')
    section = (START + '<section id="meeting-outcomes" aria-labelledby="outcomes-title"><h2 id="outcomes-title">After the meeting: transcript-based outcomes</h2>'
               f'<p class="source-note">Reviewed October 24, 2026. {escape(review["evidence"])}</p>'
               '<div class="status-actions">'
               f'<a class="btn secondary" href="{transcript}">Read and search the transcript</a></div>'
               '<iframe style="display:block;width:100%;aspect-ratio:16/9;border:0" src="https://www.youtube-nocookie.com/embed/UVsGQHIcdkA" '
               'title="October 20, 2026 Beaumont City Council meeting" loading="lazy" allow="accelerometer; autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>'
               + ''.join(cards) + '</section>' + END)
    path = DOCS / f'briefings/{DATE}.html'
    page = path.read_text(encoding='utf-8')
    page = re.sub(re.escape(START) + '.*?' + re.escape(END), '', page, flags=re.S)
    page = page.replace('<h2>Preserved pre-meeting briefing and document checks</h2>', '')
    page = page.replace('October 20, 2026 Council Agenda Briefing', 'October 20, 2026 Council Meeting Record')
    page = page.replace('October 20, 2026 Beaumont City Council agenda, proposed actions, meeting details, and official supporting documents.', 'October 20, 2026 Beaumont City Council transcript-based outcomes, roll calls, video timestamps, and preserved agenda briefing.')
    page = page.replace('Short-term rentals, a new police station services agreement, downtown improvements, an $80,000 golf sponsorship request, and a proposed $978,037.43 technology renewal.', 'Police-station Phase I services, short-term rental first reading, golf sponsorship, downtown design, Highland Springs improvements, and technology renewal. The transcript-based record is separate from the preserved pre-meeting analysis below.')
    page = page.replace('<strong>Council agenda briefing</strong><span>Upcoming meeting · Proposed actions',
                        '<strong>Council meeting record</strong><span>Transcript reviewed · Approved minutes pending')
    page = page.replace('<div class="eyebrow">Pre-meeting briefing</div>', '<div class="eyebrow">Meeting record and preserved pre-meeting briefing</div>')
    page = page.replace('Upcoming · Council action pending', 'Meeting held · Transcript-based outcomes available')
    page = page.replace('Council decisions will be recorded separately after the meeting.', 'Transcript-based outcomes are recorded separately above. This pre-meeting analysis remains preserved for comparison.')
    # Keep the October 16 review intact below the new evidence section.
    marker = '<p class="source-note">Prepared October 16'
    if marker not in page:
        raise ValueError('Missing preserved October 16 document review')
    page = page.replace(marker, section + '<h2>Preserved pre-meeting briefing and document checks</h2>' + marker, 1)
    page = page.replace('<h2>Attend and comment</h2>', '<h2>Participation instructions from the published agenda</h2>')
    path.write_text(page, encoding='utf-8')

    path = ROOT / f'data/council/{DATE}-agenda.json'
    agenda = json.loads(path.read_text(encoding='utf-8'))
    agenda.update(meetingStatus='held', outcomeSource=f'data/council/{DATE}-outcomes.json', transcriptReviewedOn=review['reviewedOn'])
    path.write_text(json.dumps(agenda, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    path = DOCS / f'briefings/{DATE}-sources.html'
    page = path.read_text(encoding='utf-8').replace('Upcoming interactive agenda', 'Archived interactive agenda')
    page = page.replace('Proposed actions await Council decisions.', 'Meeting held October 20. <a href="2026-10-20.html#meeting-outcomes">Read transcript-based outcomes</a> · <a href="../transcripts/reader.html?date=2026-10-20">Search the meeting transcript</a>. The archived agenda and packet retain the original proposals.')
    path.write_text(page, encoding='utf-8')

    placeholder = ('<div class="eyebrow">Upcoming Council meeting · Agenda pending</div><h1>November 17, 2026 City Council meeting</h1>'
                   '<p class="lead-copy">This is a placeholder for the next regular meeting. A briefing and interactive agenda will be added after the City publishes the meeting materials.</p>'
                   '<span class="pill pending">Agenda and supporting documents not yet collected</span>'
                   '<p><strong>Tuesday, November 17, 2026 · Regular meeting 6:00 PM</strong><br>550 E. Sixth Street, Beaumont, CA</p>'
                   '<p>A closed-session time has not been confirmed for this meeting.</p>'
                   f'<p><strong>Schedule source:</strong> {escape(next_meeting["note"])}</p>'
                   f'<p><a href="{escape(next_meeting["scheduleSource"], quote=True)}">October 20 official City agenda</a>'
                   ' · <a href="https://pub-beaumont.escribemeetings.com/">Check the City meeting portal</a>'
                   ' · <a href="https://www.youtube.com/watch?v=UVsGQHIcdkA&amp;t=12600s" target="_blank" rel="noopener">October 20 adjournment and schedule reminder ↗</a></p>'
                   '<h2>What is available now</h2><p>No November 17 agenda topics, proposed awards, or votes are represented as confirmed. The published notice will control meeting details.</p>'
                   '<div class="status-actions"><a class="btn" href="2026-10-20.html">Review the October 20 meeting</a>'
                   '<a class="btn secondary" href="../council-intelligence.html">Council Intelligence</a></div>')
    header = re.search(r'<header class="app-header">.*?</header>', page, re.S)
    header = header.group(0) if header else re.search(r'<header class="app-header">.*?</header>', (DOCS / f'briefings/{DATE}.html').read_text(encoding='utf-8'), re.S).group(0)
    (DOCS / 'briefings/2026-11-17.html').write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>November 17, 2026 Council Meeting Placeholder | Beaumont Intelligence</title>'
        '<meta name="description" content="Next regular Beaumont City Council meeting: November 17, 2026. Agenda and briefing pending publication.">'
        '<link rel="stylesheet" href="../styles.css"><script defer src="../app.js"></script></head><body data-page="briefing">'
        '<a class="skip-link" href="#main">Skip to content</a>' + header + '<main id="main"><section class="section"><div class="wrap narrow">'
        + placeholder + '</div></section></main></body></html>', encoding='utf-8')

    actions = '<div class="status-actions"><a class="btn" href="briefings/2026-11-17.html">View November 17 placeholder</a><a class="text-link" href="briefings/2026-10-20.html#meeting-outcomes">October 20 outcomes &amp; transcript →</a></div>'
    deck = 'The next regular meeting is November 17. Agenda materials and the briefing will be added when published. There is no regular meeting on November 3.'
    path = DOCS / 'index.html'
    page = path.read_text(encoding='utf-8')
    # The older Council Briefings feature has its own latest-meeting label/link.
    page = re.sub(r'Latest meeting · [^<]+', 'Latest meeting · October 20, 2026', page)
    page = re.sub(r'href="briefings/\d{4}-\d{2}-\d{2}\.html">Open [^<]+ meeting record →',
                  'href="briefings/2026-10-20.html">Open October 20 meeting record →', page)
    page = re.sub(r'<section aria-labelledby="latest-council-title".*?</section>',
                  '<section aria-labelledby="latest-council-title" class="council-feature" data-home-meeting-mode="upcoming" data-next-regular-date="2026-11-17"><div class="wrap"><article class="council-feature-card"><div class="council-feature-copy"><div class="eyebrow">Upcoming Council meeting</div><h2 id="latest-council-title">November 17 City Council meeting</h2><p class="council-deck">' + deck + '</p>' + actions + '</div><aside aria-label="Meeting schedule" class="council-feature-meta"><span class="pill pending">Agenda pending</span><p><strong>November 17, 2026</strong></p><p>Regular meeting · 6:00 PM</p><p class="meeting-schedule-note">550 E. Sixth Street, Beaumont, CA. Closed-session time unconfirmed; details remain subject to the City notice.</p></aside></article></div></section>', page, count=1, flags=re.S)
    page = page.replace('<!-- Regular Council meetings are scheduled for the first and third Tuesdays. Keep this card on the next scheduled date; add briefing and agenda links when those records are published. -->', '<!-- Use the next meeting named in the official agenda; November 3 is canceled. Add agenda links when published. -->')
    path.write_text(page, encoding='utf-8')

    path = DOCS / 'council-intelligence.html'
    page = path.read_text(encoding='utf-8')
    page = re.sub(r'<section class="section compact alt"><div class="wrap"><div class="eyebrow">Upcoming meeting.*?</section>',
                  '<section class="section compact alt"><div class="wrap"><div class="eyebrow">Upcoming meeting · Agenda pending</div><h2>November 17, 2026</h2><p>Regular meeting 6:00 PM · Closed-session time unconfirmed</p><p>' + deck + '</p>' + actions + '</div></section>', page, count=1, flags=re.S)
    card = '<details class="briefing-card council-meeting-card featured" open><summary><span><strong>October 20, 2026 City Council Meeting</strong><small>Short-term rentals, police station, golf sponsorship, downtown design, Highland Springs, and City technology</small></span><i aria-hidden="true"></i></summary><div class="briefing-card-body"><span class="pill">Meeting held · Transcript reviewed · Minutes pending</span><p>Council introduced short-term rental regulations, authorized police-station Phase I services, approved the golf sponsorship 4–1, and directed downtown design. Read the transcript-based outcomes and preserved pre-meeting analysis.</p><div class="status-actions"><a class="btn" href="briefings/2026-10-20.html">Open October 20 meeting record</a><a class="text-link" href="transcripts/reader.html?date=2026-10-20">Search transcript →</a></div></div></details>'
    if '<strong>October 20, 2026 City Council Meeting</strong>' not in page:
        page = page.replace('<details class="briefing-card council-meeting-card featured" open>', card + '\n<details class="briefing-card council-meeting-card featured" open>', 1)
    page = page.replace('href="briefings/2026-09-15.html">Latest Briefing', 'href="briefings/2026-10-20.html">Latest Meeting Record')
    path.write_text(page, encoding='utf-8')
    path = DOCS / 'council-briefings-2026.html'
    page = path.read_text(encoding='utf-8')
    page = re.sub(r'<article class="story-card"><div class="pill pending">Upcoming · Agenda available</div><h3>October 20, 2026</h3>.*?</article>',
                  '<article class="story-card"><div class="pill">Meeting held · Transcript reviewed</div><h3>October 20, 2026</h3><p>Police station Phase I, short-term rentals, downtown design, sponsorship, street work, and technology renewal. Transcript-based outcomes and the original briefing remain available.</p><a class="btn" href="briefings/2026-10-20.html">Open meeting record</a></article>', page, count=1, flags=re.S)
    if '<h3>November 17, 2026</h3>' not in page:
        page = page.replace('<div class="story-grid">', '<div class="story-grid"><article class="story-card"><div class="pill pending">Upcoming · Agenda pending</div><h3>November 17, 2026</h3><p>Regular meeting 6:00 PM. No November 3 meeting. Agenda topics and closed-session time remain unconfirmed.</p><a class="btn" href="briefings/2026-11-17.html">View meeting placeholder</a></article>', 1)
    path.write_text(page, encoding='utf-8')
    # Refresh these search destinations without disturbing the existing index format.
    path = DOCS / 'search-index.js'
    source = path.read_text(encoding='utf-8')
    prefix = 'window.BI_SEARCH_INDEX = '
    records = json.loads(source[len(prefix):].strip().removesuffix(';'))
    for url, title, description in [
        ('briefings/2026-10-20.html', 'October 20, 2026 Council Meeting Record', 'Transcript-based outcomes, roll calls, video timestamps, and preserved pre-meeting document review.'),
        ('briefings/2026-11-17.html', 'November 17, 2026 Council Meeting Placeholder', deck),
    ]:
        replacement = dict(title=title, url=url, description=description, category='Council Intelligence', text=description + ' ' + ' '.join(item['summary'] for item in review['items']) if '10-20' in url else description)
        found = False
        for record in records:
            for row in record.get('value', []) if 'value' in record else [record]:
                if row.get('url') == url:
                    row.update(replacement)
                    found = True
        if not found:
            records.append(replacement)
    path.write_text(prefix + json.dumps(records, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
    print('Published October 20 transcript outcomes and November 17 placeholder')


if __name__ == '__main__':
    build()
