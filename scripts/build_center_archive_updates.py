"""Surface reviewed early-2022 evidence on center entry pages."""
import json
import re
from html import escape
from pathlib import Path
from historical_meeting_reviews import load_reviews

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
START = '<!-- center-archive-updates:start -->'
END = '<!-- center-archive-updates:end -->'


def publish(page, content):
    path = DOCS / page
    html = path.read_text(encoding='utf-8')
    html = re.sub(re.escape(START) + r'.*?' + re.escape(END) + r'\n?', '', html, flags=re.S)
    assert html.count('</main>') == 1, page
    html = html.replace('</main>', START + '\n' + content + '\n' + END + '\n</main>')
    path.write_text(html, encoding='utf-8')


def main():
    findings = json.loads((ROOT / 'data/council/recent-center-findings.json').read_text(encoding='utf-8'))['records']
    review = load_reviews()
    centers = [('budget', 'budget.html'), ('police', 'police.html'), ('stewart-park', 'stewart-park.html'), ('downtown', 'downtown-revitalization.html'), ('animal-control', 'animal-control.html'), ('potrero-interchange', 'potrero-interchange.html'), ('pennsylvania-grade-separation', 'pennsylvania-grade-separation.html')]
    for center, page in centers:
        cards = []
        for r in sorted(findings, key=lambda r: (r['date'], r['item']), reverse=True):
            if r['center'] != center or r['date'] not in review:
                continue
            cards.append(f'<article class="story-card"><div class="eyebrow">{r["date"]} · Item {escape(r["item"])}</div><h3>{escape(r["title"])}</h3><p>{escape(r["summary"])}</p><p><strong>Evidence limit:</strong> {escape(r["limits"])}</p><a href="{r["page"]}#{r["id"]}">Review decision and evidence →</a></article>')
        publish(page, '<section class="section compact alt" id="early-2022-evidence"><div class="wrap"><h2>From the Council archive</h2><p>Historical findings from the collected 2022 and 2025 meeting packets. These decisions describe the record at the time, not current project status.</p><div class="story-grid">' + ''.join(cards) + '</div></div></section>')

    groups = {}
    for date, meeting in sorted(review.items()):
        agenda = json.loads((ROOT / f'data/council/{date}-agenda.json').read_text(encoding='utf-8'))
        for item in agenda['items']:
            for area in meeting['items'][item['item']].get('relatedServiceAreas', []):
                group = groups.setdefault(area['id'], {'label': area['label'], 'links': []})
                group['links'].append(f'<li><a href="briefings/{date}-sources.html#item-{item["item"]}">{date} · Item {escape(item["item"])}: {escape(item["title"])}</a></li>')
    sections = []
    for key, group in groups.items():
        sections.append(f'<details id="archive-{key}"><summary>{escape(group["label"])} · {len(group["links"])} agenda entries</summary><ul>' + ''.join(group['links']) + '</ul></details>')
    publish('intelligence-centers.html', f'<section class="section compact alt" id="early-2022-evidence"><div class="wrap"><h2>Explore historical Council evidence</h2><p>{len(review)} collected agendas organized by service area. Open an item for its published recommendation, separately recorded outcome, supporting documents in the BI viewer, and available transcript or video. Items can relate to more than one area; a listing does not imply approval.</p>' + ''.join(sections) + '</div></section>')
    print(f'Updated {len(centers)} center landing pages and {len(groups)} service-area evidence groups.')


if __name__ == '__main__':
    main()
