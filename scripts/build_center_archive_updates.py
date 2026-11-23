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
    centers = [('budget', 'budget-records.html'), ('police', 'police.html'), ('stewart-park', 'stewart-park.html'), ('downtown', 'downtown-revitalization.html'), ('animal-control', 'animal-control.html'), ('potrero-interchange', 'potrero-interchange.html'), ('pennsylvania-grade-separation', 'pennsylvania-grade-separation.html')]
    for center, page in centers:
        cards = []
        for r in sorted(findings, key=lambda r: (r['date'], r['item']), reverse=True):
            if r['center'] != center or r['date'] not in review:
                continue
            cards.append(f'<article class="story-card"><div class="eyebrow">{r["date"]} · Item {escape(r["item"])}</div><h3>{escape(r["title"])}</h3><p>{escape(r["summary"])}</p><p><strong>Evidence limit:</strong> {escape(r["limits"])}</p><a href="{r["page"]}#{r["id"]}">Review decision and evidence →</a></article>')
        publish(page, '<section class="section compact alt" id="early-2022-evidence"><div class="wrap"><h2>From the Council archive</h2><p>Historical findings from the collected 2022 and 2025 meeting packets. These decisions describe the record at the time, not current project status.</p><div class="story-grid">' + ''.join(cards) + '</div></div></section>')

    print(f'Updated {len(centers)} center landing pages.')


if __name__ == '__main__':
    main()
