"""Build an agenda-led historical meeting page; outcomes are not inferred."""
import json
from pathlib import Path
from html import escape as esc

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/council/2015-11-03.json'
DOCS = ROOT / 'docs'

def main():
    data = json.loads(DATA.read_text(encoding='utf-8'))
    sections = []
    for section in ['Closed Session', 'Opening and Reports', 'Action', 'Additional Records', 'Consent']:
        rows = []
        for item in data['items']:
            if item['section'] != section:
                continue
            links = ''.join(f'<p><button class="btn small" data-document="{esc(d["url"], quote=True)}">View {esc(d["title"])}</button> <a href="{esc(d["url"], quote=True)}" target="_blank" rel="noopener">Open official record ↗</a></p>' for d in item['documents'])
            rows.append(f'<details class="agenda-record" id="{item["id"]}"><summary>{esc(item["item"])} · {esc(item["title"])}</summary><div class="agenda-documents"><p>{esc(item["notes"])}</p>{links or "<p>No separate supporting document located; consult the official agenda.</p>"}<p><small>Outcome and video timestamp not yet verified.</small></p></div></details>')
        sections.append(f'<section class="agenda-section"><h2>{section}</h2>{"".join(rows)}</section>')
    html = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>November 3, 2015 Interactive Agenda | Beaumont Intelligence</title><link rel="stylesheet" href="../styles.css"><style>
.agenda-record{background:white;border:1px solid var(--line);border-radius:12px;margin:12px 0}.agenda-record summary{padding:18px;cursor:pointer;color:var(--navy);font-weight:800}.agenda-documents{padding:0 18px 18px}.agenda-section{margin:30px 0}#agenda-search{width:100%;padding:14px;font:inherit}.viewer-dialog{width:min(1180px,95vw);height:90vh;border:0;border-radius:12px}.viewer-dialog iframe{width:100%;height:75vh;border:0}.viewer-dialog::backdrop{background:#001b3dcc}[hidden]{display:none!important}.status-actions{display:flex;flex-wrap:wrap;gap:12px}
</style></head><body><a class="skip-link" href="#main">Skip to content</a><header class="app-header"><div class="wrap header-row"><a class="brand" href="../index.html">Beaumont Intelligence</a><a href="../council-meeting-sources.html">Council meeting archive</a></div></header><main id="main" class="wrap section"><p class="eyebrow">November 3, 2015 · Historical record</p><h1>Interactive council agenda</h1><p>Explore the posted agenda and supporting official records. Agenda requests are not evidence of approval or payment.</p><div class="status-actions"><a class="btn" href="https://www.youtube.com/watch?v=mokmwjT4ujs&amp;t=73s" target="_blank" rel="noopener">Watch meeting ↗</a><a class="btn secondary" href="#wrcog">WRCOG agenda item</a><a class="btn secondary" href="../wrcog-restitution.html">WRCOG &amp; Restitution Center</a></div>
<section><h2>Source coverage</h2><p>All 26 entries listed in the City's November 3 archive folder are linked, plus the separately located Urban Futures record. This is not a complete attachment audit: supporting records for consent items 8.A and 8.J were not separately identified, the two Interwest versions have not been reconciled, and an unnamed scan remains unclassified. The seven-page agenda is available; a single combined packet has not been located.</p><p>YouTube identifies this video as November 3, 2015. The separately supplied September 15 transcript is not used here. November's transcript, item timestamps, motions, votes, and public report-out remain pending verification.</p><p><button class="btn" data-document="https://portal.laserfiche.com/Portal/DocView.aspx?id=199722&amp;repo=r-d75cb0c2">View official agenda</button> <a href="https://portal.laserfiche.com/Portal/Browse.aspx?id=135575&amp;repo=r-d75cb0c2" target="_blank" rel="noopener">Browse official archive ↗</a></p></section>
<label for="agenda-search">Search agenda items and supporting records</label><input id="agenda-search" type="search" placeholder="WRCOG, budget, quiet zones…"><p id="agenda-count" aria-live="polite"></p><div id="agenda-results">SECTIONS</div><noscript>All agenda items are displayed. Use the official-record links to view documents.</noscript></main><dialog class="viewer-dialog" id="viewer-dialog" aria-label="Official document viewer"><button id="viewer-close" class="btn">Close document</button><p>If the official viewer cannot load, use the item's Open official record link.</p><iframe title="Official source document" id="viewer-frame"></iframe></dialog><script src="historical-agenda.js"></script></body></html>'''.replace('SECTIONS', ''.join(sections))
    (DOCS / 'briefings/2015-11-03-sources.html').write_text(html, encoding='utf-8')
    print(f'Built November 3 agenda: {len(data["items"])} entries')

if __name__ == '__main__':
    main()
