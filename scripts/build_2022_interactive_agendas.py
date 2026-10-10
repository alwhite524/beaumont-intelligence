"""Render packet-based historical agendas without conflating recommendations and outcomes."""
import json
from datetime import date
from html import escape as esc
from pathlib import Path
from historical_meeting_reviews import load_reviews

ROOT = Path(__file__).resolve().parents[1]
DATES = ['2022-01-04','2022-01-18','2022-02-01','2022-02-15','2022-03-01','2022-03-15']

def button(url, title):
    return f'<button class="btn small secondary" data-document="{esc(url, quote=True)}" data-title="{esc(title, quote=True)}">{esc(title)}</button>'

def main():
    videos = {v['date']: v for v in json.loads((ROOT/'data/council/video-links.json').read_text(encoding='utf-8'))['videos']}
    reviews = load_reviews()
    for day in sorted(reviews):
        data = json.loads((ROOT/f'data/council/{day}-agenda.json').read_text(encoding='utf-8'))
        review = reviews[day]
        label = date.fromisoformat(day).strftime('%B %d, %Y').replace(' 0',' ')
        video = videos.get(day, {}).get('url')
        transcript = ROOT/f'docs/transcripts/{day}-city-council-transcript.txt'
        actions = button(data['agendaUrl'], 'View published agenda') + button(data['packetArchiveUrl'], 'View full packet') + button(review['minutesUrl'], 'View minutes')
        if video:
            actions += f'<a class="btn small" href="{esc(video)}" target="_blank" rel="noopener">Watch meeting</a>'
        if transcript.exists():
            actions += f'<a class="btn small" href="../transcripts/reader.html?date={day}">Read searchable transcript</a>'
        groups = []
        for section in ['Closed Session','Presentation','Public Hearing','Action','Reports','Consent']:
            rows = []
            for item in (x for x in data['items'] if x['section'] == section):
                number = item['item']
                record = review['items'].get(number, {})
                links = ''.join(button(d['archiveUrl'], d['title']) + f'<small>Packet pp. {d["packet_page_start"]}-{d["packet_page_end"]}</small>' for d in data['documents'] if d['item'] == number)
                rec = f'<p><strong>Published recommendation:</strong> {esc(item["recommendation"])}</p>' if item['recommendation'] else ''
                outcome = f'<p><strong>Minutes record:</strong> {esc(record.get("minutesRecord", "Presentation; no action recorded."))}</p>'
                if record.get('transcriptRecord'):
                    outcome += f'<p><strong>Caption evidence:</strong> {esc(record["transcriptRecord"])}</p>'
                if record.get('relatedServiceAreas'):
                    outcome += '<p>Related service areas: ' + ' · '.join(f'<a href="../intelligence-centers.html#{area["id"]}">{esc(area["label"])}</a>' for area in record['relatedServiceAreas']) + '</p>'
                if record.get('timestampSeconds') is not None and video:
                    links += f'<a class="btn small" href="{esc(video)}&amp;t={record["timestampSeconds"]}s" target="_blank" rel="noopener">Watch discussion</a>'
                rows.append(f'<details class="agenda-record" id="item-{number}" data-section="{section}"><summary><b>{number}</b><strong>{esc(item["title"])}</strong></summary><div class="agenda-body">{rec}{outcome}<div class="document-list">{links}</div></div></details>')
            if rows:
                groups.append(f'<section class="agenda-section"><h2>{section}</h2>{"".join(rows)}</section>')
        transcript_note = ('Machine-generated transcript available; names, numbers and quotations require checking against the recording.' if transcript.exists() else 'No transcript collected for this meeting.')
        audit = data.get('audit', {})
        audit_text = (f'Official HTML attachment audit: {audit["linkedDocuments"]} of {audit["expectedDocuments"]} City-listed attachments matched to the supplied packet. Original City URLs are retained in the source dataset.' if audit.get('officialHtmlAuditComplete') else f'All {len(data["documents"])} bookmarked supporting documents are linked. This is a packet-based inventory; the City\'s historical online attachment list has not been independently audited.')
        note = esc(review.get('note','') + ' ' + review.get('timestampNote',''))
        html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{label} Interactive Agenda | Beaumont Intelligence</title><link rel="stylesheet" href="../styles.css"><link rel="stylesheet" href="historical-agenda.css"></head><body><a class="skip-link" href="#main">Skip to content</a><header class="app-header"><div class="wrap header-row"><a class="brand" href="../index.html">BEAUMONT INTELLIGENCE</a><a href="../council-meeting-sources.html">Meeting sources</a></div></header><main id="main" class="section"><div class="wrap narrow"><div class="eyebrow">{label} · Archived meeting</div><h1>Interactive Council agenda</h1><p>Browse {len(data['items'])} numbered agenda items and {len(data['documents'])} supporting documents. The published agenda includes closed-session matters and meeting procedures.</p><div class="status-actions">{actions}</div><p class="source-note">Source: {esc(data['sourceFilename'])} ({data['packetPages']} pages). {audit_text} Consent is displayed last for browsing. Recommendations describe proposed actions; minutes records describe subsequent decisions. {transcript_note} {note}</p><div class="agenda-toolbar"><label>Search agenda<input type="search" id="agenda-search" placeholder="Search topics, recommendations or outcomes"></label><label>Section<select id="agenda-filter"><option value="all">All sections</option><option>Closed Session</option><option>Presentation</option><option>Public Hearing</option><option>Action</option><option>Reports</option><option>Consent</option></select></label></div><p id="agenda-count" aria-live="polite"></p>{''.join(groups)}</div></main><dialog id="document-dialog" class="viewer-dialog" aria-labelledby="document-title"><header><strong id="document-title">Document viewer</strong><button class="btn small" id="close-document">Close</button></header><iframe id="document-frame" title="Beaumont Intelligence document viewer"></iframe></dialog><script src="2022-agenda.js"></script></body></html>'''
        (ROOT/f'docs/briefings/{day}-sources.html').write_text(html, encoding='utf-8')
        print(day, len(data['items']), 'items')

if __name__ == '__main__':
    main()
