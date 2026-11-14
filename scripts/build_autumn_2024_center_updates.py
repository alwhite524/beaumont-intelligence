"""Publish the reviewed autumn 2024 packet findings on centers and service routes."""
import json
import re
from html import escape as esc
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
DATA = ROOT / 'data/council/2024-autumn-center-review.json'
KEY = 'autumn-2024-center-review'
PAGE = 'autumn-2024-center-review.html'
FEATURED = {
    'budget-records.html': ['quarterly-budget', 'fy2024-audit', 'financial-policies', 'ia17d-bonds'],
    'land-policy.html': ['dif-continuance', 'truck-viability', 'potrero-benefit', 'tumf-update'],
    'downtown-revitalization.html': ['business-incentives', 'facade-960', 'downtown-assessments', 'director-positions'],
}
AREAS = {
    'public-works-mobility': 'Public Works & Mobility',
    'public-safety': 'Public Safety',
    'growth-community-development': 'Growth & Community Development',
    'economic-development': 'Economic Development',
    'parks-community-services': 'Parks & Community Services',
    'finance-government': 'Finance & City Government',
    'utilities-environment': 'Utilities & Environment',
}


def replace(path, body, near_top=False):
    text = path.read_text(encoding='utf-8')
    block = f'<!-- {KEY}:start -->\n{body}\n<!-- {KEY}:end -->'
    pattern = rf'<!-- {KEY}:start -->.*?<!-- {KEY}:end -->'
    if re.search(pattern, text, re.S):
        text = re.sub(pattern, lambda _: block, text, flags=re.S)
    elif near_top:
        main = text.index('<main')
        pos = text.index('</section>', main) + len('</section>')
        text = text[:pos] + '\n' + block + text[pos:]
    else:
        assert text.count('</main>') == 1, path
        text = text.replace('</main>', block + '\n</main>')
    css = '../' if path.parent != DOCS else ''
    css += 'autumn-2024-centers.css?v=20261113'
    if 'autumn-2024-centers.css' not in text:
        text = text.replace('</head>', f'<link rel="stylesheet" href="{css}">\n</head>')
    path.write_text(text, encoding='utf-8')


def card(row, packets, compact=False):
    day = row['date']
    packet = packets[day]
    sources = [d for d in packet['documents'] if d['item'] in row['items']]
    minutes = 'https://documents.beaumontintelligence.com/official-documents/' + day + '/council-minutes.pdf'
    viewer = 'documents/viewer.html?' + urlencode(dict(url=minutes, page=row['minutesPages'][0], title=day+' Council minutes'))
    links = ' · '.join(f'<a href="briefings/{day}-sources.html#item-{key.lower().replace(".", "-")}">Agenda {esc(key)} and attachments</a>' for key in row['items'])
    links += f' · <a href="{esc(viewer, quote=True)}">Minutes, page {row["minutesPages"][0]}</a>'
    if sources:
        d = sources[0]
        source_view = 'documents/viewer.html?' + urlencode(dict(url=d['archiveUrl'], title=d['title']))
        links += f' · <a href="{esc(source_view, quote=True)}">Staff report · packet pages {d["packet_page_start"]}–{d["packet_page_end"]}</a>'
    detail = f'<p><strong>Evidence limit / next records:</strong> {esc(row["limit"])}</p>'
    more = f'<p><a href="{PAGE}#{row["id"]}">Full finding and evidence limits →</a></p>' if compact else ''
    return f'<article class="story-card" id="{row["id"]}"><div class="eyebrow">{day} · Items {esc(", ".join(row["items"]))}</div><h3>{esc(row["title"])}</h3><p><strong>{esc(row["status"])}</strong></p><p>{esc(row["summary"])}</p>{detail}<p>{links}</p>{more}</article>'


def section(title, content, id='autumn-2024-findings'):
    return f'<section class="section compact alt" id="{id}"><div class="wrap"><h2>{esc(title)}</h2>{content}</div></section>'


