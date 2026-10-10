"""Publish dated Council findings from the reviewed source dataset."""
import json
import re
from html import escape
from pathlib import Path
from urllib.parse import quote
from minutes_selection import preferred_minutes

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
RECORDS = json.loads((ROOT / 'data/council/recent-center-findings.json').read_text(encoding='utf-8'))['records']
MINUTES = preferred_minutes(json.loads((ROOT / 'data/council/minutes-register.json').read_text(encoding='utf-8'))['documents'])
START = '<!-- recent-center-findings:start -->'
END = '<!-- recent-center-findings:end -->'


def render_findings(page):
    records = [r for r in RECORDS if r['page'] == page]
    if not records:
        return ''
    cards = []
    for r in records:
        candidates = [m for m in MINUTES if m.get('date') == r['date']]
        minute = next((m for m in candidates if m.get('kind') == 'regular'), candidates[0])
        url = minute['url']
        if url.endswith('.pdf'):
            url = 'viewer.html?url=' + quote(url, safe='')
        label = 'Minutes (Word)' if minute['url'].endswith('.docx') else 'Minutes'
        links = f'<a href="{escape(url, quote=True)}">{label}</a>'
        if r.get('videoUrl'):
            links += f' · <a href="{escape(r["videoUrl"], quote=True)}" target="_blank" rel="noopener">' + ('Video at discussion' if '&t=' in r['videoUrl'] else 'Full meeting video') + '</a>'
        if r.get('agendaUrl'):
            links += f' · <a href="{escape(r["agendaUrl"], quote=True)}">Agenda and supporting documents</a>'
        if r['transcript']:
            transcript_label = 'Transcript' if r.get('agendaUrl') else 'Supplied transcript'
            transcript_url = ('transcripts/reader.html?date=' + r['date']) if r.get('agendaUrl') and r['date'].startswith('2022-') else 'transcripts/' + r['transcript']
            links += f' · <a href="{escape(transcript_url, quote=True)}">{transcript_label}</a>'
        cards.append(f'<article class="story-card" id="{r["id"]}"><div class="eyebrow">{r["date"]} · Item {escape(r["item"])}</div><h3>{escape(r["title"])}</h3><p>{escape(r["summary"])}</p><p><strong>Evidence limit:</strong> {escape(r["limits"])}</p><p>{links}</p></article>')
    return START + '\n<section class="section compact alt" id="recent-council-findings"><div class="wrap"><div class="section-heading"><div><div class="eyebrow">Additional Council evidence</div><h2>Decisions and planning discussions</h2></div></div><p class="source-note">These dated findings use the linked minutes and, where available, supplied transcripts. Transcript timestamps are navigation aids; automatic transcription can misidentify names and numbers. Video playback has not been independently checked. Proposals and forecasts remain distinct from adopted budgets, payments and completed work.</p><div class="story-grid">' + '\n'.join(cards) + '</div></div></section>\n' + END


def main():
    for page in sorted({r['page'] for r in RECORDS}):
        path = DOCS / page
        html = path.read_text(encoding='utf-8')
        html = re.sub(re.escape(START) + r'.*?' + re.escape(END) + r'\n?', '', html, flags=re.S)
        assert html.count('</main>') == 1, page
        path.write_text(html.replace('</main>', render_findings(page) + '\n</main>'), encoding='utf-8')
    print(f'Published {len(RECORDS)} findings across {len({r["center"] for r in RECORDS})} centers.')


if __name__ == '__main__':
    main()