def main():
    data = json.loads(DATA.read_text(encoding='utf-8'))
    packets = {day: json.loads((ROOT/f'data/council/{day}-agenda.json').read_text(encoding='utf-8')) for day in data['dates']}
    rows = data['findings']
    # Assert source references before rendering; a missing item must never silently disappear.
    for r in rows:
        assert set(r['items']) <= {i['item'] for i in packets[r['date']]['items']}, r['id']
        assert all((DOCS/p).exists() for p in r['pages']), r['id']
    intro = f'<p>Historical record review · {data["reviewedOn"]}. Five October–December 2024 packets screened; {len(rows)} findings checked against collected minutes and linked packet records. These findings describe the record at the time and do not replace current status, payment records or completion evidence.</p>'
    pages = sorted({page for r in rows for page in r['pages']})
    for page in pages:
        selected = [r for r in rows if page in r['pages']]
        overview = not any(token in page for token in ['-funding.', '-evidence.', '-history.', '-design.', '-schedule.', '-council-actions.', '-business.', '-facilities.', '-staffing.'])
        shown = selected[:4] if overview else selected
        if page in FEATURED:
            shown = [next(r for r in selected if r['id']=='autumn-2024-'+slug) for slug in FEATURED[page]]
        content = intro + '<div class="story-grid archive-review-grid">' + ''.join(card(r, packets, compact=overview) for r in shown) + '</div>'
        content += f'<p><a class="text-link" href="{PAGE}">Review all {len(rows)} findings and service-area routes →</a></p>'
        if '/' in page:
            content = re.sub(r'href="(?!https?://|#)([^"]+)"', r'href="../\1"', content)
        replace(DOCS/page, section('From the October–December 2024 agendas', content), near_top=overview)

    table = '<table><thead><tr><th>Meeting</th><th>Agenda entries screened</th><th>Supporting documents</th><th>Findings</th></tr></thead><tbody>'
    for day, packet in packets.items():
        table += f'<tr><td><a href="briefings/{day}-sources.html">{day}</a></td><td>{len(packet["items"])}</td><td>{len(packet["documents"])}</td><td>{sum(r["date"]==day for r in rows)}</td></tr>'
    table += '</tbody></table>'
    coverage = '<p>Every agenda entry was screened for relevance. Closed-session listings do not establish action; presentations, routine warrants and minutes approvals are retained in the interactive agendas. Findings below are a selected substantive review, not an audit of all 260 attachments. Missing vote tallies and document discrepancies are identified explicitly.</p>'
    groups = ''
    directory = intro + '<div class="feature-grid">'
    for area, label in AREAS.items():
        selected = [r for r in rows if area in r['areas']]
        directory += f'<article class="feature"><h3>{esc(label)}</h3><p>{len(selected)} dated findings</p><a href="{PAGE}#{area}">Review decisions and records →</a></article>'
        groups += section(label, '<ul>' + ''.join(f'<li><a href="#{r["id"]}">{r["date"]} · {esc(r["title"])}</a> — {esc(r["status"])}</li>' for r in selected) + '</ul>', area)
    directory += '</div><p>Cross-listed findings count once in the review total.</p>'
    replace(DOCS/'intelligence-centers.html', section('Newly reviewed 2024 Council records', directory))
    # Keep one full finding per stable anchor; area routes cross-reference it.
    groups += section('Findings and primary evidence', '<div class="story-grid archive-review-grid">' + ''.join(card(r, packets) for r in rows) + '</div>', 'findings')
    template = (DOCS/'budget-records.html').read_text(encoding='utf-8')
    header = template[template.index('<header'):template.index('</header>')+len('</header>')]
    body = '<section class="section compact"><div class="wrap"><div class="eyebrow">Historical Council review</div><h1>October–December 2024: findings by service area</h1>' + intro + coverage + table + '<nav aria-label="Service areas">' + ' · '.join(f'<a href="#{a}">{esc(label)}</a>' for a,label in AREAS.items()) + '</nav></div></section>'
    html = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Dated findings from five 2024 Council agendas, with decisions, source records and evidence limits by service area."><title>October–December 2024 Council Findings | Beaumont Intelligence</title><link rel="stylesheet" href="styles.css"><link rel="icon" href="favicon.png"></head><body><a class="skip-link" href="#main">Skip to content</a>' + header + '<main id="main">' + body + groups + '</main><footer class="footer"><div class="wrap"><a href="intelligence-centers.html">Intelligence Centers</a> · <a href="council-intelligence.html#autumn-2024-agendas">All five interactive agendas</a></div></footer><script src="app.js"></script></body></html>\n'
    html = html.replace('</head>', '<link rel="stylesheet" href="autumn-2024-centers.css?v=20261113"></head>')
    (DOCS/PAGE).write_text(html, encoding='utf-8')
    for day in data['dates']:
        selected = [r for r in rows if r['date']==day]
        related = f'<p>{len(selected)} findings from this meeting connect the packet to the relevant centers, with minutes-based dispositions and evidence limits.</p><ul>'
        related += ''.join(f'<li><a href="../{PAGE}#{r["id"]}">{esc(r["title"])}</a></li>' for r in selected) + '</ul>'
        replace(DOCS/f'briefings/{day}-sources.html', section('Related Intelligence Center findings', related))
    replace(DOCS/'council-intelligence.html', section('Review the newly added 2024 records by service area', intro + f'<p><a class="btn" href="{PAGE}">Open findings and center updates →</a></p>'))
    search = DOCS/'search-index.js'
    prefix = 'window.BI_SEARCH_INDEX = '
    records = json.loads(search.read_text(encoding='utf-8')[len(prefix):].strip().removesuffix(';'))
    records = [r for r in records if r.get('sourceReview') != '2024-autumn-centers']
    for r in rows:
        records.append(dict(title=r['title'], url=PAGE+'#'+r['id'], category='Intelligence Centers', description=r['summary'], text=r['date']+' '+r['status']+' '+r['summary']+' '+r['limit'], sourceReview='2024-autumn-centers'))
    search.write_text(prefix+json.dumps(records, ensure_ascii=False, separators=(',', ':'))+';\n', encoding='utf-8')
    print(f'Published {len(rows)} historical findings on {len(pages)} center pages and seven service-area routes.')


if __name__ == '__main__':
    main()
